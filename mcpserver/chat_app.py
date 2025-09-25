"""
Custom LLM Chat App for Linux
Streamlit frontend with simple  chat interface
Connects to MCP filesystem server via Google Gemini LLM
"""

import asyncio
import streamlit as st
import time
from typing import Dict, List, Any
import nest_asyncio

from mcp_client_simple import SimpleMCPClient
from llm_handler import GeminiLLMHandler

# Enable nested asyncio for Streamlit
nest_asyncio.apply()

'''Host:The main application that orchestrates everything llm runing,client intialization 

'''

class ChatApp:
    """Main chat application class."""
    
    def __init__(self):
        """Initialize the chat app."""
        self.mcp_client = None
        self.llm_handler = None
        self.connected = False
        
    async def initialize(self):
        """Initialize MCP client and LLM handler."""
        try:
            # Initialize MCP client
            self.mcp_client = SimpleMCPClient()
            self.connected = True
            st.success("✅ MCP filesystem client initialized!")
            
            # Initialize LLM handler
            self.llm_handler = GeminiLLMHandler()
            st.success("✅ Google Gemini LLM initialized!")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Initialization failed: {e}")
            return False
    
    async def process_user_message(self, user_message: str) -> str:
        """Process user message and return response."""
        if not self.connected or not self.llm_handler:
            return "❌ System not initialized. Please refresh the page."
        
        try:
            # Show processing indicator
            with st.spinner("🤖 Processing your request..."):
                # Get tool and arguments from LLM
                tool_name, arguments, explanation = self.llm_handler.process_query(user_message)
                
                if tool_name == "error":
                    return f"❌ {explanation}"
                
                # Execute the tool
                result = await self.mcp_client.call_tool(tool_name, arguments)
                
                # Format response based on tool type
                response = f"**{explanation}**\n\n"
                response += f"🔧 **Tool used:** `{tool_name}`\n"
                response += f"📝 **Arguments:** `{arguments}`\n\n"
                
                # Format result nicely based on tool type
                if tool_name == "list_directory":
                    formatted_result = self._format_directory_listing(result)
                elif tool_name == "read_file":
                    formatted_result = self._format_file_content(result)
                elif tool_name == "get_file_info":
                    formatted_result = self._format_file_info(result)
                else:
                    formatted_result = result
                
                response += f"📋 **Result:**\n{formatted_result}"
                
                return response
                
        except Exception as e:
            return f"❌ Error processing request: {e}"
    
    def _format_directory_listing(self, result: str) -> str:
        """Format directory listing result for better display."""
        try:
            import json
            # Parse the JSON result
            file_list = json.loads(result)
            
            if not file_list:
                return "📁 Directory is empty"
            
            formatted = "📁 **Files and directories:**\n\n"
            for item in file_list:
                if item.get('is_dir', False):
                    formatted += f"📁 **{item['name']}/** (directory)\n"
                else:
                    size = item.get('size', 0)
                    size_str = self._format_file_size(size)
                    formatted += f"📄 {item['name']} ({size_str})\n"
            
            return formatted
            
        except (json.JSONDecodeError, Exception) as e:
            return f"```\n{result}\n```"
    
    def _format_file_content(self, result: str) -> str:
        """Format file content result."""
        if len(result) > 1000:
            return f"```\n{result[:1000]}...\n[Content truncated - file is {len(result)} characters long]\n```"
        return f"```\n{result}\n```"
    
    def _format_file_info(self, result: str) -> str:
        """Format file info result."""
        try:
            import json
            info = json.loads(result)
            formatted = f"📄 **File Information:**\n\n"
            formatted += f"**Name:** {info.get('name', 'Unknown')}\n"
            formatted += f"**Path:** {info.get('path', 'Unknown')}\n"
            formatted += f"**Type:** {'Directory' if info.get('is_dir', False) else 'File'}\n"
            formatted += f"**Size:** {self._format_file_size(info.get('size', 0))}\n"
            formatted += f"**Exists:** {'Yes' if info.get('exists', False) else 'No'}\n"
            return formatted
        except (json.JSONDecodeError, Exception) as e:
            return f"```\n{result}\n```"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        elif size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Custom LLM Chat App",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background-color: #e8f4fd;
        border-left-color: #764ba2;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Custom LLM Chat App</h1>
        <p>Chat with your filesystem using Google Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_app" not in st.session_state:
        st.session_state.chat_app = ChatApp()
    
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
    
    # Sidebar
    with st.sidebar:
        st.header("🛠️ Available Tools")
        
        if st.session_state.initialized and st.session_state.chat_app.llm_handler:
            tools = st.session_state.chat_app.llm_handler.get_available_tools()
            for tool in tools:
                description = st.session_state.chat_app.llm_handler.get_tool_description(tool)
                st.write(f"**{tool}**")
                st.caption(description)
                st.write("---")
        
        st.header("💡 Example Queries")
        example_queries = [
            "List files in Desktop",
            "Show me Documents folder",
            "Read interview.txt from Documents",
            "Create a folder called 'test'",
            "Search for .pdf files in Documents",
            "Get info about Downloads folder"
        ]
        
        for query in example_queries:
            if st.button(f"💬 {query}", key=f"example_{query}"):
                st.session_state.user_input = query
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Initialize system if not done
        if not st.session_state.initialized:
            st.info("🔄 Initializing system...")
            if asyncio.run(st.session_state.chat_app.initialize()):
                st.session_state.initialized = True
                st.rerun()
            else:
                st.error("Failed to initialize. Please check your configuration.")
                st.stop()
        
        # Chat interface
        st.subheader("💬 Chat with your filesystem")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me to help with your files..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get assistant response
            with st.chat_message("assistant"):
                response = asyncio.run(st.session_state.chat_app.process_user_message(prompt))
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.subheader("📊 System Status")
        
        if st.session_state.initialized:
            st.success("✅ System Ready")
            st.success("✅ MCP Server Connected")
            st.success("✅ Gemini LLM Active")
            
            if st.session_state.chat_app.mcp_client:
                tools_count = len(st.session_state.chat_app.mcp_client.get_available_tools())
                st.info(f"🛠️ {tools_count} tools available")
        else:
            st.error("❌ System Not Ready")
        
        # Clear chat button
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.rerun()
        
        # System info
        st.subheader("ℹ️ About")
        st.markdown("""
        This app connects to your local MCP filesystem server and uses Google Gemini AI to understand your natural language requests and perform file operations.
        
        **Architecture:**
        - 🌐 **Streamlit Frontend** (This app)
        - 🤖 **Google Gemini LLM** (Natural language processing)
        - 🔌 **MCP Client** (stdio transport)
        - 🖥️ **MCP Server** (fs_server.py)
        - 📁 **Filesystem** (Your home directory)
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Custom LLM Chat App for Linux | Built with Streamlit, Google Gemini, and MCP"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
