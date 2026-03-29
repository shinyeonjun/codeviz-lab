from fastapi import APIRouter

from app.modules.auth.presentation.http.router import router as auth_router
from app.modules.exams.presentation.http.router import router as exams_router
from app.modules.examples.presentation.http.router import router as examples_router
from app.modules.executions.presentation.http.router import router as executions_router
from app.modules.health.presentation.http.router import router as health_router
from app.modules.learning.presentation.http.router import router as learning_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(examples_router, prefix="/examples", tags=["examples"])
api_router.include_router(executions_router, prefix="/executions", tags=["executions"])
api_router.include_router(learning_router, prefix="/learning", tags=["learning"])
api_router.include_router(exams_router, prefix="/exams", tags=["exams"])
