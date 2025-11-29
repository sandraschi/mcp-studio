# MCPB/DXT Package Support in MCP Studio

## 🎯 Overview

MCP Studio now fully supports **"naked" MCPB and DXT package files** - you can drop a `.mcpb` or `.dxt` file into your discovery path and it will automatically:

1. ✅ **Detect** the package
2. ✅ **Extract** (unzip) the contents
3. ✅ **Parse** manifest.json
4. ✅ **Install** dependencies
5. ✅ **Launch** the server
6. ✅ **Connect** via stdio
7. ✅ **Display** in dashboard

---

## 📦 What Are MCPB/DXT Files?

### **MCPB** (Modern Format)
Standard packaging format for MCP servers:

```
awesome-mcp.mcpb (ZIP file)
├── manifest.json         # Metadata, dependencies, capabilities
├── server.py            # MCP server entry point
├── requirements.txt     # Python dependencies
└── assets/              # Icons, prompts, docs
    ├── icon.svg
    └── prompts/
        ├── system.md
        └── troubleshooting.md
```

### **DXT** (Deprecated Format)
Older packaging format, same structure as MCPB:

```
legacy-server.dxt (ZIP file)
├── manifest.json
├── server.py
└── requirements.txt
```

**Both formats are handled identically by MCP Studio!**

---

## 🚀 Usage

### **Quick Start**

1. **Drop the file** anywhere in your MCP discovery paths:
   ```
   ~/.mcp/servers/
   ~/Dev/repos/mcp-studio/mcp_servers/
   C:\Users\{user}\AppData\Roaming\Claude\
   ```

2. **That's it!** MCP Studio automatically:
   - Finds the .mcpb/.dxt file
   - Extracts it to cache
   - Installs dependencies
   - Launches the server
   - Shows it in dashboard

3. **Use it** from dashboard or Claude Desktop

---

## 🔧 How It Works

### **1. Discovery** (Automatic)

```python
# MCP Studio scans discovery paths every 30 seconds
for path in discovery_paths:
    for file in path.iterdir():
        if file.suffix in (".mcpb", ".dxt"):
            # Found a package!
            await _discover_dxt_server(file)
```

### **2. Extraction**

```python
# Extract to cache directory
cache_dir = ~/.mcp-studio/package-cache/awesome-mcp_{timestamp}/

# Unzip the package
with zipfile.ZipFile("awesome-mcp.mcpb") as zip:
    zip.extractall(cache_dir)
```

### **3. Manifest Parsing**

```python
# Read manifest.json
{
  "name": "awesome-mcp",
  "version": "1.0.0",
  "main": "server.py",
  "dependencies": {...}
}
```

### **4. Dependency Installation**

```python
# Install requirements.txt
pip install -q -r requirements.txt
```

### **5. Server Launch**

```python
# Launch server process
python {cache_dir}/server.py

# Connect via stdio (just like regular Python servers)
client = FastMCP.Client(StdioTransport(...))
await client.connect()
```

### **6. Dashboard Display**

```
┌─────────────────────────────────────┐
│ Awesome MCP               ● Online │
│ Source: package (mcpb)             │
│ 🔧 15 tools  •  v1.0.0             │
│ [Test] [Stop]                      │
└─────────────────────────────────────┘
```

---

## 📁 Cache Management

### **Cache Directory**
```
~/.mcp-studio/package-cache/
├── awesome-mcp_1698765432/     # Extracted MCPB
│   ├── manifest.json
│   ├── server.py
│   └── requirements.txt
├── legacy-server_1698765123/   # Extracted DXT
│   └── ...
```

### **Cache Features**
- ✅ **Reuses** cache if package unchanged
- ✅ **Cleanup** - Removes caches older than 7 days
- ✅ **Isolation** - Each package in separate directory
- ✅ **Timestamp-based** - New extraction if file modified

### **Manual Cleanup**
```bash
# Clear all package cache
rm -rf ~/.mcp-studio/package-cache/
```

