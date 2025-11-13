"""
Document Loader Utility
Handles loading and chunking of various document formats (PDF, DOCX, TXT, MD, HTML)
"""

from pathlib import Path
from typing import List, Dict, Any
import re

# Document processing imports
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup

from config import DOCUMENT_CONFIG, DATA_DIR
from logger import log


class DocumentChunk:
    """
    Represents a chunk of document text with metadata.
    
    Attributes:
        text (str): The actual text content
        metadata (dict): Associated metadata (source, page, chunk_id, etc.)
    """
    
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata
    
    def __repr__(self):
        return f"DocumentChunk(text_length={len(self.text)}, metadata={self.metadata})"


class DocumentLoader:
    """
    Loads documents from various formats and splits them into manageable chunks.
    
    Supports:
    - Plain text (.txt, .md)
    - PDF (.pdf)
    - Word documents (.docx)
    - HTML (.html, .htm)
    """
    
    def __init__(self):
        """Initialize the document loader with configuration settings."""
        self.chunk_size = DOCUMENT_CONFIG["chunk_size"]
        self.chunk_overlap = DOCUMENT_CONFIG["chunk_overlap"]
        self.supported_formats = DOCUMENT_CONFIG["supported_formats"]
        self.min_chunk_length = DOCUMENT_CONFIG["min_chunk_length"]
        self.max_chunk_length = DOCUMENT_CONFIG["max_chunk_length"]
        self.separators = DOCUMENT_CONFIG["separators"]
        
        log.info(f"DocumentLoader initialized (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})")
    
    def load_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Load a document from file path and return chunked content.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            List[DocumentChunk]: List of document chunks with metadata
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check if format is supported
        if path.suffix.lower() not in self.supported_formats:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        
        log.info(f"Loading document: {path.name}")
        
        # Route to appropriate loader based on file extension
        if path.suffix.lower() == '.pdf':
            text = self._load_pdf(path)
        elif path.suffix.lower() == '.docx':
            text = self._load_docx(path)
        elif path.suffix.lower() in ['.html', '.htm']:
            text = self._load_html(path)
        else:  # .txt, .md, or other text files
            text = self._load_text(path)
        
        # Create chunks from the extracted text
        chunks = self._create_chunks(
            text=text,
            source=str(path),
            document_type=path.suffix.lower()
        )
        
        log.info(f"Successfully loaded {len(chunks)} chunks from {path.name}")
        return chunks
    
    def load_directory(self, directory_path: str) -> List[DocumentChunk]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory_path (str): Path to directory containing documents
            
        Returns:
            List[DocumentChunk]: Combined list of chunks from all documents
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        all_chunks = []
        
        # Find all supported files
        for ext in self.supported_formats:
            for file_path in dir_path.rglob(f"*{ext}"):
                try:
                    chunks = self.load_document(str(file_path))
                    all_chunks.extend(chunks)
                except Exception as e:
                    log.error(f"Failed to load {file_path.name}: {str(e)}")
        
        log.info(f"Loaded {len(all_chunks)} total chunks from {len(set(c.metadata['source'] for c in all_chunks))} documents")
        return all_chunks
    
    def _load_text(self, path: Path) -> str:
        """Load plain text file."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf(self, path: Path) -> str:
        """
        Load PDF file and extract text from all pages.
        
        Args:
            path (Path): Path to PDF file
            
        Returns:
            str: Extracted text from all pages
        """
        reader = PdfReader(path)
        text_parts = []
        
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text.strip():  # Only add non-empty pages
                text_parts.append(f"[Page {page_num}]\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    def _load_docx(self, path: Path) -> str:
        """
        Load Word document and extract text from paragraphs.
        
        Args:
            path (Path): Path to DOCX file
            
        Returns:
            str: Extracted text from document
        """
        doc = Document(path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
    
    def _load_html(self, path: Path) -> str:
        """
        Load HTML file and extract clean text.
        
        Args:
            path (Path): Path to HTML file
            
        Returns:
            str: Cleaned text content
        """
        with open(path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style']):
            element.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _create_chunks(self, text: str, source: str, document_type: str) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks using hierarchical separators.
        
        This method:
        1. Tries to split on major separators first (paragraphs, sentences)
        2. Falls back to character-level splitting if needed
        3. Creates overlap between chunks to preserve context
        4. Filters out chunks that are too short or too long
        
        Args:
            text (str): Full text to chunk
            source (str): Source file path
            document_type (str): File extension/type
            
        Returns:
            List[DocumentChunk]: List of document chunks with metadata
        """
        chunks = []
        chunk_id = 0
        
        # Recursive text splitting with multiple separators
        splits = self._recursive_split(text, self.separators, self.chunk_size)
        
        # Create overlapping chunks
        for i in range(len(splits)):
            chunk_text = splits[i]
            
            # Add overlap from next chunk if available
            if i < len(splits) - 1 and len(chunk_text) < self.max_chunk_length:
                overlap_text = splits[i + 1][:self.chunk_overlap]
                chunk_text = chunk_text + " " + overlap_text
            
            # Filter by length
            if self.min_chunk_length <= len(chunk_text) <= self.max_chunk_length:
                metadata = {
                    "source": source,
                    "chunk_id": chunk_id,
                    "document_type": document_type,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                }
                
                chunks.append(DocumentChunk(text=chunk_text.strip(), metadata=metadata))
                chunk_id += 1
        
        return chunks
    
    def _recursive_split(self, text: str, separators: List[str], chunk_size: int) -> List[str]:
        """
        Recursively split text using a hierarchy of separators.
        
        Tries each separator in order, falling back to the next if chunks are still too large.
        
        Args:
            text (str): Text to split
            separators (List[str]): List of separators in order of preference
            chunk_size (int): Target chunk size
            
        Returns:
            List[str]: List of text splits
        """
        if not separators:
            # Base case: split by character if no separators left
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        separator = separators[0]
        splits = text.split(separator)
        
        result = []
        current_chunk = ""
        
        for split in splits:
            # If adding this split would exceed chunk size
            if len(current_chunk) + len(split) > chunk_size:
                if current_chunk:
                    result.append(current_chunk)
                
                # If split itself is too large, recursively split with next separator
                if len(split) > chunk_size:
                    sub_splits = self._recursive_split(split, separators[1:], chunk_size)
                    result.extend(sub_splits)
                    current_chunk = ""
                else:
                    current_chunk = split
            else:
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
        
        if current_chunk:
            result.append(current_chunk)
        
        return result


# Convenience function for loading documents
def load_documents(path: str) -> List[DocumentChunk]:
    """
    Convenience function to load documents from a file or directory.
    
    Args:
        path (str): Path to file or directory
        
    Returns:
        List[DocumentChunk]: List of document chunks
    """
    loader = DocumentLoader()
    
    path_obj = Path(path)
    if path_obj.is_dir():
        return loader.load_directory(path)
    else:
        return loader.load_document(path)
