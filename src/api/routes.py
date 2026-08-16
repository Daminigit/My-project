"""
API Route Definitions.

Defines all REST API endpoints for the recommendation system.
Will be implemented in Phase 5.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# TODO (Phase 5): Implement the following endpoints
# GET  /cuisines   — List available cuisines
# GET  /locations  — List available locations
# POST /recommend  — Get AI-powered recommendations
