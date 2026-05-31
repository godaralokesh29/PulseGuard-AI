"""WebSocket endpoints for real-time incident streaming."""

import asyncio
import uuid
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from backend.services.notification import get_notification_service
from backend.utils.logging import get_logger

logger = get_logger("websocket")
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/incidents")
async def websocket_incidents(websocket: WebSocket):
    """
    WebSocket endpoint for real-time incident/decision streaming.
    
    Clients connect and receive live updates on:
    - Decision generation
    - Anomaly detection
    - System events
    
    Usage:
        ws://localhost:8000/ws/incidents
    
    Message Format:
        {
            "type": "decision" | "anomaly" | "ping",
            "data": {...}
        }
    """
    client_id = f"ws_{uuid.uuid4()}"
    
    await websocket.accept()
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Get notification service
        notification_service = get_notification_service()
        
        # Register client
        message_queue = await notification_service.ws_manager.connect(client_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to incident stream",
            "server_time": str(uuid.uuid4())}
        )
        
        # Receive and handle messages
        while True:
            # Create task to receive from WebSocket
            receive_task = asyncio.create_task(websocket.receive_text())
            
            # Create task to receive from message queue
            queue_task = asyncio.create_task(message_queue.get())
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [receive_task, queue_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check which task completed
            if receive_task in done:
                # Received message from client
                try:
                    data = await receive_task
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        # Respond to ping
                        await websocket.send_json({"type": "pong"})
                    elif message.get("type") == "subscribe":
                        # Subscribe to tenant-specific updates
                        tenant_id = message.get("tenant_id")
                        logger.info(f"Client {client_id} subscribed to tenant: {tenant_id}")
                    
                except WebSocketDisconnect:
                    raise
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client {client_id}")
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
            
            else:
                # Received message from queue
                try:
                    message = await queue_task
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending queued message: {e}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
        await notification_service.ws_manager.disconnect(client_id, message_queue)
    
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    WebSocket endpoint for dashboard real-time updates.
    
    Sends aggregated metrics and system status.
    
    Usage:
        ws://localhost:8000/ws/dashboard
    """
    client_id = f"dashboard_{uuid.uuid4()}"
    
    await websocket.accept()
    logger.info(f"Dashboard client connected: {client_id}")
    
    try:
        notification_service = get_notification_service()
        message_queue = await notification_service.ws_manager.connect(client_id)
        
        # Send initial system status
        await websocket.send_json({
            "type": "system_status",
            "connected_clients": notification_service.ws_manager.get_active_clients(),
            "timestamp": str(uuid.uuid4())
        })
        
        while True:
            try:
                # Receive from queue with timeout
                message = await asyncio.wait_for(message_queue.get(), timeout=60.0)
                await websocket.send_text(message)
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "connected_clients": notification_service.ws_manager.get_active_clients()
                })
    
    except WebSocketDisconnect:
        logger.info(f"Dashboard client disconnected: {client_id}")
        await notification_service.ws_manager.disconnect(client_id, message_queue)
    
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass


@router.get("/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    notification_service = get_notification_service()
    ws_manager = notification_service.ws_manager
    
    return {
        "active_connections": ws_manager.get_active_clients(),
        "client_ids": ws_manager.get_client_list(),
        "slack_enabled": notification_service.slack_notifier.enabled,
        "timestamp": str(uuid.uuid4())
    }
