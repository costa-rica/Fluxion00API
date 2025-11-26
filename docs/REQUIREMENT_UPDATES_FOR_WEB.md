# REQUIREMENT_UPDATES_FOR_WEB.md

## Overview

This file contains the details of the new reuqirements needed to facilitate the web interface porject called Fluxion00Web.

### Login and authentication

The Fluxion00Web will have a login page. We need to have a login route that uses the same codeing and decoding method as the News Nexus API (NN API), which is an ExperssJS app written in TypeScript. The NN API uses `const jwt = require("jsonwebtoken");` and specifically `const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET);` to create a token.

### Chat status-log feature

The Fluxion00Web will have a chat status-log feature. This feature will allow the users to see the agent's progress in real-time. For starters this will share the information as to when it makes a call to the llm, what agents are being used, and what tools are being used. When the call to the llm is made we want to have a count of characters in the prompt and the response. We want a count of characters in the output of the agent and tools if there is any.
