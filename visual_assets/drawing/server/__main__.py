import sys

from visual_assets.drawing.server import mcp
from visual_assets.store import config as store_config

if __name__ == "__main__":
    # stdout carries the MCP protocol, so the root goes to stderr: a wrong root is visible in the client's server log
    print(f"visual_assets store root: {store_config.describe_root()}", file=sys.stderr, flush=True)
    mcp.run()
