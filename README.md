# DNS MCP Server

A DNS query MCP server built with FastMCP, supporting cross-platform operation (Windows/Linux/macOS) and customizable upstream DNS servers.

## Features

- 🔍 Support for multiple DNS record types (A, AAAA, MX, CNAME, TXT, NS, SOA)
- 🌐 Cross-platform support (Windows/Linux/macOS)
- ⚙️ Configurable upstream DNS servers via environment variables or command line parameters
- 🚀 High performance using FastMCP framework
- 📦 Dependency management with uv

## Installation

### Using uv (Recommended)

```bash
uv sync
```

### Using pip

```bash
pip install -r requirements.txt
```

## Usage

### 1. Using System Default DNS Servers

Using uv:
```bash
uv run dns-mcp
```

Using Python:
```bash
python -m dns_mcp.server
```

### 2. Specifying DNS Servers via Command Line

Using uv:
```bash
uv run dns-mcp --dns-servers 8.8.8.8 1.1.1.1
```

Using Python:
```bash
python -m dns_mcp.server --dns-servers 8.8.8.8 1.1.1.1
```

### 3. Specifying DNS Servers via Environment Variables

```bash
# Windows
set DNS_MCP_SERVERS=8.8.8.8,1.1.1.1

# Linux/macOS
export DNS_MCP_SERVERS=8.8.8.8,1.1.1.1
```

Then run:
```bash
# Using uv
uv run dns-mcp

# Using Python
python -m dns_mcp.server
```

## MCP Tools

### dns_query

Query DNS records for a specified hostname.

### Install
```
"mcpServers": {
    "dns-mcp": {
      "command": "uv",
      "args": [
        "--directory", "PATH_TO_SOURCES",
        "run", "dns-mcp"
      ]
    }
}
```

#### Parameters

- `host` (required): The hostname to query (e.g., 'example.com')
- `type` (optional): DNS record type, defaults to 'A'

#### Supported Record Types

- **A**: IPv4 address records
- **AAAA**: IPv6 address records
- **MX**: Mail exchange records
- **CNAME**: Canonical name records
- **TXT**: Text records
- **NS**: Name server records
- **SOA**: Start of authority records

#### Response Format

```json
{
  "host": "example.com",
  "type": "A",
  "success": true,
  "records": ["93.184.216.34"],
  "ttl": 86400,
  "upstream_servers": ["8.8.8.8", "8.8.4.4"]
}
```

#### Usage Examples

```python
# Query A record
result = await dns_query("example.com")

# Query MX record
result = await dns_query("example.com", "MX")

# Query TXT record
result = await dns_query("example.com", "TXT")
```

## Configuration Options

### Environment Variables

- `DNS_MCP_SERVERS`: Comma-separated list of upstream DNS servers

### Command Line Arguments

- `--dns-servers`: Specify upstream DNS servers (space-separated)
- `--port`: Specify MCP server port (default: 3000)

## System DNS Server Detection

The server automatically detects system DNS configuration:

- **Windows**: Uses `nslookup` command to get system DNS settings
- **Linux**: Reads `/etc/resolv.conf` file
- **macOS**: Uses `scutil --dns` and `networksetup` commands to detect DNS servers
- **Fallback**: If system settings cannot be detected, falls back to Google Public DNS (8.8.8.8, 8.8.4.4)

## Development

### Install Development Dependencies

```bash
uv sync --dev
```

## License

MIT License

## Example Client

Here's a simple client example demonstrating how to use this DNS MCP server:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "dns-mcp"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            
            # Query A record
            result = await session.call_tool("dns_query", {
                "host": "example.com",
                "type": "A"
            })
            print(f"A record: {result}")
            
            # Query MX record
            result = await session.call_tool("dns_query", {
                "host": "example.com", 
                "type": "MX"
            })
            print(f"MX record: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing

Pull requests and issue reports are welcome!
