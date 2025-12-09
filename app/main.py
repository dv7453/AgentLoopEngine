from fastapi import FastAPI

from app.api.routes import router as api_router
# Ensure workflow nodes & conditions are registered at startup
import app.workflows.code_review  # noqa: F401

app = FastAPI(title="Workflow Engine API", version="0.1.0")

# Mount API routes
app.include_router(api_router, prefix="/graph")


@app.get("/")
async def root() -> dict:
    """Root health endpoint."""
    return {"status": "ok", "service": "workflow-engine"}
