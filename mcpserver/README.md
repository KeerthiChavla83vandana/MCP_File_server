# Custom LLM Chat App for Linux

A custom LLM chat application that connects to your local MCP filesystem server using Google Gemini AI. This app provides a simple chat interface to interact with your filesystem using natural language.

## 🏗️ Architecture

```
Web Browser → Streamlit Chat Interface → Google Gemini AI → MCP Client → MCP Server (fs_server.py) → Filesystem
```

## 🛠️ Available Tools

- 📁 **list_directory** - Browse folders
- 📖 **read_file** - Read file contents  
- ✏️ **write_file** - Create/edit files
- 🔍 **search_files** - Find files by name
- 🔎 **search_in_files** - Search text within files
- ℹ️ **get_file_info** - File metadata
- ➕ **create_directory** - Make new folders
- 🗑️ **delete_file** - Remove files
- 📋 **copy_file** - Copy files
- 📦 **move_file** - Move/rename files

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies
uv sync
```

### 2. Set Up Google Gemini API

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create `.env` file:
```bash
cp env_template.txt .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Run the Chat App

```bash
# Option 1: Use the run script
python3 run_chat_app.py

# Option 2: Run directly with Streamlit
streamlit run chat_app.py
```

### 4. Open in Browser

The app will open at: http://localhost:8501

## 📁 Project Structure

```
mcpserver/
├── chat_app.py              # Main Streamlit chat interface
├── mcp_client.py            # MCP client with stdio transport
├── llm_handler.py           # Google Gemini LLM integration
├── run_chat_app.py          # Simple run script
├── server/
│   ├── fs_server.py         # MCP filesystem server
│   └── fs.json              # MCP server configuration
├── pyproject.toml           # Dependencies and project config
├── env_template.txt         # Environment variables template
└── README.md               # This file
```

## 💬 Example Queries

- "List files in Desktop"
- "Show me Documents folder"
- "Read interview.txt from Documents"
- "Create a folder called 'test_project'"
- "Search for .pdf files in Documents"
- "Find files containing 'hello' in Desktop"
- "Get info about Downloads folder"
- "Copy file1.txt to file2.txt"
- "Move old_file.txt to Documents"

## 🔧 Configuration

### MCP Server Configuration (`server/fs.json`)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uv",
      "args": ["run", "server/fs_server.py"],
      "cwd": "/home/keerthichavlavandana/mcp2/mcpserver",
      "env": {
        "FS_ROOT": "/home/keerthichavlavandana"
      }
    }
  }
}
```

### Environment Variables (`.env`)

```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

## 🧪 Testing

### Test MCP Client
```bash
python3 mcp_client.py
```

### Test LLM Handler
```bash
python3 llm_handler.py
```

### Test Complete App
```bash
python3 run_chat_app.py
```

## 🔒 Security

- **FS_ROOT Sandboxing**: All file operations are restricted to your home directory
- **Path Validation**: Prevents directory traversal attacks
- **API Key Protection**: Store your Google API key securely in `.env`

## 🐛 Troubleshooting

### Common Issues

1. **"GOOGLE_API_KEY not found"**
   - Create `.env` file with your API key
   - Use `env_template.txt` as reference

2. **"Failed to connect to MCP server"**
   - Check if `fs_server.py` exists in `server/` directory
   - Verify `fs.json` configuration
   - Ensure `uv` is installed and working

3. **"Module not found" errors**
   - Run `uv sync` to install dependencies
   - Check if you're in the correct directory

4. **Streamlit connection issues**
   - Check if port 8501 is available
   - Try running with different port: `streamlit run chat_app.py --server.port 8502`

## 📝 Dependencies

- `mcp[cli]` - MCP client and server components
- `streamlit` - Web interface framework
- `google-generativeai` - Google Gemini AI integration
- `langchain-google-genai` - LangChain Gemini integration
- `python-dotenv` - Environment variable management
- `nest-asyncio` - Async support for Streamlit

## 🎯 Features

- ✅ **Natural Language Processing** - Chat with your files using plain English
- ✅ **Real-time File Operations** - Perform filesystem operations through chat
- ✅ **Attractive UI** - Modern, responsive Streamlit interface
- ✅ **Secure** - Sandboxed to your home directory
- ✅ **Extensible** - Easy to add new tools and features
- ✅ **Cross-platform** - Works on Linux, macOS, and Windows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Built with ❤️ using Streamlit, Google Gemini, and MCP**

Command to run: uv run streamlit chat_app.py

limitations:while searching files 

Problems:
❌ 1000 character limit: Too small for most files
❌ No streaming: Loads entire response into memory
❌ UI blocking: Large responses freeze the interface
3. MCP Client Buffer Limitations
In mcp_client_simple.py:
Problems:
❌ No size validation: Accepts unlimited response size
❌ Memory accumulation: Large responses stay in memory
❌ No timeout: Could hang on large operations

next to add: 
Add file size limits to server
Add file size limits to read file fuction
Add Response size limits to chat app
4. Add memory monitering to MCP Clinet
