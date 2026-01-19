"""
통합 MCP Server - 단순화 버전
포트: 8765 / 모든 도구 노출

Claude.ai 웹에서 등록:
- pc.jmshinhwa.org/mcp?key=yoojin-secret-2026-xyz789
- pc-cmd.jmshinhwa.org/mcp?key=yoojin-secret-2026-xyz789

API Key: URL 쿼리 파라미터로 검증 (?key=xxx)
"""
import os
import sys

# 현재 디렉토리를 path에 추가 (connectors 임포트용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP
import uvicorn

# 커넥터 임포트
from connectors import filesystem, commander

# ==================== 설정 ====================
API_KEY = "yoojin-secret-2026-xyz789"
PORT = 8765

# ==================== MCP 서버 생성 ====================
mcp = FastMCP(name="PC-Remote")

# ==================== 커넥터 도구 등록 ====================
filesystem.register_tools(mcp)
commander.register_tools(mcp)

# ==================== 서버 실행 ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("[PC-Remote] MCP Server Starting...")
    print("="*60)
    print(f"Local: http://127.0.0.1:{PORT}/mcp")
    print(f"")
    print(f"External (via Cloudflare Tunnel):")
    print(f"  https://pc.jmshinhwa.org/mcp?key={API_KEY}")
    print(f"  https://pc-cmd.jmshinhwa.org/mcp?key={API_KEY}")
    print(f"")
    print(f"Tools: {len(filesystem.TOOLS) + len(commander.TOOLS)} total")
    print(f"  - Filesystem: {len(filesystem.TOOLS)}")
    print(f"  - Commander: {len(commander.TOOLS)}")
    print("="*60 + "\n")
    
    mcp.run(transport="streamable-http", host="127.0.0.1", port=PORT)
