from .health_routers import router as health_router
from .auth_routers import router as auth_router
from .resume_routers import router as resume_router

__all__ = ["health_router", "auth_router", "resume_router"]
