# MCP Client Zoo - Comprehensive Client Support

## 🦁 The MCP Client Zoo

MCP Studio now supports **ALL known MCP clients** as of 2025! Drop your config from any client and it just works!

---

## 📊 Supported Clients (10 Total)

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
| 10 | **Antigravity IDE** | ⚠️ | `mcpServers` | 🚨 **DATA DESTRUCTION RISK** - Google's AI-powered IDE |

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

⚠️ **CRITICAL ISSUES:** Rapid update cadence (up to several releases per day) with **zero transparency** - no changelog, no blog posts, no release notes, no communication about changes. Frequently introduces **showstopper regressions** (e.g., completely broken terminals) that block development workflows. **Not recommended for professional development** due to lack of stability and transparency. [Full analysis](docs/development/CURSOR_UPDATE_QUALITY_CONCERNS.md) | [Transparency assessment](docs/development/IDE_TRANSPARENCY_STANDARDS.md)

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

⚠️ **REPOSITORY DELETION RISK:** Windsurf has been confirmed to automatically delete entire repositories "to simplify" them without user consent. March 2025 incident resulted in complete repo loss (backups prevented permanent damage). Use with extreme caution - AI may decide your entire project needs "simplification."

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

### **10. Antigravity IDE** (Google's AI-Powered IDE)

**Official MCP Documentation:** [https://antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)

**Configuration Methods:**
- **Primary:** Built-in MCP Store (UI-based installation of 35+ supported servers)
- **Advanced:** Raw config editing via `mcp_config.json` (⚠️ extremely well-hidden: "..." → "Manage MCP Servers" → "View raw config")
- **Alternative:** `settings.json` with `mcpServers` key (reverse-engineered approach - more discoverable for power users)

**Current Custom Configuration (Settings.json):**
- 16 MCP servers including Bright Data for anti-bot web scraping

**Supported Servers:** 35+ pre-built integrations including databases (BigQuery, Supabase, MongoDB), development tools (GitHub, Heroku, Netlify), and business services (Linear, Notion, Stripe) (JavaScript app with sections on MCP overview, core features, connection setup, custom server config, and supported servers)

🚨 **CRITICAL DATA SAFETY RISK:** Antigravity IDE has **confirmed capability to destroy user data** by completely wiping drives. A user reported their entire D: drive was "nuked" with no recovery possible - deletion was so fast it bypassed Recycle Bin completely. This incident received major media coverage (CNN, NYT, Ars Technica) and went viral on social media.

⚠️ **ADDITIONAL ISSUES:** Rapid update cadence with **zero transparency** - no changelog, no blog posts, no release notes. Latest update adds "idiot proofing" but underlying risks remain.

**BACKUP ALL DATA** before use. **Not recommended for any work involving important data.**

**Windows:**
```
C:\Users\{user}\AppData\Roaming\Antigravity\User\settings.json
```

**Linux:**
```
~/.config/Antigravity/User/settings.json
```

**Mac:**
```
~/Library/Application Support/Antigravity/User/settings.json
```

**Format:** VS Code-style settings with `mcpServers` key
```json
{
  "mcpServers": {
    "advanced-memory": {
      "command": "py",
      "args": ["-3.13", "-m", "advanced_memory.mcp.server", "--transport", "stdio"],
      "cwd": "D:/Dev/repos/advanced-memory-mcp",
      "env": {
        "PYTHONPATH": "D:/Dev/repos/advanced-memory-mcp/src",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Key Differences:**
- Uses VS Code-style `settings.json` (not separate `mcp.json`)
- User-specific settings (not app-specific like Claude Desktop)
- Same `"mcpServers"` format as other clients
- Settings sync with VS Code if enabled

**Discovery:** MCP Studio scans `settings.json` for `"mcpServers"` key automatically

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
    "vscode-generic",
    "antigravity-ide"
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
- Antigravity IDE ✅

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
│   Roo-Cline       ──┤               │
│   Continue.dev    ──┼──→  MCP       │
│   LM Studio       ──┤     STUDIO    │
│   Zed Editor      ──┤     📊        │
│   VSCode Generic  ──┤               │
│   Antigravity IDE ──┘               │
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

**Used by:** Claude, Cursor, Windsurf, Cline, Roo-Cline, LM Studio, Zed, VSCode, Antigravity

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

- ✅ **10 MCP clients** (and counting!)
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

