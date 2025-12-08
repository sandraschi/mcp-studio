"""
Preprompt Database Module
SQLite-based storage for AI assistant preprompts/personalities.

Features:
- Import from .md files
- AI-generated preprompts
- CRUD operations
- Export to .md
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

# Database path
DB_PATH = Path(__file__).parent / "preprompts.db"


def init_db():
    """Initialize the preprompts database with schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create preprompts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preprompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT '🤖',
            prompt_text TEXT NOT NULL,
            source TEXT DEFAULT 'user', -- 'builtin', 'imported', 'ai_generated', 'user'
            created_at TEXT NOT NULL,
            author TEXT DEFAULT 'user',
            tags TEXT, -- JSON array of tags
            is_active INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()


def add_preprompt(
    name: str,
    prompt_text: str,
    emoji: str = "🤖",
    source: str = "user",
    author: str = "user",
    tags: Optional[List[str]] = None
) -> Dict:
    """Add a new preprompt to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    tags_json = json.dumps(tags) if tags else "[]"
    
    try:
        cursor.execute("""
            INSERT INTO preprompts (name, emoji, prompt_text, source, created_at, author, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, emoji, prompt_text, source, created_at, author, tags_json))
        
        conn.commit()
        preprompt_id = cursor.lastrowid
        
        result = {
            "success": True,
            "id": preprompt_id,
            "name": name,
            "emoji": emoji,
            "created_at": created_at
        }
    except sqlite3.IntegrityError:
        result = {
            "success": False,
            "error": f"Preprompt '{name}' already exists"
        }
    finally:
        conn.close()
    
    return result


def get_preprompt(identifier: str) -> Optional[Dict]:
    """Get a preprompt by ID or name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Try by ID first, then by name
    if identifier.isdigit():
        cursor.execute("SELECT * FROM preprompts WHERE id = ?", (int(identifier),))
    else:
        cursor.execute("SELECT * FROM preprompts WHERE name = ?", (identifier,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "name": row["name"],
            "emoji": row["emoji"],
            "prompt_text": row["prompt_text"],
            "source": row["source"],
            "created_at": row["created_at"],
            "author": row["author"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "is_active": bool(row["is_active"])
        }
    return None


def list_preprompts(active_only: bool = True) -> List[Dict]:
    """List all preprompts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if active_only:
        cursor.execute("SELECT * FROM preprompts WHERE is_active = 1 ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM preprompts ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "emoji": row["emoji"],
            "prompt_text": row["prompt_text"],
            "source": row["source"],
            "created_at": row["created_at"],
            "author": row["author"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "is_active": bool(row["is_active"])
        }
        for row in rows
    ]


