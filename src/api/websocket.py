"""
WebSocket handler for Fluxion00API chat interface.

This module provides WebSocket endpoint management for real-time chat
with the agent system.
"""

import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from src.agent import Agent


class ConnectionManager:
    """
    Manages WebSocket connections for the chat interface.

    Handles multiple concurrent WebSocket connections and message broadcasting.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, Agent] = {}

    async def connect(self, websocket: WebSocket, client_id: str, agent: Agent):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
            agent: Agent instance for this connection
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.agents[client_id] = agent

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

    agent = manager.get_agent(client_id)
    if not agent:
        await manager.send_message(client_id, {
            "type": "error",
            "content": "Agent not initialized"
        })
        return

    if message_type == "user_message":
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
            # Process message with agent
            response = await agent.process_message(content)

            # Send agent response
            await manager.send_message(client_id, {
                "type": "agent_message",
                "content": response
            })

        except Exception as e:
            # Send error message
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
    agent: Agent
):
    """
    WebSocket endpoint handler.

    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        manager: Connection manager
        agent: Agent instance for this connection
    """
    await manager.connect(websocket, client_id, agent)

    try:
        # Send welcome message
        await manager.send_message(client_id, {
            "type": "system",
            "content": "Connected to Fluxion00API. How can I help you today?"
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
        manager.disconnect(client_id)
        print(f"Client {client_id} disconnected")

    except Exception as e:
        print(f"Error in WebSocket connection for {client_id}: {e}")
        manager.disconnect(client_id)
