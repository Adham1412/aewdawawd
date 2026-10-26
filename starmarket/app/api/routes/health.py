from fastapi import APIRouter
router = APIRouter(tags=["health"])

@router.get("/health", summary="Service health")
async def health():
    return {"status": "ok", "service": "starmarket-api"}
