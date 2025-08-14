"""Setup script for DNS MCP Server."""

from setuptools import setup, find_packages

setup(
    name="dns-mcp",
    version="0.1.0",
    description="A cross-platform DNS query MCP server using fastmcp with support for Windows/Linux/macOS",
    author="Power Li",
    author_email="pccr10001@gmail.com",
    packages=find_packages(),
    install_requires=[
        "fastmcp>=0.3.0",
        "dnspython>=2.4.0",
    ],
    entry_points={
        "console_scripts": [
            "dns-mcp=dns_mcp.server:cli_main",
        ],
    },
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
