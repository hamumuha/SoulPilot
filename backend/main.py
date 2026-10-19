from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import agent, chat, context, conversation, mcp, setting, template, user
from config.settings import API_HOST, API_PORT, CORS_ORIGINS
from db.session import SessionLocal
from services.privacy import migrate_sensitive_data

app = FastAPI(title="Hamu Pet API", version="3.0.0")


@app.on_event("startup")
def migrate_sensitive_records():
    db = SessionLocal()
    try:
        migrate_sensitive_data(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由模块（api/v1 路由层）
for router_module in (user, setting, chat, agent, context, template, conversation, mcp):
    app.include_router(router_module.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=True)
