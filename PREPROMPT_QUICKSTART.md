# Preprompt System - Quick Reference

**Updated**: 2025-12-04

## TL;DR

**What**: AI personality management for MCP Studio  
**How**: SQLite database + AI generation + .md import  
**Why**: Infinite custom personalities without code changes  
**Demo**: Type "coin collector" → Generate → Ready in 60 seconds

---

## Quick Commands

### Start MCP Studio
```powershell
cd D:\Dev\repos\mcp-studio
python studio_dashboard.py
# Opens on http://localhost:8001
```

### Check Database
```powershell
python -c "import preprompt_db; preps = preprompt_db.list_preprompts(); print(f'{len(preps)} preprompts')"
```

### Generate via API
```powershell
curl -X POST http://localhost:8001/api/preprompts/ai-refine -H "Content-Type: application/json" -d '{\"text\": \"detective\", \"model_id\": \"qwen2.5:14b\"}'
```

### List All
```powershell
curl http://localhost:8001/api/ai/preprompts | python -m json.tool
```

---

## File Locations

| File | Path | Purpose |
|------|------|---------|
| Main App | `studio_dashboard.py` | Dashboard + API |
| Database Module | `preprompt_db.py` | CRUD operations |
| Database File | `preprompts.db` | SQLite storage |
| Config | `.env` | Port/CORS settings |
| Docs | `docs/PREPROMPT_SYSTEM.md` | Technical docs |
| Roadmap | `docs/PREPROMPT_ROADMAP.md` | Future plans |
| Demo Guide | `DEMO_PREPROMPTS.md` | Demo script |

---

## API Endpoints Cheat Sheet

```
GET    /api/ai/preprompts         → List all
POST   /api/preprompts/ai-refine  → AI generate (60s)
POST   /api/preprompts/import     → Upload .md
GET    /api/preprompts/{id}       → Get one
PUT    /api/preprompts/{id}       → Update
DELETE /api/preprompts/{id}       → Delete
POST   /api/preprompts/seed       → Reset to builtins
```

---

## Current Preprompts (7)

1. 🛠️ MCP Developer (default)
2. 🦋 Butterfly Fancier
3. 🏴‍☠️ Code Pirate
4. 🧘 Zen Master
5. 🦘 Aussie Coder
6. 🪙 Coin Col (AI-generated)
7. 🏴‍☠️ Long John Silver, Pirate (AI-generated)

---

## Troubleshooting One-Liners

**Preprompts not loading?**
```powershell
# Check database
Test-Path preprompts.db
```

**AI generation failing?**
```powershell
# Check Ollama
curl http://localhost:11434/api/tags
```

**Import not working?**
```powershell
# Check permissions
Get-Acl preprompts.db
```

**Dropdown empty?**
```powershell
# Reseed database
curl -X POST http://localhost:8001/api/preprompts/seed
```

---

## Demo Script (30 seconds)

```
"Type 'chef' → Click Generate → 
Wait 60s → New personality! → 
Select it → Connect → 
Chat with culinary AI! 🍳"
```

---

## Next Priorities

1. ✅ Verify chat uses preprompts
2. ⏳ Library browser UI
3. ⏳ Export to .md
4. ⏳ Usage analytics
5. ⏳ AI refinement options

---

## Contact/Issues

**GitHub**: https://github.com/sandraschi/mcp-studio  
**Issues**: File bug reports with preprompt ID  
**Logs**: Check terminal output for errors

---

**Pro Tip**: Generate 3-5 personalities before demos. Have variety ready to showcase!


