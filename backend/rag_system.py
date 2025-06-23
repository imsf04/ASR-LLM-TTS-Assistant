import dashscope
from dashscope import Generation
from typing import Dict, Any, List, Generator, Optional
import json
import logging
from datetime import datetime

class RAGSystem:
    """RAG (Retrieval-Augmented Generation) system using DashScope"""
    
    def __init__(self, config):
        """
        Initialize RAG system
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.chat_history = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize DashScope
        dashscope.api_key = config.DASHSCOPE_API_KEY
        
        # Import vector store after initialization
        from .knowledge_base import KnowledgeBaseManager
        self.kb_manager = KnowledgeBaseManager(config)
        
    def _build_context_prompt(self, user_message: str) -> str:
        """
        Build context-aware prompt using RAG
        
        Args:
            user_message: User's input message
            
        Returns:
            Enhanced prompt with context
        """
        try:
            # Retrieve relevant documents
            relevant_docs = self.kb_manager.search_similar_documents(
                user_message, 
                k=self.config.RETRIEVAL_K
            )
            
            # Build context
            context_parts = []
            if relevant_docs:
                context_parts.append("相关参考信息：")
                for i, doc in enumerate(relevant_docs, 1):
                    context_parts.append(f"{i}. {doc['content']}")
                context_parts.append("")
            
            # Add chat history
            if self.chat_history:
                context_parts.append("对话历史：")
                for msg in self.chat_history[-5:]:  # Last 5 messages
                    context_parts.append(f"用户: {msg['user']}")
                    context_parts.append(f"助手: {msg['assistant']}")
                context_parts.append("")
            
            # Add current question
            context_parts.append(f"当前问题: {user_message}")
            
            full_context = "\n".join(context_parts)
            
            # Ensure context doesn't exceed max length
            if len(full_context) > self.config.MAX_CONTEXT_LENGTH:
                # Truncate context while preserving current question
                truncated_context = full_context[:self.config.MAX_CONTEXT_LENGTH-len(user_message)-50]
                full_context = truncated_context + f"\n\n当前问题: {user_message}"
            
            return full_context
            
        except Exception as e:
            self.logger.error(f"Error building context: {str(e)}")
            return user_message
    
    def chat_stream(self, user_message: str) -> Generator[Dict[str, Any], None, None]:
        """
        Stream chat response using RAG
        
        Args:
            user_message: User's input message
            
        Yields:
            Chunks of response data
        """
        try:
            # Build enhanced prompt
            enhanced_prompt = self._build_context_prompt(user_message)
            
            # Prepare messages for API
            messages = [
                {
                    "role": "system", 
                    "content": self.config.SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ]
            
            # Call DashScope API with streaming
            responses = Generation.call(
                model=self.config.LLM_MODEL,
                messages=messages,
                result_format='message',
                stream=True,
                incremental_output=True,
                max_tokens=2000,
                temperature=0.7
            )
            
            full_response = ""
            
            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if content:
                        full_response += content
                        yield {
                            "content": content,
                            "timestamp": datetime.now().isoformat()
                        }
                else:
                    self.logger.error(f"API error: {response.message}")
                    yield {
                        "error": f"API调用失败: {response.message}",
                        "timestamp": datetime.now().isoformat()
                    }
                    return
            
            # Save to chat history
            self._add_to_history(user_message, full_response)
            
        except Exception as e:
            self.logger.error(f"Chat streaming error: {str(e)}")
            yield {
                "error": f"生成回答时发生错误: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def chat(self, user_message: str) -> str:
        """
        Non-streaming chat response using RAG
        
        Args:
            user_message: User's input message
            
        Returns:
            Complete response text
        """
        try:
            # Build enhanced prompt
            enhanced_prompt = self._build_context_prompt(user_message)
            
            # Prepare messages for API
            messages = [
                {
                    "role": "system", 
                    "content": self.config.SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": enhanced_prompt
                }
            ]
            
            # Call DashScope API
            response = Generation.call(
                model=self.config.LLM_MODEL,
                messages=messages,
                result_format='message',
                max_tokens=2000,
                temperature=0.7
            )
            
            if response.status_code == 200:
                assistant_response = response.output.choices[0].message.content
                
                # Save to chat history
                self._add_to_history(user_message, assistant_response)
                
                return assistant_response
            else:
                self.logger.error(f"API error: {response.message}")
                return f"抱歉，生成回答时发生错误: {response.message}"
                
        except Exception as e:
            self.logger.error(f"Chat error: {str(e)}")
            return f"抱歉，生成回答时发生错误: {str(e)}"
    
    def _add_to_history(self, user_message: str, assistant_response: str):
        """
        Add conversation to chat history
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
        """
        self.chat_history.append({
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.chat_history) > self.config.MAX_CHAT_HISTORY:
            self.chat_history = self.chat_history[-self.config.MAX_CHAT_HISTORY:]
    
    def clear_history(self):
        """Clear chat history"""
        self.chat_history = []
        self.logger.info("Chat history cleared")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get chat history
        
        Returns:
            List of chat history entries
        """
        return self.chat_history.copy()
