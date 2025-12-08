# MCP Studio Preprompt System - Demo Guide

**Date**: 2025-12-04  
**Demo Time**: 5 minutes  
**Wow Factor**: 🌟🌟🌟🌟🌟

## Quick Start

**Access**: http://goliath:8001 (Tailscale) or http://localhost:8001  
**Tab**: 🤖 AI Assistant

## Demo Script (5 Minutes)

### Act 1: Show Built-in Personalities (30 seconds)

**Say:** "MCP Studio has an AI Assistant with multiple personalities..."

**Do:**
1. Click AI Assistant tab
2. Show Personality dropdown
3. Point out 5 built-ins:
   - 🛠️ MCP Developer
   - 🦋 Butterfly Fancier  
   - 🏴‍☠️ Code Pirate
   - 🧘 Zen Master
   - 🦘 Aussie Coder

**Say:** "But the real magic is what happens next..."

### Act 2: AI Refine Generation (90 seconds)

**Say:** "Watch me create a new personality in 60 seconds using AI..."

**Do:**
1. Scroll to Preprompt Manager panel
2. Type in AI Refine field: **"detective"**
3. Click **"Generate"** button
4. Wait (show "Generating..." state)
5. Alert appears: **"✅ Generated 🕵️ Detective preprompt!"**

**Say:** "The AI just wrote a 250-word personality with detective metaphors!"

### Act 3: Use New Personality (60 seconds)

**Do:**
1. Open Personality dropdown
2. Show **"🕵️ Detective"** now in list
3. Select it
4. Click **"🔌 Connect to LLM"**
5. Read detective-themed welcome message

**Say:** "Now the AI will respond as a detective analyzing your code for clues!"

### Act 4: Show the Generated Text (60 seconds)

**Say:** "Let's see what the AI created..."

**Do:**
1. Open new terminal
2. Run: `curl http://localhost:8001/api/preprompts/detective | python -m json.tool`
3. Show the elaborate preprompt text

**Say:** "This is what your local LLM generated - notice the metaphors, creativity, yet still technically focused!"

### Act 5: Import Demo (Optional, 30 seconds)

**Say:** "You can also import markdown files..."

**Do:**
1. Show file upload button
2. Click "📁 Import .md File"
3. Select a prepared .md file
4. Shows success alert
5. New personality in dropdown

## Prepared Test Concepts

**Quick to generate (sorted by wow factor):**

| Concept | Emoji | Style | Demo Value |
|---------|-------|-------|------------|
| detective | 🕵️ | Analyzes code like crime scenes | ⭐⭐⭐⭐⭐ |
| chef | 👨‍🍳 | Code recipes and ingredients | ⭐⭐⭐⭐⭐ |
| wizard | 🧙 | Magical code spells | ⭐⭐⭐⭐⭐ |
| astronaut | 🚀 | Space exploration metaphors | ⭐⭐⭐⭐ |
| archaeologist | 🏺 | Digging through legacy code | ⭐⭐⭐⭐ |
| librarian | 📚 | Organizing code knowledge | ⭐⭐⭐⭐ |
| surgeon | ⚕️ | Precise code operations | ⭐⭐⭐⭐ |
| architect | 🏗️ | Structural design patterns | ⭐⭐⭐ |

## Audience Reactions

**Expected responses:**
- "Wait, it generates personalities ON THE FLY?"
- "Can I make my own?"
- "This is hilarious AND useful!"
- "How many can I create?" (Answer: Infinite!)
- "Can I share these?" (Answer: Export to .md, yes!)

## Technical Talking Points

**If asked about implementation:**
- SQLite database (lightweight, fast)
- REST API (standard CRUD operations)
- Ollama integration (local LLM, no cloud)
- 150-250 word prompts (optimal length)
- Emoji auto-detection (keyword mapping)
- FastAPI backend (Python async)

## Fallback Plans

### If AI Generation Fails
**Backup**: Show import feature instead
- Have prepared .md file ready
- Upload and demonstrate instant addition
- Still impressive!

### If Ollama Slow
**Backup**: Use pre-generated
- Say "I generated these earlier..."
- Show Long John Silver and Coin Col
- Still demonstrates the concept!

### If Demo Crashes
**Backup**: API demonstration
```bash
# Show via curl
curl http://localhost:8001/api/ai/preprompts
```

## Success Indicators

**You nailed the demo if audience says:**
- "I want to try this!"
- "Can I use this for my project?"
- "This is way better than hardcoded prompts"
- "The AI generation is genius!"

## Post-Demo

**Share**:
- GitHub: https://github.com/sandraschi/mcp-studio
- Docs: http://localhost:8001/docs/PREPROMPT_SYSTEM.md
- API Docs: http://localhost:8001/api/docs

**Next Steps for Audience:**
1. Clone repo
2. Run `python studio_dashboard.py`
3. Navigate to AI Assistant
4. Generate first custom personality!

---

**Remember**: This system is demo-ready because it's REAL - not a mock-up. Everything actually works, including the AI generation. That's what makes it impressive!


