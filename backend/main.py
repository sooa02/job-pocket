from fastapi import FastAPI

# router
from routers.health import router as health_check

app = FastAPI()

app.include_router(health_check)
