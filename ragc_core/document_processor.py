"""
Document Processing Module for Hybrid RAG System

This module handles:
- Loading documents from various formats (PDF, DOCX, TXT, MD, HTML)
- Chunking documents with configurable size and overlap
- Text preprocessing and cleaning
"""

import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Document processor for handling various document formats
    
    Supports: PDF, DOCX, TXT, MD, HTML
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def load_document(self, file_path: str) -> str:
        """
        Load document from file
        
        Args:
            file_path: Path to document file
            
        Returns:
            str: Document text content
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        logger.info(f"Loading document: {file_path} (format: {file_ext})")
        
        # Route to appropriate loader based on file extension
        if file_ext == '.pdf':
            return self._load_pdf(file_path)
        elif file_ext == '.docx':
            return self._load_docx(file_path)
        elif file_ext in ['.txt', '.md']:
            return self._load_text(file_path)
        elif file_ext in ['.html', '.htm']:
            return self._load_html(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _load_pdf(self, file_path: str) -> str:
        """
        Load PDF document
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            str: Extracted text
        """
        try:
            import pypdf
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text += page.extract_text()
                    logger.debug(f"Extracted text from page {page_num + 1}")
            
            logger.info(f"Successfully loaded PDF: {len(text)} characters")
            return text
            
        except ImportError:
            logger.error("pypdf not installed. Install with: pip install pypdf")
            raise
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            raise
    
    def _load_docx(self, file_path: str) -> str:
        """
        Load DOCX document
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            str: Extracted text
        """
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            logger.info(f"Successfully loaded DOCX: {len(text)} characters")
            return text
            
        except ImportError:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            raise
        except Exception as e:
            logger.error(f"Error loading DOCX: {str(e)}")
            raise
    
    def _load_text(self, file_path: str) -> str:
        """
        Load plain text or markdown document
        
        Args:
            file_path: Path to text file
            
        Returns:
            str: File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            logger.info(f"Successfully loaded text file: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error loading text file: {str(e)}")
            raise
    
    def _load_html(self, file_path: str) -> str:
        """
        Load HTML document
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            str: Extracted text (HTML tags removed)
        """
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            
            logger.info(f"Successfully loaded HTML: {len(text)} characters")
            return text
            
        except ImportError:
            logger.error("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
            raise
        except Exception as e:
            logger.error(f"Error loading HTML: {str(e)}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text
        
        Args:
            text: Raw text
            
        Returns:
            str: Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List[Dict[str, Any]]: List of chunks with metadata
        """
        # Clean text first
        text = self.clean_text(text)
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings in the overlap region
                for delimiter in ['. ', '! ', '? ', '\n']:
                    last_delimiter = text[start:end].rfind(delimiter)
                    if last_delimiter != -1:
                        end = start + last_delimiter + len(delimiter)
                        break
            
            # Extract chunk
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunk_data = {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "chunk_size": len(chunk_text)
                }
                
                # Add user-provided metadata
                if metadata:
                    chunk_data.update(metadata)
                
                chunks.append(chunk_data)
                chunk_id += 1
            
            # Move start position (with overlap)
            start = end - self.chunk_overlap
            
            # Ensure we don't get stuck in infinite loop
            if start <= chunks[-1]["start_char"] if chunks else True:
                start = end
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def process_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Complete document processing pipeline
        
        Args:
            file_path: Path to document
            metadata: Optional metadata for the document
            
        Returns:
            List[Dict[str, Any]]: Processed chunks with metadata
        """
        # Load document
        text = self.load_document(file_path)
        
        # Add file metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "source": file_path,
            "filename": Path(file_path).name,
            "file_type": Path(file_path).suffix
        })
        
        # Chunk document
        chunks = self.chunk_text(text, metadata)
        
        logger.info(f"Document processing complete: {file_path}")
        return chunks
    
    def process_multiple_documents(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple documents
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List[Dict[str, Any]]: All chunks from all documents
        """
        all_chunks = []
        
        for file_path in file_paths:
            try:
                chunks = self.process_document(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(file_paths)} documents, created {len(all_chunks)} total chunks")
        return all_chunks


# Utility functions
def get_supported_formats() -> List[str]:
    """
    Get list of supported file formats
    
    Returns:
        List[str]: Supported file extensions
    """
    return ['.pdf', '.docx', '.txt', '.md', '.html', '.htm']


def is_supported_format(file_path: str) -> bool:
    """
    Check if file format is supported
    
    Args:
        file_path: Path to file
        
    Returns:
        bool: True if format is supported
    """
    return Path(file_path).suffix.lower() in get_supported_formats()
