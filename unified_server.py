"""
통합 MCP Server - Host 기반 커넥터 분리
포트: 8765 / 단일 서버로 Host별 도구 필터링

hostname으로 도구 분리:
- pc.jmshinhwa.org → Filesystem 도구만
- pc-cmd.jmshinhwa.org → Commander 도구만

API Key: URL 쿼리 파라미터로 검증 (?key=xxx)
"""
import os
import sys

# 현재 디렉토리를 path에 추가 (connectors 임포트용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

# 커넥터 임포트
from connectors import filesystem, commander

# ==================== 설정 ====================
API_KEY = "yoojin-secret-2026-xyz789"
HOST_FILESYSTEM = "pc.jmshinhwa.org"
HOST_COMMANDER = "pc-cmd.jmshinhwa.org"

# ==================== MCP 서버 생성 ====================
mcp = FastMCP(name="PC-Remote-Unified", stateless_http=True, json_response=True)

# ==================== 커넥터 도구 등록 ====================
filesystem.register_tools(mcp)
commander.register_tools(mcp)

# ==================== Host 기반 도구 필터링 미들웨어 ====================
class HostFilterMiddleware(Middleware):
    """Host 헤더에 따라 tools/list 응답을 필터링"""
    
    async def on_list_tools(self, context: MiddlewareContext, call_next):
        # 전체 도구 목록 가져오기
        tools = await call_next(context)
        
        # HTTP 헤더에서 Host 확인
        try:
            headers = get_http_headers(include_all=True)
            host = headers.get("host", "").lower()
        except:
            # 헤더 접근 실패시 전체 반환
            return tools
        
        # Host에 따라 필터링
        if HOST_FILESYSTEM in host:
            # Filesystem 도구만
            filtered = [t for t in tools if t.name in filesystem.TOOLS]
            print(f"[Filter] {host} → Filesystem ({len(filtered)} tools)")
            return filtered
        
        elif HOST_COMMANDER in host:
            # Commander 도구만
            filtered = [t for t in tools if t.name in commander.TOOLS]
            print(f"[Filter] {host} → Commander ({len(filtered)} tools)")
            return filtered
        
        # 알 수 없는 Host는 전체 반환
        print(f"[Filter] {host} → All ({len(tools)} tools)")
        return tools

# 미들웨어 등록
mcp.add_middleware(HostFilterMiddleware())

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
    print(f"URL: http://127.0.0.1:8765/mcp")
    print(f"API Key: {API_KEY}")
    print(f"")
    print(f"Host Routing:")
    print(f"  {HOST_FILESYSTEM} → Filesystem ({len(filesystem.TOOLS)} tools)")
    print(f"  {HOST_COMMANDER} → Commander ({len(commander.TOOLS)} tools)")
    print("="*60 + "\n")
    
    app = mcp.streamable_http_app()
    app.add_middleware(APIKeyMiddleware)
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
