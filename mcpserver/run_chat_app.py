#!/usr/bin/env python3
"""
Simple script to run the Custom LLM Chat App
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit chat app."""
    print("🚀 Starting Custom LLM Chat App...")
    print("📁 Make sure you have:")
    print("   1. Created .env file with GOOGLE_API_KEY")
    print("   2. MCP server (fs_server.py) is accessible")
    print("   3. All dependencies installed with: uv sync")
    print()
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found!")
        print("   Please create .env file with your GOOGLE_API_KEY")
        print("   Use env_template.txt as reference")
        print()
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "chat_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Chat app stopped by user")
    except Exception as e:
        print(f"❌ Error running chat app: {e}")

if __name__ == "__main__":
    main()
