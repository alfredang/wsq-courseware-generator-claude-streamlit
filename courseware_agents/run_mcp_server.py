#!/usr/bin/env python
"""
MCP Tools Server Entry Point

Run this script to start the MCP server that exposes courseware tools
to the Claude Agent SDK.

Usage:
    python run_mcp_server.py

Author: Courseware Generator Team
Date: 26 January 2026
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from courseware_agents.mcp_tools_server import main

if __name__ == "__main__":
    asyncio.run(main())
