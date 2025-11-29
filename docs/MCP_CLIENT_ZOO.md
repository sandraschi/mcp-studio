# MCP Client Zoo - Comprehensive Client Support

## 🦁 The MCP Client Zoo

MCP Studio now supports **ALL known MCP clients** as of 2025! Drop your config from any client and it just works!

---

## 📊 Supported Clients (9 Total)

| # | Client | Status | Config Format | Notes |
|---|--------|--------|---------------|-------|
| 1 | **Claude Desktop** | ✅ | `mcpServers` | Official Anthropic client |
| 2 | **Cursor IDE** | ✅ | `mcpServers` | AI-first IDE |
| 3 | **Windsurf IDE** | ✅ | `mcpServers` | Codeium IDE |
| 4 | **Cline** | ✅ | `mcpServers` | VSCode extension (was Claude Dev) |
| 5 | **Roo-Cline** | ✅ | `mcpServers` | Windsurf's Cline fork |
| 6 | **Continue.dev** | ✅ | `mcpServers` | VSCode AI coding assistant |
| 7 | **LM Studio** | ✅ | `mcpServers` | Local model runner |
| 8 | **Zed Editor** | ✅ | `mcpServers` | Modern code editor |
| 9 | **VSCode Generic** | ✅ | `mcpServers` | Generic VSCode MCP config |

---

## 🔍 Config Locations

### **1. Claude Desktop** (Anthropic Official)

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Claude\claude_desktop_config.json
```

**Linux/Mac:**
```
~/.config/Claude/claude_desktop_config.json
```

**Format:**
```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "github_mcp"]
    }
  }
}
```

---

### **2. Cursor IDE** (AI-First IDE)

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
C:\Users\{user}\AppData\Roaming\Cursor\mcp_settings.json
```

**Linux:**
```
~/.config/Cursor/User/mcp_settings.json
~/.cursor/mcp_settings.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

### **3. Windsurf IDE** (Codeium IDE)

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Windsurf\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json
C:\Users\{user}\AppData\Roaming\Windsurf\mcp_settings.json
```

**Linux:**
```
~/.config/Windsurf/mcp_settings.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

### **4. Cline** (VSCode Extension)

**Formerly "Claude Dev"** - VSCode extension for Claude

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

**Linux:**
```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

**Mac:**
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

### **5. Roo-Cline** (Windsurf's Fork)

**Windsurf's version of Cline**

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Windsurf\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json
C:\Users\{user}\AppData\Roaming\Cline\mcp_settings.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

**Note:** Often shares config with Windsurf IDE

---

### **6. Continue.dev** (VSCode Extension)

**Open-source AI coding assistant**

**All Platforms:**
```
~/.continue/config.json
```

**Windows (VSCode):**
```
C:\Users\{user}\AppData\Roaming\Code\User\globalStorage\continue.continue\config.json
```

**Linux (VSCode):**
```
~/.config/Code/User/globalStorage/continue.continue/config.json
```

**Format:** 
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": ["/path/to/filesystem-mcp"]
    }
  }
}
```

**Note:** Continue.dev might also use `"mcp": {...}` instead of `"mcpServers"`

---

### **7. LM Studio** (Local Model Runner)

**Desktop app for running local LLMs**

**Windows:**
```
C:\Users\{user}\AppData\Roaming\LM Studio\mcp_config.json
```

**All Platforms:**
```
~/.lmstudio/mcp_config.json
```

**Mac:**
```
~/Library/Application Support/LM Studio/mcp_config.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

### **8. Zed Editor** (Modern Code Editor)

**Rust-based collaborative code editor**

**All Platforms:**
```
~/.config/zed/mcp.json
```

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Zed\mcp.json
```

**Mac:**
```
~/Library/Application Support/Zed/mcp.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

### **9. VSCode Generic**

**Generic VSCode with MCP support**

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Code\User\mcp_settings.json
```

**Linux:**
```
~/.config/Code/User/mcp_settings.json
```

**Mac:**
```
~/Library/Application Support/Code/User/mcp_settings.json
```

**Format:** Same as Claude Desktop (`mcpServers`)

---

## 🎯 How MCP Studio Handles The Zoo

### **Automatic Discovery**

MCP Studio scans **ALL** of these locations automatically:

```python
# Every 30 seconds, scans:
clients = [
    "claude-desktop",
    "cursor-ide", 
    "windsurf-ide",
    "cline-vscode",
    "roo-cline",
    "continue-dev",
    "lm-studio",
    "zed-editor",
    "vscode-generic"
]

for client in clients:
    servers = parse_client_config(client)
    if servers:
        print(f"✅ Found {len(servers)} servers in {client}")
```

### **Deduplication**

Same server in multiple clients? No problem!

```
GitHub MCP in Claude Desktop  ─┐
GitHub MCP in Cursor IDE      ─┼─→ Deduplicated to 1 server
GitHub MCP in Windsurf IDE    ─┘
```

Dashboard shows: **"Source: claude-desktop, cursor-ide, windsurf-ide"**

---

## 📊 Dashboard Display

**Servers are tagged by source:**

```
┌─────────────────────────────────────────┐
│ GitHub MCP                    ● Online │
│ Source: claude-desktop, cursor-ide     │
│ 🔧 25 tools  •  v1.2.0                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Docker MCP                    ● Online │
│ Source: windsurf-ide                   │
│ 🔧 30 tools  •  v2.0.1                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Filesystem MCP                ● Online │
│ Source: lm-studio, zed-editor          │
│ 🔧 18 tools  •  v1.0.0                 │
└─────────────────────────────────────────┘
```

---

## 🔧 Implementation Details

### **Standard Format Parser**

Most clients use the same format:

```python
def _parse_standard_format(paths, source):
    '''Parse standard mcpServers format.'''
    for config_path in paths:
        config = json.load(config_path)
        
        if "mcpServers" in config:
            for server_id, server_config in config["mcpServers"].items():
                # Extract command, args, cwd, env
                servers.append(...)
