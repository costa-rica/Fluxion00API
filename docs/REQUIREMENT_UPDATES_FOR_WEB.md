# REQUIREMENT_UPDATES_FOR_WEB.md

## Overview

This file contains the details of the new reuqirements needed to facilitate the web interface porject called Fluxion00Web.

### Login and authentication

**Authentication Flow**:
1. Fluxion00Web handles login via News Nexus API (NN API)
2. NN API returns JWT token after successful authentication
3. Fluxion00API verifies and decodes tokens (does NOT create tokens or handle passwords)

**JWT Token Specification**:
- **Creation**: Handled by NN API (ExpressJS/TypeScript) using `jsonwebtoken` library
- **Algorithm**: HS256
- **Secret**: `JWT_SECRET` environment variable (shared between NN API and Fluxion00API)
- **Payload Structure**: `{ id: <user_id> }` (minimal, no expiration or other claims)
- **Verification**: Fluxion00API uses PyJWT library to decode and verify signature

**WebSocket Authentication**:
- **Endpoint**: `/ws/{client_id}?token=<jwt>`
- **Token Format**: JWT passed as query parameter
- **Middleware Requirements**:
  1. Extract token from query parameter
  2. Verify JWT signature using `JWT_SECRET`
  3. Decode payload to extract `user.id`
  4. Query Users table to verify user exists and is valid
  5. Reject connection if token invalid or user not found
  6. Attach user info to WebSocket connection context

**Endpoint Protection**:
- `/ws/{client_id}` - **Requires authentication** (JWT token mandatory)
- `/health` - **Public** (no authentication)
- `/api/info` - **Public** (no authentication)
- Future endpoints - Authentication requirements TBD

**No Backward Compatibility**: All WebSocket connections must provide valid JWT token. Previous unauthenticated access is removed.

### Chat status-log feature

The Fluxion00Web will have a chat status-log feature. This feature will allow the users to see the agent's progress in real-time. For starters this will share the information as to when it makes a call to the llm, what agents are being used, and what tools are being used. When the call to the llm is made we want to have a count of characters in the prompt and the response. We want a count of characters in the output of the agent and tools if there is any.
