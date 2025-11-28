import os
import logging
import numpy as np
from typing import List, Optional, Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

async def gemini_complete(
    prompt: str,
    system_prompt: str = None,
    history_messages: List[Dict[str, str]] = [],
    **kwargs
) -> str:
    """
    Adapter function for Gemini LLM to be used with LightRAG.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        history_messages: Optional history messages
        **kwargs: Additional arguments
        
    Returns:
        Generated text response
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
        
    model_name = kwargs.get("model_name", "gemini-2.0-flash-exp")
    temperature = kwargs.get("temperature", 0.7)
    max_tokens = kwargs.get("max_tokens", 2048)
    
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_tokens
    )
    
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
        
    for msg in history_messages:
        role = msg.get("role")
        content = msg.get("content")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            # LangChain's AIMessage or similar could be used, but for simplicity in this context
            # we might just append previous turns if needed. 
            # LightRAG typically passes history for context.
            pass
            
    messages.append(HumanMessage(content=prompt))
    
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"Error in gemini_complete: {e}")
        raise

async def gemini_embed(texts: List[str]) -> np.ndarray:
    """
    Adapter function for Gemini Embeddings to be used with LightRAG.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        Numpy array of embeddings
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
        
    model_name = "models/text-embedding-004"
    
    embeddings = GoogleGenerativeAIEmbeddings(
        model=model_name,
        google_api_key=api_key
    )
    
    try:
        # GoogleGenerativeAIEmbeddings supports embed_documents
        # Note: LangChain's embed_documents is synchronous by default in some versions,
        # but we need to check if aembed_documents is available or wrap it.
        # For safety with LightRAG's async expectation, we'll use aembed_documents if available,
        # or run in executor.
        
        # Checking if aembed_documents exists
        if hasattr(embeddings, "aembed_documents"):
            results = await embeddings.aembed_documents(texts)
        else:
            # Fallback to sync run in executor if async not strictly supported
            import asyncio
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(None, embeddings.embed_documents, texts)
            
        return np.array(results)
    except Exception as e:
        logger.error(f"Error in gemini_embed: {e}")
        raise