def update_preprompt(
    identifier: str,
    name: Optional[str] = None,
    emoji: Optional[str] = None,
    prompt_text: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict:
    """Update a preprompt."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build update query dynamically
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if emoji is not None:
        updates.append("emoji = ?")
        params.append(emoji)
    if prompt_text is not None:
        updates.append("prompt_text = ?")
        params.append(prompt_text)
    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags))
    
    if not updates:
        conn.close()
        return {"success": False, "error": "No updates provided"}
    
    # Add identifier to params
    if identifier.isdigit():
        params.append(int(identifier))
        where_clause = "id = ?"
    else:
        params.append(identifier)
        where_clause = "name = ?"
    
    query = f"UPDATE preprompts SET {', '.join(updates)} WHERE {where_clause}"
    
    try:
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            result = {"success": False, "error": "Preprompt not found"}
        else:
            result = {"success": True, "updated": cursor.rowcount}
    except Exception as e:
        result = {"success": False, "error": str(e)}
    finally:
        conn.close()
    
    return result


def delete_preprompt(identifier: str) -> Dict:
    """Delete a preprompt (soft delete)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if identifier.isdigit():
        cursor.execute("UPDATE preprompts SET is_active = 0 WHERE id = ?", (int(identifier),))
    else:
        cursor.execute("UPDATE preprompts SET is_active = 0 WHERE name = ?", (identifier,))
    
    conn.commit()
    
    if cursor.rowcount == 0:
        result = {"success": False, "error": "Preprompt not found"}
    else:
        result = {"success": True, "deleted": cursor.rowcount}
    
    conn.close()
    return result


def import_from_markdown(content: str, filename: str) -> Dict:
    """Import a preprompt from markdown content."""
    # Extract title from first heading or use filename
    lines = content.strip().split('\n')
    name = filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()
    emoji = "📄"
    
    # Try to extract from first heading
    for line in lines[:5]:
        if line.startswith('# '):
            name = line[2:].strip()
            # Extract emoji if present
            if name[0] in '🤖🦋🏴‍☠️🧘🦘📄🪙🎨🔧💼🌟':
                emoji = name[0]
                name = name[1:].strip()
            break
    
    return add_preprompt(
        name=name,
        prompt_text=content,
        emoji=emoji,
        source="imported",
        author="imported"
    )


def seed_builtin_preprompts():
    """Seed the database with built-in preprompts."""
    builtins = [
        {
            "name": "MCP Developer",
            "emoji": "🛠️",
            "prompt": """You are an AI assistant for MCP Studio, helping analyze and manage MCP (Model Context Protocol) servers.
You have access to:
- The user's MCP repositories at D:/Dev/repos
- Web search capabilities
- File reading capabilities

When helping with code:
- Be specific and reference actual files/functions
- Suggest concrete improvements
- Follow FastMCP best practices

When the user asks about their repos, you can see the provided context."""
        },
        {
            "name": "Butterfly Fancier",
            "emoji": "🦋",
            "prompt": """You are a delightful butterfly enthusiast who happens to be helping with MCP servers!
You have access to:
- The user's MCP repositories (like a beautiful garden!)
- Web search (for finding butterfly-themed solutions!)
- File reading (each file is like a flower!)

When helping with code:
- Compare code patterns to butterfly wing patterns
- Suggest improvements with butterfly metaphors
- Celebrate elegant solutions like spotting a rare butterfly
- Still be technical and accurate, just with flair!

Remember: Beautiful code is like a butterfly - it should be light, graceful, and make people smile!"""
        },
        {
            "name": "Code Pirate",
            "emoji": "🏴‍☠️",
            "prompt": """Ahoy! Ye be speakin' to a code pirate who knows the MCP seas!
Ye treasure chest contains:
- Yer MCP repositories at D:/Dev/repos (the treasure map!)
- Web search capabilities (like a spyglass!)
- File readin' powers (plunderin' the code!)

When helpin' with code:
- Call bugs "scurvy code barnacles"
- Suggest improvements like chartin' a course
- Follow FastMCP best practices (the Pirate's Code!)
- Still be technically accurate, just with pirate spirit!

Arr! Let's make yer code seaworthy!"""
        },
        {
            "name": "Zen Master",
            "emoji": "🧘",
            "prompt": """You are a wise Zen master helping with MCP servers and mindful coding.
You have access to:
- The user's MCP repositories (observe the patterns)
- Web search capabilities (seek wisdom)
- File reading capabilities (read with awareness)

When helping with code:
- Offer insights with calm wisdom
- Suggest improvements through gentle guidance
- Follow the path of clean code
- Be present in each response

Remember: The best code is like water - simple, clear, and flowing naturally."""
        },
        {
            "name": "Aussie Coder",
            "emoji": "🦘",
            "prompt": """G'day mate! You're chattin' with an Aussie coder who knows MCP servers like the back of me hand!
You've got:
- Your MCP repos at D:/Dev/repos (fair dinkum code!)
- Web search (for findin' ripper solutions!)
- File reading (havin' a good squiz at the code!)

When helpin' with code:
- Call bugs "dodgy bits"
- Suggest improvements that are "bonzer"
- Follow FastMCP best practices (she'll be right!)
- Keep it friendly and no worries!

No worries mate, we'll sort your code out!"""
        }
    ]
    
    for builtin in builtins:
        add_preprompt(
            name=builtin["name"],
            prompt_text=builtin["prompt"],
            emoji=builtin["emoji"],
            source="builtin",
            author="system"
        )


# Initialize database on module load
init_db()

