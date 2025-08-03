from fastapi import APIRouter
from app.controllers import auth_controller
from app.controllers import test_controller
from app.controllers import candidate_application_controller
from app.controllers import dashboard_controller
from app.controllers import assessment_controller
from app.controllers import websocket_controller
from app.controllers import log_controller


router = APIRouter()


router.include_router(auth_controller.router, prefix="/auth")
router.include_router(test_controller.router, prefix="/tests")
router.include_router(candidate_application_controller.router,prefix="/candidate-applications")
router.include_router(dashboard_controller.router, prefix="")
router.include_router(websocket_controller.router, tags=["WebSocket"])
router.include_router(assessment_controller.router, prefix="/tests")
router.include_router(log_controller.router, prefix="/logs")

