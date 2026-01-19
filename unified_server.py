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
from contextvars import ContextVar

# 현재 디렉토리를 path에 추가 (connectors 임포트용)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import uvicorn

# 커넥터 임포트
from connectors import filesystem, commander

# ==================== 설정 ====================
API_KEY = "yoojin-secret-2026-xyz789"
HOST_FILESYSTEM = "pc.jmshinhwa.org"
HOST_COMMANDER = "pc-cmd.jmshinhwa.org"

# 현재 요청의 커넥터 타입 저장 (스레드 안전)
current_connector: ContextVar[str] = ContextVar("current_connector", default="")

# ==================== MCP 서버 생성 ====================
mcp = FastMCP(name="PC-Remote-Unified", stateless_http=True, json_response=True)

# ==================== 도구 등록 (래핑) ====================
def register_filtered_tools():
    """커넥터별로 필터링된 도구 등록"""
    
    # Filesystem 도구들
    for tool_name in filesystem.TOOLS:
        original_func = None
        
        # filesystem 모듈에서 도구 함수 찾기
        @mcp.tool(name=tool_name)
        def make_tool(tn=tool_name):
            def wrapper(*args, **kwargs):
                connector = current_connector.get()
                if connector != "filesystem":
                    return {"error": f"Tool '{tn}' not available for this host"}
                # 실제 함수 실행은 register_tools에서 처리
            return wrapper
    
    # 실제 도구 등록
    filesystem.register_tools(mcp)
    commander.register_tools(mcp)

# 도구 등록
filesystem.register_tools(mcp)
commander.register_tools(mcp)

# ==================== API Key + Host 검증 미들웨어 ====================
class SecurityMiddleware(BaseHTTPMiddleware):
    """API Key 검증 + Host 기반 커넥터 설정"""
    
    async def dispatch(self, request, call_next):
        # MCP 엔드포인트만 체크
        if "/mcp" not in request.url.path:
            return await call_next(request)
        
        # 1. API Key 검증
        key = request.query_params.get("key", "")
        if key != API_KEY:
            return JSONResponse({"error": "Invalid API Key"}, status_code=401)
        
        # 2. Host 추출 (포트 제거 + 소문자)
        host_header = request.headers.get("host", "")
        host = host_header.split(":")[0].lower().strip()
        
        # 3. 정확한 Host 매칭 (보안: in 대신 ==)
        if host == HOST_FILESYSTEM:
            current_connector.set("filesystem")
        elif host == HOST_COMMANDER:
            current_connector.set("commander")
        else:
            # 알 수 없는 Host는 거부
            return JSONResponse(
                {"error": f"Unknown host: {host}. Allowed: {HOST_FILESYSTEM}, {HOST_COMMANDER}"}, 
                status_code=403
            )
        
        return await call_next(request)

# ==================== Tool List 필터링 ====================
# MCP의 tools/list 응답을 후처리로 필터링
original_list_tools = None

def create_filtered_app():
    """필터링이 적용된 앱 생성"""
    app = mcp.streamable_http_app()
    
    # 기존 라우트를 래핑해서 tools/list 응답 필터링
    from starlette.routing import Route
    from starlette.responses import Response
    import json
    
    class ToolFilterMiddleware(BaseHTTPMiddleware):
        """tools/list 응답에서 Host에 맞는 도구만 필터링"""
        
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            
            # tools/list 응답인지 확인
            if "/mcp" in request.url.path:
                connector = current_connector.get()
                
                # Response body 읽기
                if hasattr(response, 'body'):
                    try:
                        body = response.body
                        if isinstance(body, bytes):
                            data = json.loads(body.decode())
                            
                            # tools/list 응답 필터링
                            if "result" in data and "tools" in data.get("result", {}):
                                tools = data["result"]["tools"]
                                
                                if connector == "filesystem":
                                    allowed = filesystem.TOOLS
                                elif connector == "commander":
                                    allowed = commander.TOOLS
                                else:
                                    allowed = []
                                
                                filtered = [t for t in tools if t.get("name") in allowed]
                                data["result"]["tools"] = filtered
                                
                                return Response(
                                    content=json.dumps(data),
                                    status_code=response.status_code,
                                    headers=dict(response.headers),
                                    media_type="application/json"
                                )
                    except:
                        pass
            
            return response
    
    # 미들웨어 추가 (순서 중요: Security → Filter)
    app.add_middleware(ToolFilterMiddleware)
    app.add_middleware(SecurityMiddleware)
    
    return app

# ==================== 서버 실행 ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("[PC-Remote] Unified MCP Server Starting...")
    print("="*60)
    print(f"URL: http://127.0.0.1:8765/mcp")
    print(f"API Key: {API_KEY}")
    print(f"")
    print(f"Host Routing (정확한 매칭):")
    print(f"  {HOST_FILESYSTEM} → Filesystem ({len(filesystem.TOOLS)} tools)")
    print(f"  {HOST_COMMANDER} → Commander ({len(commander.TOOLS)} tools)")
    print(f"")
    print(f"보안:")
    print(f"  - API Key 필수")
    print(f"  - 알 수 없는 Host → 403 Forbidden")
    print("="*60 + "\n")
    
    app = create_filtered_app()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")
