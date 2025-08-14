"""DNS MCP Server implementation."""

import argparse
import asyncio
import os
import platform
import socket
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union

import dns.resolver
from fastmcp import FastMCP

# Create the FastMCP instance
mcp = FastMCP("DNS MCP Server")


def get_system_dns_servers() -> List[str]:
    """Get system DNS servers for cross-platform support."""
    system = platform.system().lower()
    
    if system == "windows":
        return _get_windows_dns_servers()
    elif system == "linux":
        return _get_linux_dns_servers()
    elif system == "darwin":  # macOS
        return _get_macos_dns_servers()
    else:
        # Fallback to common public DNS servers
        return ["8.8.8.8", "8.8.4.4"]


def _get_windows_dns_servers() -> List[str]:
    """Get DNS servers on Windows."""
    try:
        # Use nslookup to get current DNS servers
        result = subprocess.run(
            ["nslookup", "localhost"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        dns_servers = []
        for line in result.stdout.split('\n'):
            if 'Address:' in line:
                server = line.split(':')[-1].strip()
                if server and server != "localhost":
                    dns_servers.append(server)
        
        if dns_servers:
            return dns_servers
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Fallback to public DNS
    return ["8.8.8.8", "8.8.4.4"]


def _get_linux_dns_servers() -> List[str]:
    """Get DNS servers on Linux."""
    try:
        with open('/etc/resolv.conf', 'r') as f:
            dns_servers = []
            for line in f:
                line = line.strip()
                if line.startswith('nameserver'):
                    parts = line.split()
                    if len(parts) >= 2:
                        dns_servers.append(parts[1])
            
            if dns_servers:
                return dns_servers
    except (FileNotFoundError, PermissionError):
        pass
    
    # Fallback to public DNS
    return ["8.8.8.8", "8.8.4.4"]


def _get_macos_dns_servers() -> List[str]:
    """Get DNS servers on macOS."""
    try:
        # Try using scutil first (more reliable on macOS)
        result = subprocess.run(
            ["scutil", "--dns"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        dns_servers = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if 'nameserver[0]' in line or 'nameserver[1]' in line:
                # Extract IP address from lines like "nameserver[0] : 8.8.8.8"
                parts = line.split(':')
                if len(parts) >= 2:
                    server = parts[-1].strip()
                    if server and server not in dns_servers:
                        dns_servers.append(server)
        
        if dns_servers:
            return dns_servers
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        # Fallback to networksetup command
        result = subprocess.run(
            ["networksetup", "-getdnsservers", "Wi-Fi"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        dns_servers = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and line != "There aren't any DNS Servers set on Wi-Fi.":
                # Check if it's a valid IP address format
                parts = line.split('.')
                if len(parts) == 4 and all(part.isdigit() for part in parts):
                    dns_servers.append(line)
        
        if dns_servers:
            return dns_servers
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        # Also try Ethernet interface
        result = subprocess.run(
            ["networksetup", "-getdnsservers", "Ethernet"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        dns_servers = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line and line != "There aren't any DNS Servers set on Ethernet.":
                # Check if it's a valid IP address format
                parts = line.split('.')
                if len(parts) == 4 and all(part.isdigit() for part in parts):
                    dns_servers.append(line)
        
        if dns_servers:
            return dns_servers
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Fallback to reading /etc/resolv.conf on macOS
    try:
        with open('/etc/resolv.conf', 'r') as f:
            dns_servers = []
            for line in f:
                line = line.strip()
                if line.startswith('nameserver'):
                    parts = line.split()
                    if len(parts) >= 2:
                        dns_servers.append(parts[1])
            
            if dns_servers:
                return dns_servers
    except (FileNotFoundError, PermissionError):
        pass
    
    # Final fallback to public DNS
    return ["8.8.8.8", "8.8.4.4"]


class DNSQueryTool:
    """DNS query tool for MCP server."""
    
    def __init__(self, upstream_servers: Optional[List[str]] = None):
        """Initialize DNS query tool.
        
        Args:
            upstream_servers: List of upstream DNS servers to use.
                            If None, will use system default.
        """
        self.upstream_servers = upstream_servers or get_system_dns_servers()
        self._configure_resolver()
    
    def _configure_resolver(self):
        """Configure the DNS resolver with upstream servers."""
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = self.upstream_servers
        self.resolver.timeout = 10
        self.resolver.lifetime = 30
    
    async def query(self, host: str, record_type: str = 'A') -> Dict[str, Any]:
        """Query DNS record for a host.
        
        Args:
            host: The hostname to query
            record_type: The DNS record type (A, AAAA, MX, CNAME, TXT, NS, etc.)
        
        Returns:
            Dictionary containing query results
        """
        record_type = record_type.upper()
        
        try:
            # Perform DNS query in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._sync_query, 
                host, 
                record_type
            )
            return result
        except Exception as e:
            return {
                "host": host,
                "type": record_type,
                "success": False,
                "error": str(e),
                "records": []
            }
    
    def _sync_query(self, host: str, record_type: str) -> Dict[str, Any]:
        """Synchronous DNS query."""
        try:
            answer = self.resolver.resolve(host, record_type)
            
            records = []
            for rdata in answer:
                if record_type == 'A':
                    records.append(str(rdata))
                elif record_type == 'AAAA':
                    records.append(str(rdata))
                elif record_type == 'MX':
                    records.append({
                        "priority": rdata.preference,
                        "exchange": str(rdata.exchange)
                    })
                elif record_type == 'CNAME':
                    records.append(str(rdata.target))
                elif record_type == 'TXT':
                    records.append(' '.join([s.decode() if isinstance(s, bytes) else str(s) for s in rdata.strings]))
                elif record_type == 'NS':
                    records.append(str(rdata.target))
                elif record_type == 'SOA':
                    records.append({
                        "mname": str(rdata.mname),
                        "rname": str(rdata.rname),
                        "serial": rdata.serial,
                        "refresh": rdata.refresh,
                        "retry": rdata.retry,
                        "expire": rdata.expire,
                        "minimum": rdata.minimum
                    })
                else:
                    records.append(str(rdata))
            
            return {
                "host": host,
                "type": record_type,
                "success": True,
                "records": records,
                "ttl": answer.ttl,
                "upstream_servers": self.upstream_servers
            }
            
        except dns.resolver.NXDOMAIN:
            return {
                "host": host,
                "type": record_type,
                "success": False,
                "error": "Domain does not exist (NXDOMAIN)",
                "records": [],
                "upstream_servers": self.upstream_servers
            }
        except dns.resolver.NoAnswer:
            return {
                "host": host,
                "type": record_type,
                "success": False,
                "error": f"No {record_type} record found",
                "records": [],
                "upstream_servers": self.upstream_servers
            }
        except dns.resolver.Timeout:
            return {
                "host": host,
                "type": record_type,
                "success": False,
                "error": "DNS query timeout",
                "records": [],
                "upstream_servers": self.upstream_servers
            }


# Global DNS tool instance
dns_tool: Optional[DNSQueryTool] = None


@mcp.tool()
async def dns_query(host: str, type: str = "A") -> Dict[str, Any]:
    """Query DNS records for a hostname.
    
    Args:
        host: The hostname to query (e.g., 'example.com')
        type: The DNS record type to query (default: 'A'). 
              Supported types: A, AAAA, MX, CNAME, TXT, NS, SOA
    
    Returns:
        Dictionary containing query results with the following fields:
        - host: The queried hostname
        - type: The record type queried
        - success: Boolean indicating if query was successful
        - records: List of DNS records (format varies by type)
        - ttl: Time to live in seconds (if successful)
        - error: Error message (if not successful)
        - upstream_servers: List of DNS servers used
    """
    global dns_tool
    if dns_tool is None:
        raise RuntimeError("DNS tool not initialized")
    
    return await dns_tool.query(host, type)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="DNS MCP Server")
    parser.add_argument(
        "--dns-servers",
        nargs="*",
        help="Upstream DNS servers to use (space-separated). If not provided, uses system default."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run the MCP server on (default: 3000)"
    )
    
    return parser.parse_args()


def get_upstream_servers(args: argparse.Namespace) -> List[str]:
    """Get upstream DNS servers from environment variable or command line args."""
    # Priority: 1. Command line args, 2. Environment variable, 3. System default
    
    if args.dns_servers:
        return args.dns_servers
    
    env_servers = os.environ.get("DNS_MCP_SERVERS")
    if env_servers:
        return [s.strip() for s in env_servers.split(",") if s.strip()]
    
    return get_system_dns_servers()


def main():
    """Main entry point for the DNS MCP server."""
    global dns_tool
    
    args = parse_args()
    upstream_servers = get_upstream_servers(args)
    
    print(f"Starting DNS MCP Server...")
    print(f"Upstream DNS servers: {upstream_servers}")
    print(f"Platform: {platform.system()}")
    if platform.system().lower() == "darwin":
        print("macOS DNS detection using scutil and networksetup commands")
    
    # Initialize DNS tool
    dns_tool = DNSQueryTool(upstream_servers)
    
    # Run the server
    mcp.run(transport="stdio")


def cli_main():
    """CLI entry point."""
    main()


if __name__ == "__main__":
    cli_main()
