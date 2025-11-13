"""
Graph RAG Component
Implements knowledge graph-based retrieval using NetworkX
Extracts entities and relationships using Gemini LLM
Provides graph traversal and reasoning capabilities
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import json
import pickle
import networkx as nx
from pyvis.network import Network
import google.generativeai as genai

from config.config import (
    GRAPH_CONFIG,
    GEMINI_CONFIG,
    HYBRID_RAG_CONFIG,
    BASE_DIR
)
from src.utils.logger import log
from src.utils.document_loader import DocumentChunk


class KnowledgeGraph:
    """
    Knowledge Graph implementation using NetworkX.
    
    Stores entities as nodes and relationships as edges.
    Supports:
    - Entity and relationship extraction using LLM
    - Graph traversal and multi-hop reasoning
    - Subgraph retrieval based on queries
    - Graph visualization
    """
    
    def __init__(self):
        """
        Initialize Knowledge Graph with NetworkX and Gemini API.
        
        Creates:
        - Directed multigraph for storing entities and relationships
        - Gemini client for entity extraction
        """
        log.info("Initializing Knowledge Graph component...")
        
        # Initialize directed multigraph (allows multiple edges between nodes)
        self.graph = nx.MultiDiGraph()
        
        # Configure Gemini API
        genai.configure(api_key=GEMINI_CONFIG["api_key"])
        self.llm = genai.GenerativeModel(
            model_name=GEMINI_CONFIG["model_name"],
            generation_config={
                "temperature": GEMINI_CONFIG["temperature"],
                "top_p": GEMINI_CONFIG["top_p"],
                "top_k": GEMINI_CONFIG["top_k"],
                "max_output_tokens": GEMINI_CONFIG["max_output_tokens"],
            }
        )
        
        log.info("Knowledge Graph initialized successfully")
        
        # Try to load existing graph if it exists
        self._load_graph()
    
    def build_from_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Build knowledge graph from document chunks using LLM-based extraction.
        
        Process:
        1. For each chunk, extract entities and relationships using Gemini
        2. Add entities as nodes with attributes
        3. Add relationships as edges with properties
        4. Persist graph to disk
        
        Args:
            chunks (List[DocumentChunk]): Document chunks to process
        """
        if not chunks:
            log.warning("No chunks provided to build_from_documents")
            return
        
        log.info(f"Building knowledge graph from {len(chunks)} document chunks...")
        
        for i, chunk in enumerate(chunks):
            try:
                # Extract entities and relationships from chunk
                entities, relationships = self._extract_knowledge(chunk)
                
                # Add entities to graph
                for entity in entities:
                    self._add_entity(entity, chunk.metadata)
                
                # Add relationships to graph
                for rel in relationships:
                    self._add_relationship(rel, chunk.metadata)
                
                if (i + 1) % 10 == 0:
                    log.info(f"Processed {i + 1}/{len(chunks)} chunks")
                    
            except Exception as e:
                log.error(f"Error processing chunk {i}: {str(e)}")
                continue
        
        log.info(
            f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )
        
        # Save graph to disk
        self._save_graph()
    
    def _extract_knowledge(
        self,
        chunk: DocumentChunk
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extract entities and relationships from text using Gemini LLM.
        
        Uses structured prompt to get JSON output with entities and relationships.
        
        Args:
            chunk (DocumentChunk): Document chunk to process
            
        Returns:
            Tuple containing:
            - List of entity dicts with 'name', 'type', 'description'
            - List of relationship dicts with 'source', 'target', 'relation'
        """
        # Construct extraction prompt
        prompt = f"""Extract entities and relationships from the following text. 
        
TEXT:
{chunk.text}

INSTRUCTIONS:
1. Identify key entities (people, organizations, concepts, technologies, processes)
2. Identify relationships between entities
3. Return as JSON with this exact structure:

{{
  "entities": [
    {{"name": "Entity Name", "type": "entity_type", "description": "brief description"}}
  ],
  "relationships": [
    {{"source": "Entity1", "target": "Entity2", "relation": "relationship_type"}}
  ]
}}

IMPORTANT: 
- Extract only factual, explicit information
- Entity names should be specific and consistent
- Relationship types should be descriptive (e.g., "implements", "uses", "requires")
- Return ONLY valid JSON, no additional text

JSON OUTPUT:"""

        try:
            # Call Gemini API
            response = self.llm.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            data = json.loads(response_text)
            
            entities = data.get("entities", [])
            relationships = data.get("relationships", [])
            
            # Limit number of entities per chunk
            max_entities = GRAPH_CONFIG["entity_extraction"]["max_entities_per_chunk"]
            if len(entities) > max_entities:
                entities = entities[:max_entities]
            
            return entities, relationships
            
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON response: {str(e)}")
            return [], []
        except Exception as e:
            log.error(f"Entity extraction failed: {str(e)}")
            return [], []
    
    def _add_entity(self, entity: Dict[str, Any], source_metadata: Dict[str, Any]) -> None:
        """
        Add an entity as a node in the knowledge graph.
        
        If entity already exists, updates its attributes.
        
        Args:
            entity (Dict): Entity dict with 'name', 'type', 'description'
            source_metadata (Dict): Metadata from source document
        """
        entity_name = entity.get("name", "").strip()
        if not entity_name:
            return
        
        # Normalize entity name (lowercase, remove extra spaces)
        entity_id = entity_name.lower().replace("  ", " ")
        
        # Get existing attributes or create new
        if self.graph.has_node(entity_id):
            node_attrs = self.graph.nodes[entity_id]
            # Append to sources list
            if 'sources' not in node_attrs:
                node_attrs['sources'] = []
            if source_metadata.get('source') not in node_attrs['sources']:
                node_attrs['sources'].append(source_metadata.get('source'))
        else:
            # Create new node
            node_attrs = {
                'name': entity_name,
                'type': entity.get('type', 'unknown'),
                'description': entity.get('description', ''),
                'sources': [source_metadata.get('source', 'unknown')]
            }
        
        # Add or update node
        self.graph.add_node(entity_id, **node_attrs)
    
    def _add_relationship(self, relationship: Dict[str, Any], source_metadata: Dict[str, Any]) -> None:
        """
        Add a relationship as an edge in the knowledge graph.
        
        Args:
            relationship (Dict): Relationship dict with 'source', 'target', 'relation'
            source_metadata (Dict): Metadata from source document
        """
        source = relationship.get("source", "").strip()
        target = relationship.get("target", "").strip()
        relation = relationship.get("relation", "related_to").strip()
        
        if not source or not target:
            return
        
        # Normalize entity names
        source_id = source.lower().replace("  ", " ")
        target_id = target.lower().replace("  ", " ")
        
        # Ensure both nodes exist
        if not self.graph.has_node(source_id):
            self._add_entity({"name": source}, source_metadata)
        if not self.graph.has_node(target_id):
            self._add_entity({"name": target}, source_metadata)
        
        # Add edge with attributes
        self.graph.add_edge(
            source_id,
            target_id,
            relation=relation,
            source_doc=source_metadata.get('source', 'unknown')
        )
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        max_depth: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant subgraph for a query.
        
        Process:
        1. Extract key entities from query using LLM
        2. Find matching nodes in graph
        3. Traverse graph from matched nodes (multi-hop reasoning)
        4. Return context from subgraph
        
        Args:
            query (str): Search query
            top_k (int, optional): Number of results to return
            max_depth (int, optional): Maximum traversal depth from seed nodes
            
        Returns:
            List[Dict[str, Any]]: Retrieved graph contexts with relevance scores
        """
        if top_k is None:
            top_k = HYBRID_RAG_CONFIG["graph_top_k"]
        if max_depth is None:
            max_depth = GRAPH_CONFIG["reasoning"]["max_depth"]
        
        log.info(f"Retrieving from knowledge graph for query: '{query[:100]}...'")
        
        # Extract key entities from query
        query_entities = self._extract_query_entities(query)
        
        if not query_entities:
            log.warning("No entities extracted from query")
            return []
        
        # Find matching nodes in graph
        seed_nodes = self._find_matching_nodes(query_entities)
        
        if not seed_nodes:
            log.warning("No matching nodes found in graph")
            return []
        
        # Retrieve subgraph context for each seed node
        results = []
        for seed_node in seed_nodes[:top_k]:
            context = self._get_node_context(seed_node, max_depth)
            results.append({
                'text': context['text'],
                'score': context['score'],
                'metadata': context['metadata'],
                'retrieval_method': 'graph'
            })
        
        log.info(f"Retrieved {len(results)} graph contexts")
        return results
    
    def _extract_query_entities(self, query: str) -> List[str]:
        """
        Extract key entities/concepts from query using LLM.
        
        Args:
            query (str): User query
            
        Returns:
            List[str]: List of entity names
        """
        prompt = f"""Extract key entities, concepts, and keywords from this query.
        
QUERY: {query}

Return ONLY a JSON list of strings, like: ["entity1", "entity2", "concept1"]
No additional text or explanation.

JSON LIST:"""

        try:
            response = self.llm.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            entities = json.loads(response_text)
            return entities if isinstance(entities, list) else []
            
        except Exception as e:
            log.error(f"Failed to extract query entities: {str(e)}")
            return query.lower().split()  # Fallback to simple word split
    
    def _find_matching_nodes(self, query_entities: List[str]) -> List[str]:
        """
        Find graph nodes that match query entities.
        
        Uses fuzzy matching on node names.
        
        Args:
            query_entities (List[str]): List of entity names from query
            
        Returns:
            List[str]: List of matching node IDs
        """
        matching_nodes = []
        
        for entity in query_entities:
            entity_lower = entity.lower()
            
            # Exact match
            if entity_lower in self.graph.nodes():
                matching_nodes.append(entity_lower)
                continue
            
            # Partial match
            for node_id in self.graph.nodes():
                if entity_lower in node_id or node_id in entity_lower:
                    if node_id not in matching_nodes:
                        matching_nodes.append(node_id)
        
        return matching_nodes
    
    def _get_node_context(self, node_id: str, max_depth: int) -> Dict[str, Any]:
        """
        Get rich context for a node by traversing its neighborhood.
        
        Includes:
        - Node attributes
        - Connected entities (neighbors)
        - Relationships (edges)
        - Multi-hop traversal up to max_depth
        
        Args:
            node_id (str): ID of seed node
            max_depth (int): Maximum traversal depth
            
        Returns:
            Dict with 'text', 'score', 'metadata'
        """
        # Get node attributes
        node_data = self.graph.nodes[node_id]
        
        # Build context text
        context_parts = [
            f"Entity: {node_data.get('name', node_id)}",
            f"Type: {node_data.get('type', 'unknown')}",
        ]
        
        if node_data.get('description'):
            context_parts.append(f"Description: {node_data['description']}")
        
        # Get neighbors and relationships
        max_neighbors = GRAPH_CONFIG["reasoning"]["max_neighbors"]
        
        # Outgoing edges
        out_edges = list(self.graph.out_edges(node_id, data=True))[:max_neighbors]
        if out_edges:
            context_parts.append("\nRelationships:")
            for source, target, data in out_edges:
                relation = data.get('relation', 'related_to')
                target_name = self.graph.nodes[target].get('name', target)
                context_parts.append(f"  - {relation} -> {target_name}")
        
        # Incoming edges (who references this entity)
        in_edges = list(self.graph.in_edges(node_id, data=True))[:max_neighbors]
        if in_edges:
            context_parts.append("\nReferenced by:")
            for source, target, data in in_edges:
                source_name = self.graph.nodes[source].get('name', source)
                relation = data.get('relation', 'related_to')
                context_parts.append(f"  - {source_name} ({relation})")
        
        # Combine context
        context_text = "\n".join(context_parts)
        
        # Calculate relevance score (based on node centrality)
        try:
            # Degree centrality as relevance proxy
            score = nx.degree_centrality(self.graph).get(node_id, 0.5)
        except:
            score = 0.5
        
        return {
            'text': context_text,
            'score': score,
            'metadata': {
                'node_id': node_id,
                'type': node_data.get('type'),
                'sources': node_data.get('sources', [])
            }
        }
    
    def visualize(self, output_path: Optional[str] = None) -> str:
        """
        Create an interactive HTML visualization of the knowledge graph.
        
        Args:
            output_path (str, optional): Path to save HTML file
            
        Returns:
            str: Path to generated HTML file
        """
        if output_path is None:
            output_path = GRAPH_CONFIG["visualization_path"]
        
        log.info("Generating graph visualization...")
        
        # Create pyvis network
        net = Network(
            height="750px",
            width="100%",
            bgcolor="#222222",
            font_color="white",
            directed=True
        )
        
        # Add nodes with colors based on type
        type_colors = {
            'person': '#FF6B6B',
            'organization': '#4ECDC4',
            'concept': '#95E1D3',
            'technology': '#F38181',
            'process': '#AA96DA',
            'unknown': '#FCBAD3'
        }
        
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            entity_type = node_data.get('type', 'unknown')
            color = type_colors.get(entity_type, type_colors['unknown'])
            
            net.add_node(
                node_id,
                label=node_data.get('name', node_id)[:30],
                title=node_data.get('description', '')[:200],
                color=color,
                size=20
            )
        
        # Add edges
        for source, target, data in self.graph.edges(data=True):
            relation = data.get('relation', '')
            net.add_edge(source, target, title=relation, label=relation[:20])
        
        # Save
        net.save_graph(output_path)
        log.info(f"Graph visualization saved to: {output_path}")
        
        return output_path
    
    def _save_graph(self) -> None:
        """Save graph to disk using pickle."""
        persist_path = Path(GRAPH_CONFIG["persist_path"])
        persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(persist_path, 'wb') as f:
            pickle.dump(self.graph, f)
        
        log.info(f"Knowledge graph saved to: {persist_path}")
    
    def _load_graph(self) -> None:
        """Load graph from disk if it exists."""
        persist_path = Path(GRAPH_CONFIG["persist_path"])
        
        if persist_path.exists():
            try:
                with open(persist_path, 'rb') as f:
                    self.graph = pickle.load(f)
                log.info(
                    f"Loaded existing knowledge graph: {self.graph.number_of_nodes()} nodes, "
                    f"{self.graph.number_of_edges()} edges"
                )
            except Exception as e:
                log.error(f"Failed to load graph: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dict with graph statistics
        """
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "avg_degree": sum(dict(self.graph.degree()).values()) / max(self.graph.number_of_nodes(), 1),
            "is_directed": self.graph.is_directed(),
        }
    
    def __repr__(self):
        return f"KnowledgeGraph(nodes={self.graph.number_of_nodes()}, edges={self.graph.number_of_edges()})"
