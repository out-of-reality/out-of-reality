from fastapi import APIRouter
from .users import router as users_router
from .videos import router as videos_router
from .levels import router as levels_router

router = APIRouter()
router.include_router(users_router)
router.include_router(videos_router)
router.include_router(levels_router)
