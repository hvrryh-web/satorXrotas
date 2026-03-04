"""
Axiom Pipeline - Setup Configuration
=====================================

Entry point configuration for pip install.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="axiom-pipeline",
    version="1.0.0",
    author="Axiom Esports",
    author_email="dev@axiomesports.com",
    description="Production data pipeline for esports match data extraction and processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/axiomesports/axiom-pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.10",
    install_requires=[
        # Core dependencies
        "click>=8.0.0",
        "croniter>=1.4.0",
        "python-dateutil>=2.8.0",
        
        # Database
        "asyncpg>=0.28.0",
        
        # Web server (for daemon)
        "aiohttp>=3.8.0",
        "aiohttp-cors>=0.7.0",
        
        # Monitoring
        "prometheus-client>=0.17.0",
        
        # Utilities
        "pydantic>=2.0.0",
        "python-json-logger>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "responses>=0.23.0",
            "aioresponses>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "axiom-pipeline=pipeline.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
