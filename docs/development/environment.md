# Development Environment Setup

This guide will help you set up a local development environment for MCP Studio.

## Prerequisites

- Python 3.10 or later
- Node.js 16+ (for frontend assets)
- Git
- (Optional) Docker and Docker Compose

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/sandraschi/mcp-studio.git
cd mcp-studio
```

### 2. Set Up Python Environment

#### Using venv (recommended):

```bash
# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e .[dev]
```

#### Using conda:

```bash
conda create -n mcp-studio python=3.10
conda activate mcp-studio
pip install -e .[dev]
```

### 3. Install Pre-commit Hooks

```bash
pre-commit install
```

### 4. Set Up Frontend Dependencies

```bash
# Install Node.js dependencies
npm install -g tailwindcss postcss autoprefixer

# Build frontend assets
npm run build
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
# App settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite by default)
DATABASE_URL=sqlite:///mcp-studio.db

# Redis (for caching and async tasks)
REDIS_URL=redis://localhost:6379/0
```

### 6. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Create initial data
python -m mcp_studio.cli init
```

### 7. Start Development Server

```bash
# Start the development server
uvicorn mcp_studio.main:app --reload
```

The application will be available at http://localhost:8000

## Docker Setup (Alternative)

If you prefer using Docker:

```bash
# Build and start containers
docker-compose up --build

# Run migrations
docker-compose run --rm app alembic upgrade head

# Create initial data
docker-compose run --rm app python -m mcp_studio.cli init
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py -v
```

### Code Quality

```bash
# Run linters
flake8 src tests

# Run type checking
mypy src

# Format code
black src tests
isort src tests
```

### Documentation

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- Black Formatter
- isort
- GitLens
- Docker
- ESLint
- Prettier

### PyCharm

1. Mark `src` as Sources Root
2. Enable Black or use built-in formatter
3. Configure Python interpreter to use the virtual environment

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Ensure the database server is running
   - Check connection string in `.env`

2. **Missing dependencies**
   - Run `pip install -e .[dev]`
   - Clear pip cache: `pip cache purge`

3. **Frontend assets not updating**
   - Run `npm run build`
   - Check browser cache

4. **Import errors**
   - Ensure virtual environment is activated
   - Run `pip install -e .`

## Getting Help

If you encounter any issues, please:
1. Check the [Troubleshooting](#troubleshooting) section
2. Search the [issue tracker](https://github.com/sandraschi/mcp-studio/issues)
3. Open a new issue if the problem persists
