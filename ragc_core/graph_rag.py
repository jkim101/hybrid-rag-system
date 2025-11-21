"""
Graph RAG Module for Hybrid RAG System

This module implements graph-based retrieval using:
- NetworkX for knowledge graph construction
- Entity and relationship extraction
- Graph traversal for contextual retrieval
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
import networkx as nx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .config import RAGConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphRAG:
    """
    Graph-based Retrieval Augmented Generation system
    
    Uses NetworkX for knowledge graph construction and traversal
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
        
        # Initialize knowledge graph
        self.graph = nx.DiGraph()
        
        # Document storage (chunk_id -> chunk data)
        self.documents = {}
        
        logger.info("GraphRAG initialized with empty knowledge graph")
    
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
                    # In production, use more sophisticated relationship extraction
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
        
        logger.info(f"Building knowledge graph from {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{i}_{chunk.get('chunk_id', i)}"
            text = chunk["text"]
            
            # Store document
            self.documents[chunk_id] = chunk
            
            # Extract entities
            entities = self._extract_entities(text)
            
            # Add entities as nodes
            for entity in entities:
                if not self.graph.has_node(entity):
                    self.graph.add_node(entity, type="entity", documents=[])
                
                # Link entity to document
                if chunk_id not in self.graph.nodes[entity]["documents"]:
                    self.graph.nodes[entity]["documents"].append(chunk_id)
            
            # Extract and add relationships
            relationships = self._extract_relationships(text, entities)
            for entity1, rel_type, entity2 in relationships:
                if entity1 != entity2:  # Avoid self-loops
                    self.graph.add_edge(
                        entity1, 
                        entity2, 
                        relationship=rel_type,
                        weight=1.0
                    )
        
        logger.info(f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, "
                   f"{self.graph.number_of_edges()} edges")
    
    def _find_relevant_entities(self, query: str) -> List[str]:
        """
        Find entities in the graph relevant to the query
        
        Args:
            query: Query text
            
        Returns:
            List[str]: Relevant entity names
        """
        query_entities = self._extract_entities(query)
        relevant_entities = []
        
        # Find exact matches
        for entity in query_entities:
            if entity in self.graph.nodes:
                relevant_entities.append(entity)
        
        # Find partial matches
        query_lower = query.lower()
        for node in self.graph.nodes:
            if node.lower() in query_lower or query_lower in node.lower():
                if node not in relevant_entities:
                    relevant_entities.append(node)
        
        return relevant_entities
    
    def _get_subgraph(self, entities: List[str], depth: int = 1) -> nx.DiGraph:
        """
        Get subgraph around entities
        
        Args:
            entities: Starting entities
            depth: Depth of graph traversal
            
        Returns:
            nx.DiGraph: Subgraph
        """
        nodes_to_include = set(entities)
        
        # BFS to find neighboring nodes
        for entity in entities:
            if entity in self.graph:
                # Get neighbors at specified depth
                for _ in range(depth):
                    neighbors = set()
                    for node in nodes_to_include:
                        if node in self.graph:
                            neighbors.update(self.graph.neighbors(node))
                            neighbors.update(self.graph.predecessors(node))
                    nodes_to_include.update(neighbors)
        
        # Create subgraph
        subgraph = self.graph.subgraph(nodes_to_include).copy()
        return subgraph
    
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
        
        logger.info(f"Retrieving top {top_k} documents for query: {query[:100]}...")
        
        # Find relevant entities
        relevant_entities = self._find_relevant_entities(query)
        
        if not relevant_entities:
            logger.warning("No relevant entities found in graph")
            return []
        
        logger.info(f"Found {len(relevant_entities)} relevant entities: {relevant_entities[:5]}")
        
        # Get subgraph around relevant entities
        subgraph = self._get_subgraph(relevant_entities, depth=2)
        
        # Collect documents from relevant entities
        doc_scores = {}
        for node in subgraph.nodes:
            if "documents" in self.graph.nodes[node]:
                for doc_id in self.graph.nodes[node]["documents"]:
                    # Score based on entity relevance and graph centrality
                    score = 1.0 if node in relevant_entities else 0.5
                    
                    # Boost score for nodes with higher degree (more connections)
                    degree = self.graph.degree(node)
                    score *= (1 + 0.1 * min(degree, 10))
                    
                    if doc_id in doc_scores:
                        doc_scores[doc_id] = max(doc_scores[doc_id], score)
                    else:
                        doc_scores[doc_id] = score
        
        # Sort by score and return top_k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        retrieved_docs = []
        for rank, (doc_id, score) in enumerate(sorted_docs):
            if doc_id in self.documents:
                retrieved_docs.append({
                    "text": self.documents[doc_id]["text"],
                    "score": score,
                    "metadata": {k: v for k, v in self.documents[doc_id].items() if k != "text"},
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
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "num_documents": len(self.documents),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }
    
    def clear_graph(self) -> None:
        """Clear knowledge graph"""
        self.graph.clear()
        self.documents.clear()
        logger.info("Knowledge graph cleared")
    
    def export_graph(self, output_path: str) -> None:
        """
        Export graph to file
        
        Args:
            output_path: Path to save graph
        """
        import pickle
        
        with open(output_path, 'wb') as f:
            pickle.dump({
                'graph': self.graph,
                'documents': self.documents
            }, f)
        
        logger.info(f"Graph exported to {output_path}")
    
    def import_graph(self, input_path: str) -> None:
        """
        Import graph from file
        
        Args:
            input_path: Path to graph file
        """
        import pickle
        
        with open(input_path, 'rb') as f:
            data = pickle.load(f)
            self.graph = data['graph']
            self.documents = data['documents']
        
        logger.info(f"Graph imported from {input_path}")