```

**Supported by:**
- Claude Desktop ✅
- Cursor IDE ✅
- Windsurf IDE ✅
- Cline ✅
- Roo-Cline ✅
- LM Studio ✅
- Zed Editor ✅
- VSCode Generic ✅

### **Alternative Format Parser**

Continue.dev might use different structure:

```python
def _parse_continue_format(paths, source):
    '''Handle Continue.dev specific formats.'''
    # Try standard format first
    if "mcpServers" in config:
        # Standard format
    
    elif "mcp" in config:
        # Alternative format
        for server_id, server_config in config["mcp"].items():
            servers.append(...)
```

---

## 🎯 Usage Scenarios

### **Scenario 1: Multi-IDE Developer**

You use Claude Desktop for work, Cursor for personal projects, and Windsurf for experiments:

```
MCP Studio scans ALL three:
  ✅ 15 servers from Claude Desktop
  ✅ 8 servers from Cursor IDE
  ✅ 12 servers from Windsurf IDE
  
Dashboard shows: 20 unique servers
(15 deduplicated due to overlap)
```

### **Scenario 2: Local Models Enthusiast**

You use LM Studio for privacy, Zed for editing:

```
MCP Studio finds:
  ✅ LM Studio config → 5 servers
  ✅ Zed Editor config → 3 servers
  
All shown in unified dashboard!
```

### **Scenario 3: VSCode Power User**

Multiple VSCode extensions with MCP:

```
MCP Studio scans:
  ✅ Cline extension
  ✅ Continue.dev extension
  ✅ Generic VSCode config
  
Finds all servers from all extensions!
```

---

## 🦁 The Complete Zoo

**MCP Studio is now the UNIVERSAL MCP CLIENT MANAGER!**

```
        🦁 MCP CLIENT ZOO 🦁
        
┌─────────────────────────────────────┐
│                                     │
│   Claude Desktop  ──┐               │
│   Cursor IDE      ──┤               │
│   Windsurf IDE    ──┤               │
│   Cline           ──┤               │
│   Roo-Cline       ──┼──→  MCP       │
│   Continue.dev    ──┤     STUDIO    │
│   LM Studio       ──┤     📊        │
│   Zed Editor      ──┤               │
│   VSCode Generic  ──┘               │
│                                     │
│   ONE DASHBOARD TO RULE THEM ALL!  │
│                                     │
└─────────────────────────────────────┘
```

---

## 📚 Technical Notes

### **Config Format Compatibility**

**Standard Format (90% of clients):**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "package"],
      "cwd": "/optional/path",
      "env": {"KEY": "value"}
    }
  }
}
```

**Used by:** Claude, Cursor, Windsurf, Cline, Roo-Cline, LM Studio, Zed, VSCode

**Alternative Format (Continue.dev):**
```json
{
  "mcp": {
    "server-name": {
      "command": "...",
      "args": [...]
    }
  }
}
```

**MCP Studio handles BOTH!**

---

### **Deduplication Strategy**

**Key:** `command + args`

```python
# Same server, different clients
"python -m github_mcp" in Claude Desktop
"python -m github_mcp" in Cursor IDE
"python -m github_mcp" in Windsurf IDE

→ Deduplicated to 1 server
→ Source: "claude-desktop, cursor-ide, windsurf-ide"
```

---

## 🚀 Future-Proofing

**When new MCP clients appear:**

1. Add config path to respective parser
2. Determine if standard format or custom
3. Add to client zoo scan list
4. Done!

**Example - Adding "New IDE 2026":**
```python
def parse_new_ide_2026(self) -> List[MCPServerInfo]:
    paths = [
        Path.home() / ".newide2026" / "mcp_config.json"
    ]
    return self._parse_standard_format(paths, "new-ide-2026")
```

---

## 🏆 Benefits

### **For Users**
- ✅ **Universal** - Works with any MCP client
- ✅ **Auto-discovery** - No manual configuration
- ✅ **Unified view** - All servers in one dashboard
- ✅ **Multi-client** - Use multiple IDEs seamlessly

### **For Developers**
- ✅ **Test anywhere** - Works regardless of IDE
- ✅ **Cross-platform** - Same servers everywhere
- ✅ **No duplication** - Smart deduplication
- ✅ **Source tracking** - Know where servers came from

---

## 🎯 Summary

**MCP Studio supports:**

- ✅ **9 MCP clients** (and counting!)
- ✅ **Standard format** (`mcpServers`)
- ✅ **Alternative formats** (Continue.dev's `mcp`)
- ✅ **Cross-platform** (Windows, Linux, Mac)
- ✅ **Auto-discovery** (scans all locations)
- ✅ **Deduplication** (same server only shown once)
- ✅ **Source tracking** (shows which clients have it)

**If it uses MCP, MCP Studio supports it!** 🦁🇦🇹

---

## 🔮 The Future

As the MCP ecosystem grows, new clients will emerge. MCP Studio is designed to easily add support for:

- New IDEs
- New extensions
- New desktop apps
- New web interfaces
- Custom clients

**Just add the config path and format - that's it!**

---

**MCP Studio: The UNIVERSAL Mission Control for the entire MCP ecosystem!** 🚀🌍