---

## 🎯 Fallback Behavior

If `manifest.json` is missing or invalid, MCP Studio tries to find the entry point:

**Searches for:**
1. `server.py`
2. `main.py`
3. `__main__.py`
4. `{package-name}.py`
5. `mcp_server.py`

**In directories:**
- Root of extracted package
- First-level subdirectories

---

## 🔍 Supported Config Sources

MCP Studio now reads MCP configurations from:

### **1. Claude Desktop** ✅
```json
// C:\Users\{user}\AppData\Roaming\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["-m", "github_mcp"]
    }
  }
}
```

### **2. Cursor IDE** ✅ NEW!
```json
// C:\Users\{user}\AppData\Roaming\Cursor\User\settings.json
{
  "mcpServers": {
    "filesystem": {
      "command": "node",
      "args": ["/path/to/filesystem-mcp"]
    }
  }
}
```

### **3. Windsurf IDE** ✅
```json
// C:\Users\{user}\AppData\Roaming\Windsurf\mcp_settings.json
{
  "mcpServers": {
    "docker": {
      "command": "python",
      "args": ["-m", "docker_mcp"]
    }
  }
}
```

### **4. MCPB/DXT Packages** ✅ NEW!
```
Just drop the file:
  ~/mcp_servers/awesome-mcp.mcpb
  ~/mcp_servers/legacy-server.dxt
```

---

## 📊 Dashboard Display

**Packages are clearly marked:**

```
┌─────────────────────────────────────────┐
│ GitHub MCP                    ● Online │
│ Source: claude-desktop                 │
│ Type: python                           │
│ 🔧 25 tools  •  v1.2.0                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Awesome MCP                   ● Online │
│ Source: package (mcpb) 📦              │
│ Type: mcpb                             │
│ 🔧 15 tools  •  v1.0.0                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Legacy Server                ● Online  │
│ Source: package (dxt) ⚠️               │
│ Type: dxt                              │
│ 🔧 8 tools  •  v0.5.0                  │
└─────────────────────────────────────────┘
```

---

## 🛡️ Safety Features

### **Dependency Isolation**
- ✅ Dependencies installed in current Python environment
- ⚠️ **Recommendation:** Use virtual environments
- 💡 **Future:** Container-based isolation

### **Validation**
- ✅ Checks ZIP integrity
- ✅ Validates manifest.json structure
- ✅ Verifies entry point exists
- ✅ Logs all extraction steps

### **Error Handling**
- ✅ Corrupted ZIP → Warning logged, skipped
- ✅ Missing manifest → Fallback to common names
- ✅ Missing entry point → Error logged, not registered
- ✅ Dependency install fails → Warning, continues anyway

---

## 🔄 Workflow Examples

### **Example 1: Installing an MCPB Package**

```bash
# 1. Download package
wget https://example.com/awesome-mcp.mcpb

# 2. Move to discovery path
mv awesome-mcp.mcpb ~/.mcp/servers/

# 3. Wait 30 seconds (or restart MCP Studio)
# Discovery service finds and loads it automatically

# 4. Check dashboard
# Server appears with "Source: package (mcpb)"

# 5. Use it!
# Click tools, test them, use from Claude Desktop
```

### **Example 2: Legacy DXT Package**

```bash
# Same process, works identically
mv legacy-server.dxt ~/.mcp/servers/

# Shows with warning icon
# "Source: package (dxt) ⚠️"
# Still works perfectly!
```

### **Example 3: Multiple Packages**

```bash
# Drop multiple packages
~/.mcp/servers/
├── github-mcp.mcpb
├── docker-mcp.mcpb
├── filesystem-mcp.mcpb
└── legacy-tool.dxt

# All discovered and loaded automatically
# Each in separate cache directory
# All shown in dashboard
```

---

## 🐛 Troubleshooting

### **Package Not Detected**

