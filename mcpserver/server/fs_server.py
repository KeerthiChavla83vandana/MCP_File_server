
from __future__ import annotations
from typing import Any, Optional
from pathlib import Path
import os, shutil, base64, json, re
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
# FastMCP is a tiny server framework to build MCP servers in Python
#It handles the MCP protocol (JSON‑RPC 2.0 over stdio)
load_dotenv()


mcp = FastMCP("filesystem")
'''
MCP server. It exposes filesystem functions as tools via @mcp.tool over stdio. 
Why Inspector uses only fs_server.py
The MCP Inspector is itself a Host. It launches and talks to MCP servers. It doesn’t run “clients” (like agent_client.py). So you use the Inspector to test servers (fs_server.py, weather.py) with structured JSON args. For natural prompts, run agent_client.py instead.
'''

def _get_fs_root() -> Path:
    root = os.getenv("FS_ROOT") or os.getcwd()
    return Path(root).resolve()


def _resolve_safe(path: str) -> Path:
    base = _get_fs_root()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"Path escapes FS_ROOT: {target}")
    return target


def _format_entry(p: Path) -> dict[str, Any]:
    try:
        stat = p.stat()
        return {
            "path": str(p),
            "name": p.name,
            "is_dir": p.is_dir(),
            "size": stat.st_size,
        }
    except Exception:
        return {"path": str(p), "name": p.name, "is_dir": p.is_dir(), "size": None}

# like ls command
@mcp.tool()
def list_directory(path: str = ".") -> list[dict[str, Any]]:
    """List entries in a directory under FS_ROOT."""
    directory = _resolve_safe(path)
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Not a directory: {directory}")
    return [_format_entry(child) for child in sorted(directory.iterdir())]

    
# ✅ Works for: .txt, .md, .py, .json, .csv, etc.
# ❌ Fails for: .pdf, .docx, .xlsx, .jpg, .png, .zip, etc.

@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> str:
    """Read and return file contents."""
    file_path = _resolve_safe(path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding=encoding)


