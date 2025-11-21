import uvicorn
import os
import argparse
import logging
from dotenv import load_dotenv
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("representative_agent_launcher")

def main():
    parser = argparse.ArgumentParser(description="Run the Representative Agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--index-docs", action="store_true", help="Index documents from data/documents on startup")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not found in environment variables. Agent may fail to initialize.")

    # Pre-indexing logic (if requested)
    if args.index_docs:
        logger.info("Pre-indexing documents from data/documents...")
        # Note: In a real production scenario, we might want to do this differently,
        # but for this simple launcher, we'll rely on the API to handle indexing 
        # or we could initialize the RAG system here directly. 
        # However, since the API initializes its own RAG system on startup, 
        # we should probably let the API handle it or share the instance.
        # For simplicity, we will just print a message here and let the user know 
        # they can use the /index endpoint or we could add a startup hook in the API.
        
        # Actually, let's do it via a direct call to the core logic if we want to ensure it's ready
        # before the server starts, OR we can send a request to ourselves after start.
        # Let's keep it simple: Just warn that this flag is for future use or 
        # implemented via a separate script for now.
        
        # Better approach: We can use the python API directly here to index into the persistent DB
        # before starting the server.
        try:
            from ragc_core.hybrid_rag import HybridRAG
            from ragc_core.document_processor import DocumentProcessor
            from ragc_core.config import RAGConfig
            
            config = RAGConfig(gemini_api_key=os.getenv("GEMINI_API_KEY"))
            rag = HybridRAG(config)
            processor = DocumentProcessor()
            
            doc_dir = os.path.join(os.path.dirname(__file__), "data", "documents")
            files = []
            for ext in ["*.pdf", "*.docx", "*.txt", "*.md"]:
                files.extend(glob.glob(os.path.join(doc_dir, ext)))
                
            if files:
                logger.info(f"Found {len(files)} documents to index.")
                chunks = processor.process_multiple_documents(files)
                rag.add_documents(chunks)
                logger.info("Indexing complete.")
            else:
                logger.warning(f"No documents found in {doc_dir}")
                
        except Exception as e:
            logger.error(f"Failed to pre-index documents: {e}")

    logger.info(f"Starting Representative Agent on {args.host}:{args.port}")
    uvicorn.run("api.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
