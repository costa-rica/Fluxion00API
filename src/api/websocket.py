"""
WebSocket handler for Fluxion00API chat interface.

This module provides WebSocket endpoint management for real-time chat
with the agent system.
"""

import json
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from src.agent import Agent
from src.utils import logger


class ConnectionManager:
    """
    Manages WebSocket connections for the chat interface.

    Handles multiple concurrent WebSocket connections and message broadcasting.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, Agent] = {}
        self.users: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, agent: Agent, user: Dict[str, Any]):
        """
        Accept a new WebSocket connection with authenticated user.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
            agent: Agent instance for this connection
            user: Authenticated user data from JWT
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.agents[client_id] = agent
        self.users[client_id] = user

    def disconnect(self, client_id: str):
        """
        Remove a WebSocket connection.

        Args:
            client_id: Client identifier to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.agents:
            del self.agents[client_id]
        if client_id in self.users:
            del self.users[client_id]

    async def send_message(self, client_id: str, message: Dict):
        """
        Send a message to a specific client.

        Args:
            client_id: Client identifier
            message: Message dictionary to send
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    async def send_text(self, client_id: str, text: str):
        """
        Send plain text to a specific client.

        Args:
            client_id: Client identifier
            text: Text message to send
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(text)

    def get_agent(self, client_id: str) -> Agent:
        """
        Get the agent for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Agent: Agent instance for the client
        """
        return self.agents.get(client_id)

    def get_user(self, client_id: str) -> Dict[str, Any]:
        """
        Get the authenticated user for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Dict: User data from JWT authentication
        """
        return self.users.get(client_id)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)


async def handle_chat_message(
    websocket: WebSocket,
    client_id: str,
    manager: ConnectionManager,
    message: Dict
):
    """
    Handle incoming chat messages from clients.

    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        manager: Connection manager
        message: Parsed message dictionary
    """
    message_type = message.get("type")
    content = message.get("content", "")
    mode = message.get("mode", "auto")  # Get mode from message payload

    agent = manager.get_agent(client_id)
    if not agent:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "Agent not initialized"
        })
        return

    # Get user context for logging
    user = manager.get_user(client_id)
    username = user.get('username', 'Unknown') if user else 'Unknown'

    if message_type == "user_message":
        # Check for /sql command prefix
        use_sql_mode = False
        sql_query = content

        if content.strip().startswith('/sql'):
            use_sql_mode = True
            sql_query = content.strip()[4:].strip()  # Remove '/sql ' prefix
            logger.info(f"[AGENT] {username} (client_id: {client_id}) | SQL mode triggered by /sql prefix")
        elif mode == "sql":
            use_sql_mode = True
            logger.info(f"[AGENT] {username} (client_id: {client_id}) | SQL mode triggered by mode=sql")

        # Log user message
        from src.utils import truncate_text
        mode_indicator = "[SQL MODE] " if use_sql_mode else ""
        logger.info(f"[AGENT] {mode_indicator}{username} (client_id: {client_id}) | Message: \"{truncate_text(sql_query if use_sql_mode else content)}\"")

        # Send acknowledgment
        await manager.send_message(client_id, {
            "type": "user_echo",
            "content": content
        })

        # Send typing indicator
        await manager.send_message(client_id, {
            "type": "typing",
            "content": True
        })

        try:
            # Process message with agent (direct SQL or normal mode)
            if use_sql_mode:
                response = await agent.process_sql_query(sql_query)
            else:
                response = await agent.process_message(content)

            # Log agent response
            logger.info(f"[AGENT] {username} (client_id: {client_id}) | Response sent | Length: {len(response)} chars")

            # Send agent response
            await manager.send_message(client_id, {
                "type": "agent_message",
                "content": response
            })

        except Exception as e:
            # Send error message
            logger.error(f"[AGENT] {username} (client_id: {client_id}) | Error: {str(e)}")
            await manager.send_message(client_id, {
                "type": "error",
                "content": f"Error processing message: {str(e)}"
            })

        finally:
            # Stop typing indicator
            await manager.send_message(client_id, {
                "type": "typing",
                "content": False
            })

    elif message_type == "clear_history":
        # Clear conversation history
        agent.clear_history()
        await manager.send_message(client_id, {
            "type": "system",
            "content": "Conversation history cleared"
        })

    elif message_type == "ping":
        # Respond to ping
        await manager.send_message(client_id, {
            "type": "pong"
        })


async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    manager: ConnectionManager,
    agent: Agent,
    user: Dict[str, Any]
):
    """
    WebSocket endpoint handler with authenticated user.

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        manager: Connection manager
        agent: Agent instance for this connection
        user: Authenticated user data from JWT
    """
    await manager.connect(websocket, client_id, agent, user)

    # Log connection
    username = user.get('username', 'User')
    user_id = user.get('id', 'Unknown')
    logger.info(f"[WEBSOCKET] User connected: {username} (ID: {user_id}, client_id: {client_id})")

    try:
        # Send welcome message with username
        await manager.send_message(client_id, {
            "type": "system",
            "content": f"Welcome {username}! Connected to Fluxion00API. How can I help you today?"
        })

        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                await handle_chat_message(websocket, client_id, manager, message)
            except json.JSONDecodeError:
                await manager.send_message(client_id, {
                    "type": "error",
                    "content": "Invalid message format"
                })

    except WebSocketDisconnect:
        logger.info(f"[WEBSOCKET] User disconnected: {username} (client_id: {client_id})")
        manager.disconnect(client_id)

    except Exception as e:
        logger.error(f"[WEBSOCKET] Connection error for {username} (client_id: {client_id}): {e}")
        manager.disconnect(client_id)
