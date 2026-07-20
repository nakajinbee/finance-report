from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import companies, edinet

app = FastAPI(title="企業財務データ API")

# フロントエンドはVite devサーバー（デフォルトポート5173）から接続する
# (docs/development/frontend_implementation_policy.md 参照)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(edinet.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
