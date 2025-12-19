from setuptools import setup, find_packages

setup(
    name="mcp-studio",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "fastmcp>=2.11.0",
        "mcp>=1.0.0,<2.0.0",  # CRITICAL: Prevent MCP 1.16.0+ Python 3.13 incompatibility
        "anyio>=4.0.0,<5.0.0",  # CRITICAL: Prevent incompatible anyio versions
        "structlog>=23.0.0",
        "aiofiles>=23.0.0",
        "watchdog>=3.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.0.0",
        "aiohttp>=3.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=3.0.0",
            "pytest-cov>=4.0.0",
            "pre-commit>=3.0.0",
        ]
    },
    include_package_data=True,
    package_data={
        "mcp_studio": ["templates/*.html", "templates/**/*.html", "static/*"],
    },
    entry_points={
        "console_scripts": [
            "mcp-studio=mcp_studio.main:main",
        ],
    },
)
