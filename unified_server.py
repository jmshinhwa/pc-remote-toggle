"""
통합 MCP Server - 모든 도구 제공
포트: 8765 / Filesystem + Commander 도구 모두 제공

API Key: URL 쿼리 파라미터로 검증 (?key=xxx)
"""
import os
import sys

# 현재 디렉토리를 path에 추가 (connectors 임포트용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

# 설정 임포트
from config import API_KEY, TUNNEL_PORT

# 커넥터 임포트
from connectors import filesystem, commander

# ==================== MCP 서버 생성 ====================
mcp = FastMCP(name="PC-Remote-Unified", stateless_http=True, json_response=True)

# ==================== 커넥터 도구 등록 ====================
filesystem.register_tools(mcp)
commander.register_tools(mcp)

# ==================== API Key 미들웨어 ====================
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # MCP 엔드포인트만 체크
        if "/mcp" in request.url.path:
            key = request.query_params.get("key", "")
            if key != API_KEY:
                return JSONResponse({"error": "Invalid API Key"}, status_code=401)
        return await call_next(request)

# ==================== 서버 실행 ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("[PC-Remote] Unified MCP Server Starting...")
    print("="*60)
    print(f"URL: http://127.0.0.1:{TUNNEL_PORT}/mcp")
    # Mask API key for security (show last 4 chars only)
    masked_key = f"{'*' * max(0, len(API_KEY) - 4)}{API_KEY[-4:]}" if len(API_KEY) >= 4 else "***"
    print(f"API Key: {masked_key}")
    print(f"")
    print(f"Available Tools:")
    print(f"  Filesystem: {len(filesystem.TOOLS)} tools")
    print(f"  Commander: {len(commander.TOOLS)} tools")
    print(f"  Total: {len(filesystem.TOOLS) + len(commander.TOOLS)} tools")
    print("="*60 + "\n")
    
    app = mcp.streamable_http_app()
    app.add_middleware(APIKeyMiddleware)
    uvicorn.run(app, host="127.0.0.1", port=TUNNEL_PORT, log_level="warning")
