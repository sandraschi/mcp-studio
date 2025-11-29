# Contributing to MCP Studio

Thank you for your interest in contributing to **MCP Studio**! This is a hybrid fullstack application with both MCP server and web interface capabilities, so please read this guide carefully.

---

## 🎯 Project Overview

**MCP Studio** is Mission Control for the MCP Zoo 🦁🐘🦒 - a comprehensive web-based management platform for MCP servers. It features:

- 🔧 **MCP Server** (FastMCP 2.11)
- 🌐 **Web Interface** (React + FastAPI)
- 🎯 **Working Sets** (Config management)
- 📊 **Real-time Monitoring** (WebSocket)

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**
- **uv** (Python package manager) or **pip**

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/sandraschi/mcp-studio.git
cd mcp-studio

# Install Python dependencies
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend
npm install
cd ..

# Run tests
pytest tests/ -v
cd frontend && npm test && cd ..
```

---

## 🛠️ Development Workflow

### Backend (Python)

1. **Make Changes**
   ```bash
   # Edit files in src/mcp_studio/ or src/api/
   ```

2. **Lint & Format**
   ```bash
   ruff check .
   ruff format .
   ```

3. **Type Check**
   ```bash
   mypy src/
   ```

4. **Test**
   ```bash
   pytest tests/ -v --cov=src/mcp_studio
   ```

5. **Run MCP Server**
   ```bash
   python -m mcp_studio.server
   ```

### Frontend (React/TypeScript)

1. **Make Changes**
   ```bash
   # Edit files in frontend/src/
   ```

2. **Lint**
   ```bash
   cd frontend
   npm run lint
   ```

3. **Build**
   ```bash
   npm run build
   ```

4. **Test**
   ```bash
   npm test
   npm run cypress:open  # E2E tests
   ```

5. **Development Server**
   ```bash
   npm start
   ```

---

## 📝 Code Standards

### Python

- **Linter**: ruff
- **Formatter**: ruff format
- **Type Checker**: mypy
- **Line Length**: 100
- **Type Hints**: Required for all functions
- **Docstrings**: Required for all public functions (Google style)

**Example:**
```python
from typing import Optional
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

async def get_server_status(server_name: str) -> Optional[dict]:
    '''Get the status of an MCP server.
    
    Args:
        server_name: Name of the MCP server
        
    Returns:
        Server status dict or None if not found
        
    Examples:
        >>> status = await get_server_status("github")
        >>> status["health"]
        "healthy"
    '''
    logger.info("getting_server_status", server=server_name)
    # Implementation...
```

### TypeScript/React

- **Linter**: ESLint
- **Formatter**: Prettier (via ESLint)
- **Type Safety**: Strict TypeScript
- **Components**: Functional components with hooks
- **Props**: Define interfaces for all props

**Example:**
```typescript
import React, { useState, useEffect } from 'react';
import type { MCPServer } from '@/types';

interface ServerCardProps {
  server: MCPServer;
  onStatusChange?: (status: string) => void;
}

export const ServerCard: React.FC<ServerCardProps> = ({ 
  server, 
  onStatusChange 
}) => {
  const [status, setStatus] = useState(server.status);
  
  useEffect(() => {
    // Implementation...
  }, [server.name]);
  
  return (
    <div className="server-card">
      {/* JSX */}
    </div>
  );
};
```

---

## 🧪 Testing

### Python Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_working_sets.py -v

# Run with coverage
pytest tests/ -v --cov=src/mcp_studio --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm test

# E2E tests (interactive)
npm run cypress:open

# E2E tests (headless)
npm run cypress:run
```

### Writing Tests

**Python (pytest):**
```python
import pytest
from mcp_studio.working_sets import WorkingSetManager

@pytest.mark.asyncio
async def test_switch_working_set():
    manager = WorkingSetManager()
    result = await manager.switch_set("dev_work")
    assert result["success"] is True
    assert "backup_path" in result
```

**TypeScript (Jest + React Testing Library):**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ServerCard } from './ServerCard';

describe('ServerCard', () => {
  it('renders server name', () => {
    const server = { name: 'github', status: 'active' };
    render(<ServerCard server={server} />);
    expect(screen.getByText('github')).toBeInTheDocument();
  });
});
```

---

## 📚 Documentation

### Docstring Standards

**Python** - Use Google style:
```python
def parse_config(path: str, validate: bool = True) -> dict:
    '''Parse an MCP configuration file.
    
    Args:
        path: Path to the config file
        validate: Whether to validate the config
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        ValueError: If config is invalid
        FileNotFoundError: If file doesn't exist
        
    Examples:
        >>> config = parse_config("config.json")
        >>> config["mcpServers"]["github"]
        {...}
    '''
```

### Adding Documentation

- Update README.md for user-facing changes
- Update docs/ for technical details
- Add examples in docs/examples/
- Update API reference in docs/api/

---

## 🔄 Pull Request Process

1. **Fork & Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow code standards
   - Add tests
   - Update documentation

3. **Test Everything**
   ```bash
   # Python
   ruff check . && ruff format .
   mypy src/
   pytest tests/ -v
   
   # Frontend
   cd frontend
   npm run lint
   npm run build
   npm test
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "feat: add working set validation"
   ```

5. **Push & PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a pull request on GitHub.

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build/tooling changes

**Examples:**
```bash
git commit -m "feat: add working set preview mode"
git commit -m "fix: resolve config parsing error"
git commit -m "docs: update working sets guide"
```

---

## 🐛 Bug Reports

**Use GitHub Issues** with:

1. **Clear title**
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Environment** (OS, Python version, Node version)
6. **Logs/Screenshots**

**Template:**
```markdown
## Bug Description
Brief description

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows 11
- Python: 3.11.5
- Node: 18.17.0
- MCP Studio: 0.1.0

## Logs
```

---

## 💡 Feature Requests

**Use GitHub Issues** with:

1. **Clear description**
2. **Use case**
3. **Proposed solution** (optional)
4. **Alternatives considered** (optional)

---

## 🇦🇹 Code of Conduct

- Be respectful and inclusive
- Follow Austrian engineering standards (quality, precision, thoroughness)
- Provide constructive feedback
- Help others learn and grow

---

## 📞 Questions?

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and ideas
- **Documentation**: Check docs/ first

---

## 🏆 Recognition

Contributors are recognized in:
- CHANGELOG.md
- README.md contributors section
- Release notes

---

**Thank you for contributing to MCP Studio!** 🚀🇦🇹

