"""
Graph RAG Module for Hybrid RAG System

This module implements graph-based retrieval using:
- FalkorDB for knowledge graph storage and retrieval
- Entity and relationship extraction
- Graph traversal for contextual retrieval
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from falkordb import FalkorDB
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .config import RAGConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphRAG:
    """
    Graph-based Retrieval Augmented Generation system
    
    Uses FalkorDB for knowledge graph construction and traversal
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize Graph RAG system
        
        Args:
            config: RAG configuration object
        """
        self.config = config or RAGConfig()
        self.config.validate()
        
        # Initialize Chat model
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=self.config.gemini_api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens
        )
        
        # Connect to FalkorDB
        try:
            self.db = FalkorDB(host=self.config.falkordb_host, port=self.config.falkordb_port)
            self.graph = self.db.select_graph("knowledge_graph")
            logger.info(f"Connected to FalkorDB at {self.config.falkordb_host}:{self.config.falkordb_port}")
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB: {str(e)}")
            # We don't raise here to allow instantiation even if DB is down, 
            # but methods will fail.
            self.graph = None
            
        if self.graph:
            self._create_indices()
    
    def _create_indices(self):
        """Create indices for optimization"""
        try:
            # Index on Entity name
            self.graph.query("CREATE INDEX FOR (e:Entity) ON (e.name)")
            # Index on Document id
            self.graph.query("CREATE INDEX FOR (d:Document) ON (d.id)")
        except Exception as e:
            # Indices might already exist
            logger.debug(f"Index creation note: {str(e)}")
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities from text using simple NER
        
        Args:
            text: Input text
            
        Returns:
            List[str]: Extracted entities
        """
        # Simple entity extraction: capitalized phrases
        # In production, use spaCy or a proper NER model
        entities = []
        
        # Find capitalized words and phrases
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(pattern, text)
        
        # Filter by minimum length and deduplicate
        entities = list(set([
            entity for entity in matches 
            if len(entity) >= self.config.graph_min_entity_length
        ]))
        
        # Limit number of entities
        entities = entities[:self.config.graph_max_entities]
        
        return entities
    
    def _extract_relationships(self, text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
        """
        Extract relationships between entities
        
        Args:
            text: Input text
            entities: List of entities
            
        Returns:
            List[Tuple[str, str, str]]: List of (entity1, relationship, entity2) tuples
        """
        relationships = []
        
        # Simple co-occurrence based relationship extraction
        # Entities appearing in the same sentence are considered related
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Find entities in this sentence
            sentence_entities = [e for e in entities if e in sentence]
            
            # Create relationships for co-occurring entities
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    # Use simple "related_to" relationship
                    relationships.append((entity1, "related_to", entity2))
        
        return relationships
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add documents to knowledge graph
        
        Args:
            chunks: List of document chunks with metadata
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return
            
        if not self.graph:
            logger.error("FalkorDB connection not established")
            return
        
        logger.info(f"Building knowledge graph from {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{i}_{chunk.get('chunk_id', i)}"
            text = chunk["text"]
            
            # Escape text for Cypher
            safe_text = text.replace("'", "\\'")
            
            # Create Document node
            # Using MERGE to avoid duplicates
            query = f"""
            MERGE (d:Document {{id: '{chunk_id}'}})
            SET d.text = '{safe_text}'
            """
            # Add metadata properties if needed, for now just text
            self.graph.query(query)
            
            # Extract entities
            entities = self._extract_entities(text)
            
            # Add entities and link to document
            for entity in entities:
                safe_entity = entity.replace("'", "\\'")
                query = f"""
                MERGE (e:Entity {{name: '{safe_entity}'}})
                WITH e
                MATCH (d:Document {{id: '{chunk_id}'}})
                MERGE (e)-[:MENTIONED_IN]->(d)
                """
                self.graph.query(query)
            
            # Extract and add relationships
            relationships = self._extract_relationships(text, entities)
            for entity1, rel_type, entity2 in relationships:
                if entity1 != entity2:
                    safe_e1 = entity1.replace("'", "\\'")
                    safe_e2 = entity2.replace("'", "\\'")
                    
                    query = f"""
                    MATCH (e1:Entity {{name: '{safe_e1}'}})
                    MATCH (e2:Entity {{name: '{safe_e2}'}})
                    MERGE (e1)-[:RELATED {{type: '{rel_type}'}}]->(e2)
                    """
                    self.graph.query(query)
        
        # Get stats
        stats = self.get_graph_stats()
        logger.info(f"Knowledge graph updated: {stats['num_nodes']} nodes, {stats['num_edges']} edges")
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using graph traversal
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Retrieved documents with scores
        """
        if top_k is None:
            top_k = self.config.top_k
            
        if not self.graph:
            logger.error("FalkorDB connection not established")
            return []
        
        logger.info(f"Retrieving top {top_k} documents for query: {query[:100]}...")
        
        # Extract entities from query
        query_entities = self._extract_entities(query)
        
        if not query_entities:
            logger.warning("No entities found in query")
            return []
            
        # Find relevant documents via graph traversal
        # Strategy:
        # 1. Find Entity nodes matching query entities
        # 2. Traverse to neighbors (related entities)
        # 3. Collect linked Documents
        # 4. Score documents based on number of connected relevant entities
        
        doc_scores = {}
        
        for entity in query_entities:
            safe_entity = entity.replace("'", "\\'")
            
            # Cypher query to find connected documents matching the entity or its neighbors
            # We look for documents mentioned by the entity directly, or by its neighbors (depth 1)
            cypher_query = f"""
            MATCH (e:Entity)
            WHERE e.name = '{safe_entity}' OR e.name CONTAINS '{safe_entity}'
            
            // Direct documents
            OPTIONAL MATCH (e)-[:MENTIONED_IN]->(d1:Document)
            
            // Neighbor documents
            OPTIONAL MATCH (e)-[:RELATED]-(neighbor:Entity)-[:MENTIONED_IN]->(d2:Document)
            
            RETURN d1.id as d1_id, d1.text as d1_text, 
                   d2.id as d2_id, d2.text as d2_text
            """
            
            result = self.graph.query(cypher_query)
            
            for record in result.result_set:
                # Process d1 (direct)
                if record[0]: # d1_id
                    doc_id = record[0]
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = {"score": 0, "text": record[1]}
                    doc_scores[doc_id]["score"] += 1.0 # Higher weight for direct match
                
                # Process d2 (neighbor)
                if record[2]: # d2_id
                    doc_id = record[2]
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = {"score": 0, "text": record[3]}
                    doc_scores[doc_id]["score"] += 0.5 # Lower weight for neighbor match
        
        # Format results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1]["score"], reverse=True)[:top_k]
        
        retrieved_docs = []
        for rank, (doc_id, data) in enumerate(sorted_docs):
            retrieved_docs.append({
                "text": data["text"],
                "score": data["score"],
                "metadata": {"id": doc_id},
                "id": doc_id,
                "rank": rank + 1,
                "retrieval_type": "graph"
            })
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs
    
    def generate(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate answer using retrieved documents
        
        Args:
            query: User query
            context_docs: Retrieved documents
            
        Returns:
            str: Generated answer
        """
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1} (Score: {doc['score']:.3f}):\n{doc['text']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # Create prompt
        prompt = f"""Based on the following context documents retrieved from a knowledge graph, please answer the question.
If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:"""
        
        # Generate response using Gemini
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            answer = response.content
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def query(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Dict[str, Any]: Answer and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, top_k)
        
        # Generate answer
        answer = self.generate(query, retrieved_docs)
        
        return {
            "answer": answer,
            "retrieved_documents": retrieved_docs,
            "num_documents": len(retrieved_docs),
            "query": query,
            "method": "graph_rag"
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics
        
        Returns:
            Dict[str, Any]: Graph statistics
        """
        if not self.graph:
            return {"status": "not_connected"}
            
        try:
            num_nodes = self.graph.query("MATCH (n) RETURN count(n)").result_set[0][0]
            num_edges = self.graph.query("MATCH ()-[r]->() RETURN count(r)").result_set[0][0]
            num_docs = self.graph.query("MATCH (d:Document) RETURN count(d)").result_set[0][0]
            
            return {
                "num_nodes": num_nodes,
                "num_edges": num_edges,
                "num_documents": num_docs,
                "backend": "falkordb"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    def clear_graph(self) -> None:
        """Clear knowledge graph"""
        if not self.graph:
            return
            
        try:
            self.graph.delete()
            # Re-select graph to create a fresh one (delete removes the key)
            self.graph = self.db.select_graph("knowledge_graph")
            self._create_indices()
            logger.info("Knowledge graph cleared")
        except Exception as e:
            logger.error(f"Error clearing graph: {str(e)}")
    
    def export_graph(self, output_path: str) -> None:
        """
        Export graph to file
        
        Args:
            output_path: Path to save graph
        """
        logger.warning("Graph export is not supported with FalkorDB backend. Data is persisted in the database.")
    
    def import_graph(self, input_path: str) -> None:
        """
        Import graph from file
        
        Args:
            input_path: Path to graph file
        """
        logger.warning("Graph import is not supported with FalkorDB backend. Please re-index documents.")

    def get_graph_data(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get graph data for visualization
        
        Args:
            limit: Maximum number of relationships to return
            
        Returns:
            Dict[str, Any]: Nodes and links for visualization
        """
        if not self.graph:
            return {"nodes": [], "links": []}
            
        try:
            # Query for nodes and relationships
            query = f"""
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT {limit}
            """
            result = self.graph.query(query)
            
            nodes = {}
            links = []
            
            for record in result.result_set:
                source_node = record[0]
                rel = record[1]
                target_node = record[2]
                
                # Process source node
                # FalkorDB Node object has labels, properties, id
                s_id = str(source_node.id)
                if s_id not in nodes:
                    # Determine label (Entity or Document)
                    label = "Unknown"
                    if "Entity" in source_node.labels:
                        label = "Entity"
                        name = source_node.properties.get("name", "Unknown")
                    elif "Document" in source_node.labels:
                        label = "Document"
                        name = f"Doc {source_node.properties.get('id', 'Unknown')}"
                    else:
                        name = f"Node {s_id}"
                        
                    nodes[s_id] = {
                        "id": s_id,
                        "label": label,
                        "name": name,
                        "properties": source_node.properties
                    }
                
                # Process target node
                t_id = str(target_node.id)
                if t_id not in nodes:
                    label = "Unknown"
                    if "Entity" in target_node.labels:
                        label = "Entity"
                        name = target_node.properties.get("name", "Unknown")
                    elif "Document" in target_node.labels:
                        label = "Document"
                        name = f"Doc {target_node.properties.get('id', 'Unknown')}"
                    else:
                        name = f"Node {t_id}"
                        
                    nodes[t_id] = {
                        "id": t_id,
                        "label": label,
                        "name": name,
                        "properties": target_node.properties
                    }
                
                # Process relationship
                links.append({
                    "source": s_id,
                    "target": t_id,
                    "type": rel.relation,
                    "properties": rel.properties
                })
                
            return {
                "nodes": list(nodes.values()),
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Error getting graph data: {str(e)}")
            return {"nodes": [], "links": [], "error": str(e)}
