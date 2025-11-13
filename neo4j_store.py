"""
Neo4j Integration for Hybrid RAG System
Provides scalable graph storage and advanced query capabilities using Neo4j

Features:
- Neo4j database connection and management
- Efficient entity and relationship storage
- Cypher query execution
- Vector index support for semantic search
- Batch operations for large-scale ingestion
"""

from typing import List, Dict, Any, Optional, Tuple
import os
from dataclasses import dataclass
import time

# Neo4j imports
try:
    from neo4j import GraphDatabase, basic_auth
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Run: pip install neo4j")

from loguru import logger
import numpy as np


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Entity:
    """Represents an entity node in the knowledge graph"""
    id: str
    name: str
    type: str
    attributes: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


@dataclass
class Relationship:
    """Represents a relationship edge in the knowledge graph"""
    source_id: str
    target_id: str
    relation_type: str
    attributes: Dict[str, Any]


# ============================================================================
# NEO4J GRAPH STORAGE
# ============================================================================

class Neo4jGraphStore:
    """
    Neo4j-based knowledge graph storage for production-scale RAG
    
    Advantages over NetworkX:
    - Persistent storage (survives restarts)
    - Scalable to millions of nodes
    - Native graph query language (Cypher)
    - Built-in indexing and optimization
    - Distributed deployment support
    
    Usage:
        store = Neo4jGraphStore(uri="bolt://localhost:7687")
        store.connect(username="neo4j", password="password")
        store.create_entity(Entity(...))
        results = store.cypher_query("MATCH (n:Entity) RETURN n LIMIT 10")
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        database: str = "neo4j"
    ):
        """
        Initialize Neo4j graph store
        
        Args:
            uri (str): Neo4j connection URI
            database (str): Database name (default: neo4j)
        """
        if not NEO4J_AVAILABLE:
            raise ImportError(
                "neo4j package required. Install with: pip install neo4j"
            )
        
        self.uri = uri
        self.database = database
        self.driver = None
        self._connected = False
        
        logger.info(f"Initialized Neo4j store with URI: {uri}")
    
    def connect(
        self,
        username: str = "neo4j",
        password: str = None
    ) -> bool:
        """
        Connect to Neo4j database
        
        Args:
            username (str): Neo4j username
            password (str): Neo4j password (or set NEO4J_PASSWORD env var)
            
        Returns:
            bool: True if connection successful
        """
        # Get password from environment if not provided
        if password is None:
            password = os.getenv("NEO4J_PASSWORD", "")
        
        if not password:
            logger.error("Neo4j password required. Set NEO4J_PASSWORD env var.")
            return False
        
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=basic_auth(username, password)
            )
            
            # Verify connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                assert test_value == 1
            
            self._connected = True
            logger.info("Successfully connected to Neo4j database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._connected = False
            return False
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            self._connected = False
            logger.info("Neo4j connection closed")
    
    def _check_connection(self):
        """Verify database is connected"""
        if not self._connected or not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
    
    # ========================================================================
    # ENTITY OPERATIONS
    # ========================================================================
    
    def create_entity(self, entity: Entity) -> bool:
        """
        Create entity node in graph
        
        Args:
            entity (Entity): Entity to create
            
        Returns:
            bool: True if successful
        """
        self._check_connection()
        
        try:
            with self.driver.session(database=self.database) as session:
                # Convert embedding to list if present
                props = entity.attributes.copy()
                props.update({
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type
                })
                
                if entity.embedding is not None:
                    props["embedding"] = entity.embedding.tolist()
                
                # Create node with dynamic label based on entity type
                query = f"""
                    CREATE (e:{entity.type})
                    SET e += $props
                    RETURN e.id as id
                """
                
                result = session.run(query, props=props)
                created_id = result.single()["id"]
                
                logger.debug(f"Created entity: {created_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            return False
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve entity by ID
        
        Args:
            entity_id (str): Entity ID
            
        Returns:
            Dict: Entity properties or None if not found
        """
        self._check_connection()
        
        try:
            with self.driver.session(database=self.database) as session:
                query = """
                    MATCH (e {id: $entity_id})
                    RETURN properties(e) as props
                """
                
                result = session.run(query, entity_id=entity_id)
                record = result.single()
                
                if record:
                    return dict(record["props"])
                return None
                
        except Exception as e:
            logger.error(f"Failed to get entity: {e}")
            return None
    
    def batch_create_entities(
        self,
        entities: List[Entity],
        batch_size: int = 1000
    ) -> int:
        """
        Efficiently create multiple entities using batching
        
        Args:
            entities (List[Entity]): Entities to create
            batch_size (int): Number of entities per batch
            
        Returns:
            int: Number of entities created
        """
        self._check_connection()
        
        created_count = 0
        
        # Process in batches for efficiency
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            # Prepare batch data
            batch_data = []
            for entity in batch:
                props = entity.attributes.copy()
                props.update({
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type
                })
                
                if entity.embedding is not None:
                    props["embedding"] = entity.embedding.tolist()
                
                batch_data.append({
                    "entity_type": entity.type,
                    "props": props
                })
            
            try:
                with self.driver.session(database=self.database) as session:
                    # Use UNWIND for batch creation
                    query = """
                        UNWIND $batch as item
                        CALL apoc.create.node([item.entity_type], item.props)
                        YIELD node
                        RETURN count(node) as count
                    """
                    
                    result = session.run(query, batch=batch_data)
                    batch_count = result.single()["count"]
                    created_count += batch_count
                    
                    logger.info(f"Created batch {i//batch_size + 1}: {batch_count} entities")
                    
            except Exception as e:
                logger.error(f"Failed to create batch: {e}")
        
        logger.info(f"Total entities created: {created_count}")
        return created_count
    
    # ========================================================================
    # RELATIONSHIP OPERATIONS
    # ========================================================================
    
    def create_relationship(self, relationship: Relationship) -> bool:
        """
        Create relationship between entities
        
        Args:
            relationship (Relationship): Relationship to create
            
        Returns:
            bool: True if successful
        """
        self._check_connection()
        
        try:
            with self.driver.session(database=self.database) as session:
                # Create relationship with dynamic type
                query = f"""
                    MATCH (source {{id: $source_id}})
                    MATCH (target {{id: $target_id}})
                    CREATE (source)-[r:{relationship.relation_type}]->(target)
                    SET r += $attributes
                    RETURN id(r) as rel_id
                """
                
                result = session.run(
                    query,
                    source_id=relationship.source_id,
                    target_id=relationship.target_id,
                    attributes=relationship.attributes
                )
                
                rel_id = result.single()["rel_id"]
                logger.debug(f"Created relationship: {rel_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
    
    def batch_create_relationships(
        self,
        relationships: List[Relationship],
        batch_size: int = 1000
    ) -> int:
        """
        Efficiently create multiple relationships
        
        Args:
            relationships (List[Relationship]): Relationships to create
            batch_size (int): Number of relationships per batch
            
        Returns:
            int: Number of relationships created
        """
        self._check_connection()
        
        created_count = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            
            # Group by relation type for efficiency
            by_type = {}
            for rel in batch:
                if rel.relation_type not in by_type:
                    by_type[rel.relation_type] = []
                by_type[rel.relation_type].append(rel)
            
            # Create each type in batch
            for rel_type, rels in by_type.items():
                batch_data = [
                    {
                        "source_id": r.source_id,
                        "target_id": r.target_id,
                        "attributes": r.attributes
                    }
                    for r in rels
                ]
                
                try:
                    with self.driver.session(database=self.database) as session:
                        query = f"""
                            UNWIND $batch as item
                            MATCH (source {{id: item.source_id}})
                            MATCH (target {{id: item.target_id}})
                            CREATE (source)-[r:{rel_type}]->(target)
                            SET r += item.attributes
                            RETURN count(r) as count
                        """
                        
                        result = session.run(query, batch=batch_data)
                        batch_count = result.single()["count"]
                        created_count += batch_count
                        
                except Exception as e:
                    logger.error(f"Failed to create relationship batch: {e}")
        
        logger.info(f"Total relationships created: {created_count}")
        return created_count
    
    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================
    
    def cypher_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results
        
        Args:
            query (str): Cypher query string
            parameters (Dict): Query parameters
            
        Returns:
            List[Dict]: Query results
        """
        self._check_connection()
        
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
                
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return []
    
    def find_neighbors(
        self,
        entity_id: str,
        max_depth: int = 2,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find neighboring entities within specified depth
        
        Args:
            entity_id (str): Starting entity ID
            max_depth (int): Maximum traversal depth
            limit (int): Maximum number of neighbors
            
        Returns:
            List[Dict]: Neighboring entities with paths
        """
        self._check_connection()
        
        query = """
            MATCH path = (start {id: $entity_id})-[*1..$max_depth]-(neighbor)
            RETURN DISTINCT neighbor.id as id,
                   neighbor.name as name,
                   neighbor.type as type,
                   length(path) as distance
            ORDER BY distance ASC
            LIMIT $limit
        """
        
        return self.cypher_query(
            query,
            {
                "entity_id": entity_id,
                "max_depth": max_depth,
                "limit": limit
            }
        )
    
    def vector_similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        index_name: str = "entity_embeddings"
    ) -> List[Dict[str, Any]]:
        """
        Search for similar entities using vector similarity
        Requires vector index to be created first
        
        Args:
            query_embedding (np.ndarray): Query embedding vector
            top_k (int): Number of results to return
            index_name (str): Name of vector index
            
        Returns:
            List[Dict]: Similar entities with similarity scores
        """
        self._check_connection()
        
        # Note: Requires Neo4j 5.11+ with vector index support
        query = """
            CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
            YIELD node, score
            RETURN node.id as id,
                   node.name as name,
                   node.type as type,
                   score
        """
        
        try:
            return self.cypher_query(
                query,
                {
                    "index_name": index_name,
                    "top_k": top_k,
                    "embedding": query_embedding.tolist()
                }
            )
        except Exception as e:
            logger.warning(f"Vector search failed (requires Neo4j 5.11+): {e}")
            return []
    
    # ========================================================================
    # INDEX MANAGEMENT
    # ========================================================================
    
    def create_indexes(self):
        """Create recommended indexes for performance"""
        self._check_connection()
        
        indexes = [
            # Entity ID index
            "CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.id)",
            
            # Entity name index for text search
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            
            # Entity type index for filtering
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"Created index: {index_query.split()[2]}")
                except Exception as e:
                    logger.warning(f"Index creation skipped: {e}")
    
    def create_vector_index(
        self,
        index_name: str = "entity_embeddings",
        dimension: int = 384
    ):
        """
        Create vector index for semantic search
        Requires Neo4j 5.11+ with vector index support
        
        Args:
            index_name (str): Name for the vector index
            dimension (int): Embedding dimension
        """
        self._check_connection()
        
        query = f"""
            CREATE VECTOR INDEX {index_name} IF NOT EXISTS
            FOR (e:Entity)
            ON e.embedding
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimension},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run(query)
                logger.info(f"Created vector index: {index_name}")
        except Exception as e:
            logger.warning(f"Vector index creation failed (requires Neo4j 5.11+): {e}")
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get graph statistics
        
        Returns:
            Dict: Statistics including node/relationship counts
        """
        self._check_connection()
        
        stats = {}
        
        # Node count
        result = self.cypher_query("MATCH (n) RETURN count(n) as count")
        stats["node_count"] = result[0]["count"] if result else 0
        
        # Relationship count
        result = self.cypher_query("MATCH ()-[r]->() RETURN count(r) as count")
        stats["relationship_count"] = result[0]["count"] if result else 0
        
        # Node types distribution
        result = self.cypher_query("""
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
        """)
        stats["node_types"] = {r["type"]: r["count"] for r in result}
        
        # Relationship types distribution
        result = self.cypher_query("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        stats["relationship_types"] = {r["type"]: r["count"] for r in result}
        
        return stats
    
    def clear_graph(self):
        """Delete all nodes and relationships (use with caution!)"""
        self._check_connection()
        
        logger.warning("Clearing entire graph...")
        
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        logger.info("Graph cleared")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example: Using Neo4j graph store"""
    
    # Initialize and connect
    store = Neo4jGraphStore(uri="bolt://localhost:7687")
    
    if not store.connect(username="neo4j", password="password"):
        print("Failed to connect. Make sure Neo4j is running.")
        return
    
    # Create indexes
    store.create_indexes()
    
    # Create entities
    entity1 = Entity(
        id="e1",
        name="Agent Card",
        type="Concept",
        attributes={"description": "A2A protocol component"}
    )
    
    entity2 = Entity(
        id="e2",
        name="Task Lifecycle",
        type="Process",
        attributes={"description": "States: SUBMITTED, WORKING, COMPLETED"}
    )
    
    store.create_entity(entity1)
    store.create_entity(entity2)
    
    # Create relationship
    rel = Relationship(
        source_id="e1",
        target_id="e2",
        relation_type="USES",
        attributes={"confidence": 0.95}
    )
    
    store.create_relationship(rel)
    
    # Query neighbors
    neighbors = store.find_neighbors("e1", max_depth=2, limit=10)
    print(f"Found {len(neighbors)} neighbors")
    
    # Get statistics
    stats = store.get_statistics()
    print(f"Graph stats: {stats}")
    
    # Close connection
    store.close()


if __name__ == "__main__":
    example_usage()
