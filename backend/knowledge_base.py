import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

# Document processing
import PyPDF2
import docx
from bs4 import BeautifulSoup

# Vector database and embeddings
import chromadb
from chromadb.config import Settings
import dashscope
from dashscope import TextEmbedding

# Text processing
from langchain.text_splitter import RecursiveCharacterTextSplitter

class KnowledgeBaseManager:
    """Knowledge base management with vector storage"""
    
    def __init__(self, config):
        """
        Initialize knowledge base manager
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize DashScope for embeddings
        dashscope.api_key = config.DASHSCOPE_API_KEY
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        # Initialize ChromaDB
        self._init_vector_db()
        
        # Document metadata storage
        self.metadata_file = os.path.join(config.KNOWLEDGE_BASE_FOLDER, 'metadata.json')
        self.documents_metadata = self._load_metadata()
    
    def _init_vector_db(self):
        """Initialize ChromaDB vector database"""
        try:
            # Create vector database directory
            os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.VECTOR_DB_PATH,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"description": "Knowledge base for RAG system"}
            )
            
            self.logger.info("Vector database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector database: {str(e)}")
            raise
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load documents metadata from file"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load metadata: {str(e)}")
            return {}
    
    def _save_metadata(self):
        """Save documents metadata to file"""
        try:
            os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {str(e)}")
    
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """
        Add document to knowledge base
        
        Args:
            file_path: Path to document file
            
        Returns:
            Result dictionary with processing information
        """
        try:
            self.logger.info(f"Processing document: {file_path}")
            
            # Extract text from document
            text_content = self._extract_text_from_file(file_path)
            
            if not text_content.strip():
                raise ValueError("Document contains no extractable text")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text_content)
            
            if not chunks:
                raise ValueError("Failed to split document into chunks")
            
            # Generate embeddings and store in vector database
            filename = os.path.basename(file_path)
            document_id = self._generate_document_id(filename)
            
            # Process chunks in batches
            batch_size = 10
            total_chunks = 0
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_embeddings = self._generate_embeddings(batch_chunks)
                
                # Create IDs and metadata for batch
                batch_ids = [f"{document_id}_{j}" for j in range(i, i + len(batch_chunks))]
                batch_metadata = [
                    {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": j,
                        "chunk_length": len(chunk),
                        "timestamp": datetime.now().isoformat()
                    }
                    for j, chunk in enumerate(batch_chunks, start=i)
                ]
                
                # Add to ChromaDB
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_chunks,
                    metadatas=batch_metadata
                )
                
                total_chunks += len(batch_chunks)
            
            # Update document metadata
            self.documents_metadata[document_id] = {
                "filename": filename,
                "file_path": file_path,
                "total_chunks": total_chunks,
                "added_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path),
                "content_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
            }
            
            self._save_metadata()
            
            self.logger.info(f"Document processed successfully: {filename}, {total_chunks} chunks")
            
            return {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "chunks_added": total_chunks,
                "total_characters": len(text_content)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add document: {str(e)}")
            raise Exception(f"文档处理失败: {str(e)}")
    
    def search_similar_documents(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar document chunks
        """
        try:
            if not query.strip():
                return []
            
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            similar_docs = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    similar_docs.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity_score": 1 - distance,  # Convert distance to similarity
                        "rank": i + 1
                    })
            
            self.logger.info(f"Found {len(similar_docs)} similar documents for query: {query[:50]}...")
            return similar_docs
            
        except Exception as e:
            self.logger.error(f"Failed to search documents: {str(e)}")
            return []
    
    def delete_document(self, filename: str) -> bool:
        """
        Delete document from knowledge base
        
        Args:
            filename: Name of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find document ID
            document_id = None
            for doc_id, metadata in self.documents_metadata.items():
                if metadata['filename'] == filename:
                    document_id = doc_id
                    break
            
            if not document_id:
                raise ValueError(f"Document not found: {filename}")
            
            # Delete from ChromaDB (delete all chunks of this document)
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id},
                include=['ids']
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                self.logger.info(f"Deleted {len(results['ids'])} chunks from vector database")
            
            # Delete file if it exists
            file_path = self.documents_metadata[document_id]['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Deleted file: {file_path}")
            
            # Remove from metadata
            del self.documents_metadata[document_id]
            self._save_metadata()
            
            self.logger.info(f"Document deleted successfully: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document: {str(e)}")
            raise Exception(f"文档删除失败: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in knowledge base
        
        Returns:
            List of document information
        """
        try:
            documents = []
            for doc_id, metadata in self.documents_metadata.items():
                documents.append({
                    "document_id": doc_id,
                    "filename": metadata['filename'],
                    "total_chunks": metadata['total_chunks'],
                    "added_at": metadata['added_at'],
                    "file_size": metadata['file_size'],
                    "content_preview": metadata['content_preview']
                })
            
            # Sort by added_at (newest first)
            documents.sort(key=lambda x: x['added_at'], reverse=True)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Failed to list documents: {str(e)}")
            return []
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file formats"""
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif ext == '.pdf':
                return self._extract_text_from_pdf(file_path)
            
            elif ext in ['.docx', '.doc']:
                return self._extract_text_from_docx(file_path)
            
            elif ext == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove markdown syntax for better text processing
                    soup = BeautifulSoup(content, 'html.parser')
                    return soup.get_text()
            
            else:
                raise ValueError(f"Unsupported file format: {ext}")
                
        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {str(e)}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using DashScope"""
        try:
            response = TextEmbedding.call(
                model=self.config.EMBEDDING_MODEL,
                input=texts
            )
            
            if response.status_code == 200:
                embeddings = []
                for output in response.output['embeddings']:
                    embeddings.append(output['embedding'])
                return embeddings
            else:
                raise Exception(f"Embedding API error: {response.message}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def _generate_document_id(self, filename: str) -> str:
        """Generate unique document ID"""
        timestamp = datetime.now().isoformat()
        content = f"{filename}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            total_documents = len(self.documents_metadata)
            total_chunks = sum(doc['total_chunks'] for doc in self.documents_metadata.values())
            total_size = sum(doc['file_size'] for doc in self.documents_metadata.values())
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return {}
