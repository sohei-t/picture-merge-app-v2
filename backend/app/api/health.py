"""Health check endpoint."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services.segmentation import is_rembg_loaded

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check server health and rembg model status."""
    return HealthResponse(
        status="ok",
        rembg_loaded=is_rembg_loaded(),
        version="2.0.0",
    )