@mcp.tool()
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write text to a file.

    Behavior:
    - If file does not exist: create it and write content.
    - If file exists: append content at the end.
    Returns both characters and actual bytes written.
    """
    file_path = _resolve_safe(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists() and not file_path.is_file():
        raise FileExistsError(f"Target exists and is not a file: {file_path}")

    mode = "a" if file_path.exists() else "w"

    # Count characters and encoded bytes before writing
    char_count = len(content)
    byte_count = len(content.encode(encoding))

    with file_path.open(mode, encoding=encoding) as f:
        f.write(content)

    action = "Appended" if mode == "a" else "Created"
    return (
        f"{action} file at {file_path} | "
        f"Characters written: {char_count} | "
        f"Bytes written: {byte_count}"
    )


@mcp.tool()
def search_files(path: str = ".", name_contains: Optional[str] = None) -> list[str]:
    """Find files by name substring within a directory tree."""
    root = _resolve_safe(path)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")
    results: list[str] = []
    needle = (name_contains or "").lower()
    for p in root.rglob("*"):
        if p.is_file() and (needle in p.name.lower()):
            results.append(str(p))
    return results


@mcp.tool()
def search_in_files(path: str = ".", text: str = "", encoding: str = "utf-8") -> list[dict[str, Any]]:
    """Search for text within files under a directory tree."""
    root = _resolve_safe(path)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Not a directory: {root}")
    if not text:
        return []
    out: list[dict[str, Any]] = []
    for p in root.rglob("*"):
        if p.is_file():
            try:
                content = p.read_text(encoding=encoding)
            except Exception:
                continue
            if text in content:
                out.append({"path": str(p)})
    return out


@mcp.tool()
def get_file_info(path: str) -> dict[str, Any]:
    """Return basic metadata for a file or directory."""
    p = _resolve_safe(path)
    if not p.exists():
        raise FileNotFoundError(f"Not found: {p}")
    info = _format_entry(p)
    info["exists"] = True
    return info


@mcp.tool()
def create_directory(path: str, exist_ok: bool = True) -> str:
    """Create a directory (and parents)."""
    p = _resolve_safe(path)
    p.mkdir(parents=True, exist_ok=exist_ok)
    return f"Created directory: {p}"


@mcp.tool()
def delete_file(path: str, recursive: bool = False) -> str:
    """Delete a file or directory (with recursive option)."""
    p = _resolve_safe(path)
    if not p.exists():
        return f"Already gone: {p}"
    if p.is_dir():
        if recursive:
            shutil.rmtree(p)
            return f"Removed directory tree: {p}"
        else:
            p.rmdir()
            return f"Removed directory: {p}"
    else:
        p.unlink()
        return f"Removed file: {p}"


@mcp.tool()
def copy_file(src: str, dst: str, overwrite: bool = True) -> str:
    """Copy a file within FS_ROOT."""
    s = _resolve_safe(src)
    d = _resolve_safe(dst)
    if not s.exists() or not s.is_file():
        raise FileNotFoundError(f"Source file not found: {s}")
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists() and not overwrite:
        raise FileExistsError(f"Destination exists: {d}")
    shutil.copy2(s, d)
    return f"Copied {s} -> {d}"


@mcp.tool()
def move_file(src: str, dst: str, overwrite: bool = True) -> str:
    """Move/rename a file or directory within FS_ROOT."""
    s = _resolve_safe(src)
    d = _resolve_safe(dst)
    if not s.exists():
        raise FileNotFoundError(f"Source not found: {s}")
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists() and not overwrite:
        raise FileExistsError(f"Destination exists: {d}")
    shutil.move(str(s), str(d))
    return f"Moved {s} -> {d}"



@mcp.tool()
def nl_command(prompt: str) -> str:
    """Natural-language command. Uses Gemini to plan a single filesystem action under FS_ROOT.

    Returns a textual summary or error. Requires GOOGLE_API_KEY in environment/.env.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception:
        return "Gemini support is not installed. Install langchain-google-genai and set GOOGLE_API_KEY."

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "GOOGLE_API_KEY not set. Add it to your .env or environment."

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))

    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=temperature)

    system = (
        "You are a file-operations planner. Respond ONLY with a JSON object on one line. "
        "Allowed actions: list_directory, read_file, write_file, create_directory, delete_file, copy_file, move_file, "
        "search_files, search_in_files, get_file_info. Paths MUST be relative to the sandbox root. "
        "Schemas:\n"
        "list_directory:{path}\n"
        "read_file:{path}\n"
        "write_file:{path,content}\n"
        "create_directory:{path}\n"
        "delete_file:{path,recursive?}\n"
        "copy_file:{src,dst,overwrite?}\n"
        "move_file:{src,dst,overwrite?}\n"
        "search_files:{path,name_contains}\n"
        "search_in_files:{path,text}\n"
        "get_file_info:{path}\n"
        "Example: {\"action\":\"list_directory\",\"args\":{\"path\":\"Desktop\"}}"
    )

    try:
        resp = llm.invoke(system + "\nUser: " + prompt)
        text = getattr(resp, "content", str(resp))
    except Exception as e:
        return f"LLM error: {e}"

    def _extract_json(s: str) -> Optional[dict[str, Any]]:
        s = s.strip()
        # remove code fences if present
        s = re.sub(r"^```[a-zA-Z]*", "", s).strip()
        s = re.sub(r"```$", "", s).strip()
        # try direct
        try:
            return json.loads(s)
        except Exception:
            pass
        # try to find first {...}
        m = re.search(r"\{[\s\S]*\}", s)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

    cmd = _extract_json(text)
    if not isinstance(cmd, dict):
        return f"Could not parse model output as JSON command: {text[:200]}"

    action = cmd.get("action")
    args = cmd.get("args") or {}
    # Execute the chosen action
    try:
        result: Any
        if action == "list_directory":
            result = list_directory(**args)
        elif action == "read_file":
            result = read_file(**args)
        elif action == "write_file":
            result = write_file(**args)
        elif action == "create_directory":
            result = create_directory(**args)
        elif action == "delete_file":
            result = delete_file(**args)
        elif action == "copy_file":
            result = copy_file(**args)
        elif action == "move_file":
            result = move_file(**args)
        elif action == "search_files":
            result = search_files(**args)
        elif action == "search_in_files":
            result = search_in_files(**args)
        elif action == "get_file_info":
            result = get_file_info(**args)
        else:
            return f"Unsupported action: {action}"

        # Convert structured results into a friendly sentence
        def summarize(a: str, ar: dict[str, Any], r: Any) -> str:
            if a == "list_directory" and isinstance(r, list):
                folder = ar.get("path", ".")
                count = len(r)
                names = ", ".join((e.get("name") or "?") for e in r[:10])
                more = "" if count <= 10 else f" (and {count-10} more)"
                return f"Found {count} item(s) in {folder}: {names}{more}."
            if a == "search_files" and isinstance(r, list):
                needle = ar.get("name_contains", "")
                count = len(r)
                names = ", ".join(Path(p).name for p in r[:10])
                more = "" if count <= 10 else f" (and {count-10} more)"
                return f"Found {count} file(s) matching '{needle}': {names}{more}."
            if a == "search_in_files" and isinstance(r, list):
                textq = ar.get("text", "")
                count = len(r)
                names = ", ".join(Path(d.get("path","?")).name for d in r[:10])
                more = "" if count <= 10 else f" (and {count-10} more)"
                return f"Found '{textq}' in {count} file(s): {names}{more}."
            if a == "get_file_info" and isinstance(r, dict):
                name = r.get("name", "?")
                kind = "folder" if r.get("is_dir") else "file"
                size = r.get("size")
                return f"{name} is a {kind} (size: {size} bytes)."
            if a == "read_file" and isinstance(r, str):
                preview = r[:200].replace("\n", " ")
                return f"Read file successfully. First 200 chars: {preview}{'…' if len(r)>200 else ''}"
            # For write/copy/move/delete/create, tools already return natural strings
            if isinstance(r, str):
                return r
            # Fallback: JSON dump
            return json.dumps(r, ensure_ascii=False)

        return summarize(action, args, result)
    except Exception as e:
        return f"Execution error: {e}"




if __name__ == "__main__":
    # Transport choice: stdio (default) or SSE (for web/network access)
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if transport == "sse":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        print(f"Running filesystem MCP server via SSE on {host}:{port}")
        mcp.run(transport="sse", host=host, port=port)
    else:
        print("Running filesystem MCP server via stdio")
        mcp.run(transport="stdio")


