"""CodeBot FastAPI application entrypoint."""

from fastapi import FastAPI

app = FastAPI(
    title="CodeBot",
    description="Multi-agent autonomous software development platform",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
