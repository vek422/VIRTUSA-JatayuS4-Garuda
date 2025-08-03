from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db
from app.websocket.handler import websocket_handler

router = APIRouter()


@router.websocket("/ws/assessment")
async def websocket_assessment_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(
        None, description="JWT token for authentication"),
    test_id: Optional[int] = Query(None, description="Test ID for assessment"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for AI-powered assessment chatbot

    Query Parameters:
    - token: JWT token for user authentication (required)
    - test_id: ID of the test for assessment (optional, can be provided later)

    Message Types:
    - auth: Authenticate connection
    - start_assessment: Begin assessment for a test
    - get_question: Request next question
    - submit_answer: Submit answer for current question
    - chat_message: Send chat message to AI
    - heartbeat: Keep connection alive

    Example connection:
    ws://localhost:8000/ws/assessment?token=YOUR_JWT_TOKEN&test_id=123
    """
    print("WebSocket connection established for assessment")
    await websocket_handler.handle_connection(websocket, token, test_id, db)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(
        None, description="JWT token for authentication"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for general chat functionality

    This endpoint provides a general chat interface without assessment context.
    Useful for candidate support, FAQ, or general inquiries.

    Query Parameters:
    - token: JWT token for user authentication (required)

    Example connection:
    ws://localhost:8000/ws/chat?token=YOUR_JWT_TOKEN
    """
    print("WebSocket connection established for chat")
    await websocket_handler.handle_connection(websocket, token, None, db)