**Check:**
1. File in discovery path?
   ```bash
   ls ~/.mcp/servers/
   ```

2. Correct extension? (`.mcpb` or `.dxt`)
   ```bash
   file awesome-mcp.mcpb
   # Should be: Zip archive data
   ```

3. Check MCP Studio logs:
   ```bash
   tail -f ~/.mcp-studio/logs/mcp-studio.log
   ```

### **Extraction Fails**

**Possible causes:**
- ❌ **Corrupted ZIP** - Re-download package
- ❌ **Permissions** - Check write access to `~/.mcp-studio/`
- ❌ **Disk space** - Ensure sufficient space

### **Dependencies Install Fails**

**Solutions:**
```bash
# Extract manually and install
unzip awesome-mcp.mcpb -d /tmp/awesome-mcp
cd /tmp/awesome-mcp
pip install -r requirements.txt

# Check requirements.txt for conflicts
cat requirements.txt
```

### **Server Won't Start**

**Check:**
1. Entry point exists?
   ```bash
   ls ~/.mcp-studio/package-cache/awesome-mcp_*/server.py
   ```

2. Python version compatible?
   ```bash
   python --version  # Should be 3.9+
   ```

3. Check server logs in dashboard

---

## 📚 Technical Details

### **Package Format Spec**

**MCPB manifest.json:**
```json
{
  "name": "awesome-mcp",
  "version": "1.0.0",
  "description": "An awesome MCP server",
  "author": "Your Name",
  "license": "MIT",
  "main": "server.py",
  "runtime": {
    "python": ">=3.9"
  },
  "dependencies": {
    "fastmcp": ">=2.11.0",
    "pydantic": ">=2.0.0"
  },
  "mcp": {
    "version": "1.0",
    "capabilities": ["tools", "resources", "prompts"]
  }
}
```

**Entry point (`server.py`):**
```python
from fastmcp import FastMCP

mcp = FastMCP("Awesome MCP")

@mcp.tool()
async def my_tool(param: str) -> str:
    '''My awesome tool.'''
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

---

## 🎯 Comparison with Regular Servers

| Feature | Python Server | MCPB Package | DXT Package |
|---------|---------------|--------------|-------------|
| **Installation** | Manual | Auto | Auto |
| **Dependencies** | Manual pip | Auto pip | Auto pip |
| **Updates** | Manual | Replace file | Replace file |
| **Distribution** | Git clone | Single file | Single file |
| **Documentation** | In repo | In package | In package |
| **Icons/Assets** | Separate | Bundled | Bundled |
| **Format** | Source code | ZIP archive | ZIP archive |
| **Status** | Current | Current | Deprecated |

---

## 🏆 Benefits

**For Users:**
- ✅ **One-file install** - Drop and go
- ✅ **No setup** - Auto-extraction, auto-deps
- ✅ **Easy updates** - Replace file
- ✅ **Portable** - Move between machines

**For Developers:**
- ✅ **Easy distribution** - Single file
- ✅ **Bundled assets** - Icons, prompts included
- ✅ **Version control** - Manifest tracks versions
- ✅ **Backwards compatible** - DXT still works

---

## 🚀 Future Enhancements

**Planned:**
- [ ] Container-based isolation for packages
- [ ] Dependency conflict detection
- [ ] Package signature verification
- [ ] Auto-update checking
- [ ] Package marketplace integration
- [ ] Custom package repositories

---

## 📝 Summary

**MCP Studio now handles ALL formats:**

- ✅ **Regular Python servers** - Source code, modules
- ✅ **MCPB packages** - Modern ZIP bundles
- ✅ **DXT packages** - Legacy ZIP bundles (deprecated but supported)
- ✅ **Claude Desktop** - Config parsing
- ✅ **Cursor IDE** - Config parsing
- ✅ **Windsurf IDE** - Config parsing

**Drop any .mcpb or .dxt file and it just works!** 🚀🇦🇹

