"""
Database models and operations using SQLAlchemy and Redis
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import redis
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from config import Config

logger = logging.getLogger(__name__)

# SQLAlchemy Base
Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

class Document(Base):
    """Document model"""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    extracted_text = Column(Text)
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime)
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = 'chat_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = 'chat_messages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize PostgreSQL
        self._init_postgres()
        
        # Initialize Redis
        self._init_redis()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            # Create connection string
            db_url = f"postgresql://{self.config.POSTGRES_USER}:{self.config.POSTGRES_PASSWORD}@{self.config.POSTGRES_HOST}:{self.config.POSTGRES_PORT}/{self.config.POSTGRES_DB}"
            
            # Create engine
            self.engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            self.logger.info("PostgreSQL initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                password=self.config.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            self.logger.info("Redis initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {str(e)}")
            raise
    
    def get_db_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # User operations
    def create_user(self, username: str, email: str, password_hash: str) -> User:
        """Create new user"""
        db = self.get_db_session()
        try:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        db = self.get_db_session()
        try:
            return db.query(User).filter(User.username == username).first()
        finally:
            db.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        db = self.get_db_session()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()
    
    # Document operations
    def create_document(self, user_id: str, filename: str, original_filename: str, 
                       file_path: str, file_size: int, mime_type: str = None) -> Document:
        """Create document record"""
        db = self.get_db_session()
        try:
            document = Document(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            return document
        finally:
            db.close()
    
    def update_document_processing(self, document_id: str, extracted_text: str, 
                                 chunk_count: int) -> bool:
        """Update document processing status"""
        db = self.get_db_session()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.extracted_text = extracted_text
                document.chunk_count = chunk_count
                document.is_processed = True
                document.processed_date = datetime.utcnow()
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        db = self.get_db_session()
        try:
            return db.query(Document).filter(Document.user_id == user_id).order_by(Document.upload_date.desc()).all()
        finally:
            db.close()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        db = self.get_db_session()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                db.delete(document)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    # Chat session operations
    def create_chat_session(self, user_id: str, title: str = None) -> ChatSession:
        """Create new chat session"""
        db = self.get_db_session()
        try:
            session = ChatSession(
                user_id=user_id,
                title=title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    def get_user_chat_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        db = self.get_db_session()
        try:
            return db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).order_by(ChatSession.updated_at.desc()).all()
        finally:
            db.close()
    
    def add_chat_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        """Add message to chat session"""
        db = self.get_db_session()
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(message)
            
            # Update session timestamp
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(message)
            return message
        finally:
            db.close()
    
    def get_chat_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get messages from chat session"""
        db = self.get_db_session()
        try:
            return db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp.asc()).limit(limit).all()
        finally:
            db.close()
    
    # Redis operations for caching and sessions
    def cache_user_session(self, user_id: str, session_data: Dict[str, Any], 
                          expiry_seconds: int = None) -> bool:
        """Cache user session data in Redis"""
        try:
            key = f"user_session:{user_id}"
            data = json.dumps(session_data, default=str)
            
            if expiry_seconds:
                self.redis_client.setex(key, expiry_seconds, data)
            else:
                self.redis_client.set(key, data)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache user session: {str(e)}")
            return False
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data from Redis"""
        try:
            key = f"user_session:{user_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get user session: {str(e)}")
            return None
    
    def delete_user_session(self, user_id: str) -> bool:
        """Delete user session from Redis"""
        try:
            key = f"user_session:{user_id}"
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.error(f"Failed to delete user session: {str(e)}")
            return False
    
    def cache_chat_messages(self, session_id: str, messages: List[Dict[str, Any]], 
                           expiry_seconds: int = 3600) -> bool:
        """Cache recent chat messages in Redis"""
        try:
            key = f"chat_messages:{session_id}"
            data = json.dumps(messages, default=str)
            self.redis_client.setex(key, expiry_seconds, data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to cache chat messages: {str(e)}")
            return False
    
    def get_cached_chat_messages(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached chat messages from Redis"""
        try:
            key = f"chat_messages:{session_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get cached chat messages: {str(e)}")
            return None
    
    def add_to_recent_messages(self, session_id: str, message: Dict[str, Any], 
                              max_messages: int = 20) -> bool:
        """Add message to recent messages list in Redis"""
        try:
            key = f"recent_messages:{session_id}"
            message_str = json.dumps(message, default=str)
            
            # Add to list and trim to max length
            pipe = self.redis_client.pipeline()
            pipe.lpush(key, message_str)
            pipe.ltrim(key, 0, max_messages - 1)
            pipe.expire(key, 3600)  # Expire after 1 hour
            pipe.execute()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to add recent message: {str(e)}")
            return False
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages from Redis"""
        try:
            key = f"recent_messages:{session_id}"
            messages = self.redis_client.lrange(key, 0, count - 1)
            
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            self.logger.error(f"Failed to get recent messages: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of both databases"""
        postgres_healthy = False
        redis_healthy = False
        
        # Check PostgreSQL
        try:
            db = self.get_db_session()
            db.execute("SELECT 1")
            postgres_healthy = True
            db.close()
        except Exception as e:
            self.logger.error(f"PostgreSQL health check failed: {str(e)}")
        
        # Check Redis
        try:
            self.redis_client.ping()
            redis_healthy = True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
        
        return {
            "postgres": postgres_healthy,
            "redis": redis_healthy
        }
