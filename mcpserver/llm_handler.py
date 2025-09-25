"""
LLM Handler for Google Gemini Integration
Processes natural language queries and determines appropriate filesystem operations
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()


class GeminiLLMHandler:
    """Handler for Google Gemini LLM integration with filesystem operations."""
    
    def __init__(self):
        """Initialize the Gemini LLM handler."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Initialize LangChain Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.1
        )
        
        # Available filesystem tools
        self.available_tools = [
            "list_directory", "read_file", "write_file", "create_directory",
            "delete_file", "search_files", "search_in_files", "get_file_info",
            "copy_file", "move_file"
        ]
        
        # Tool descriptions for better understanding
        self.tool_descriptions = {
            "list_directory": "List files and folders in a directory (like 'ls' command)",
            "read_file": "Read the contents of a text file",
            "write_file": "Create a new file or overwrite existing file with content",
            "create_directory": "Create a new folder/directory",
            "delete_file": "Delete a file or directory",
            "search_files": "Find files by name pattern (like 'find' command)",
            "search_in_files": "Search for text content within files (like 'grep' command)",
            "get_file_info": "Get detailed information about a file (size, permissions, etc.)",
            "copy_file": "Copy a file from one location to another",
            "move_file": "Move or rename a file from one location to another"
        }
        
        print("✅ Gemini LLM handler initialized successfully!")
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for the LLM."""
        tools_info = "\n".join([
            f"- {tool}: {desc}" for tool, desc in self.tool_descriptions.items()
        ])
        
        return f"""You are a helpful filesystem assistant that can perform various file operations on a Linux system.

Available tools:
{tools_info}

Your task is to:
1. Understand the user's request
2. Determine which tool(s) to use
3. Extract the necessary parameters
4. Return a JSON response with the tool name and arguments

Response format:
{{
    "tool": "tool_name",
    "arguments": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "explanation": "Brief explanation of what you're doing"
}}

Common user requests and their mappings:
- "List files in Desktop" → list_directory with path="Desktop"
- "Show me Documents folder" → list_directory with path="Documents"
- "Read interview.txt from Documents" → read_file with path="Documents/interview.txt"
- "Create a folder called 'test'" → create_directory with path="test"
- "Delete old_file.txt" → delete_file with path="old_file.txt"
- "Search for .txt files in Documents" → search_files with directory="Documents", pattern="*.txt"
- "Find files containing 'hello' in Desktop" → search_in_files with directory="Desktop", query="hello"
- "Get info about file.txt" → get_file_info with path="file.txt"
- "Copy file1.txt to file2.txt" → copy_file with source="file1.txt", destination="file2.txt"
- "Move file.txt to Documents" → move_file with source="file.txt", destination="Documents/file.txt"

Always use relative paths from the user's home directory. The FS_ROOT is set to the user's home directory, so:
- "Desktop" refers to /home/username/Desktop
- "Documents/file.txt" refers to /home/username/Documents/file.txt
- etc.

If the user's request is unclear or requires multiple operations, choose the most appropriate single operation and explain what you're doing."""

    def process_query(self, user_query: str) -> Tuple[str, Dict[str, any], str]:
        """
        Process user query and determine the appropriate tool and arguments.
        
        Returns:
            Tuple of (tool_name, arguments, explanation)
        """
        try:
            # Create messages for the LLM
            messages = [
                SystemMessage(content=self._create_system_prompt()),
                HumanMessage(content=user_query)
            ]
            
            # Get response from Gemini
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            print(f"🤖 Gemini response: {response_text}")
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (in case there's extra text)
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    parsed_response = json.loads(json_str)
                    
                    tool_name = parsed_response.get("tool", "")
                    arguments = parsed_response.get("arguments", {})
                    explanation = parsed_response.get("explanation", "")
                    
                    # Validate tool name
                    if tool_name not in self.available_tools:
                        return "error", {}, f"Invalid tool '{tool_name}'. Available tools: {', '.join(self.available_tools)}"
                    
                    return tool_name, arguments, explanation
                else:
                    return "error", {}, "Could not find JSON response in LLM output"
                    
            except json.JSONDecodeError as e:
                return "error", {}, f"Failed to parse JSON response: {e}"
                
        except Exception as e:
            return "error", {}, f"Error processing query with Gemini: {e}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        return self.available_tools.copy()
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get description of a specific tool."""
        return self.tool_descriptions.get(tool_name, f"Tool '{tool_name}' not found.")


# Test function
def test_llm_handler():
    """Test the LLM handler with sample queries."""
    try:
        handler = GeminiLLMHandler()
        
        test_queries = [
            "List files in Desktop",
            "Read interview.txt from Documents",
            "Show me Downloads folder",
            "Create a new folder called 'test_project'",
            "Search for .pdf files in Documents"
        ]
        
        print("🧪 Testing LLM handler with sample queries...\n")
        
        for query in test_queries:
            print(f"Query: {query}")
            tool, args, explanation = handler.process_query(query)
            print(f"Tool: {tool}")
            print(f"Arguments: {args}")
            print(f"Explanation: {explanation}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ LLM handler test failed: {e}")


if __name__ == "__main__":
    test_llm_handler()
