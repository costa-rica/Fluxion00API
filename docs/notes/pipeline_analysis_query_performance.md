# Pipeline Analysis: Query Performance Bottleneck

## Overview

This document analyzes why "How many articles have been approved?" succeeds in ~30 seconds while "How many articles has user 2 approved?" fails after 2+ minutes with an error.

## Message Processing Pipeline

All user messages follow this flow:

```
User Input → WebSocket → handle_chat_message() → Agent.process_message()
  ↓
[1] First LLM Call: Decide which tool to use
  ↓
[2] Tool Execution: Query database
  ↓
[3] Second LLM Call: Format results for user
  ↓
Response → WebSocket → User
```

## Case 1: "How many articles have been approved?" ✅ (~30 seconds)

### Step-by-Step Flow

1. **First LLM Call** (~10-15s)
   - Input: System prompt + user message
   - LLM decision: Use `count_approved_articles` tool
   - Output: `TOOL_CALL: count_approved_articles` with `is_approved=True`

2. **Tool Execution** (<1s)
   - Function: `get_approved_articles_count(is_approved=True)`
   - SQL: `SELECT COUNT(*) FROM ArticleApproveds WHERE isApproved = 1`
   - Result: `3743` (single integer)

3. **Second LLM Call** (~10-15s)
   - Input: Tool result `"3743"`
   - Processing: Minimal data, fast completion
   - Output: "The number of approved articles is 3743."

### Why It Works

- Simple tool selection (count vs list)
- Minimal database result (single integer)
- Small data payload to second LLM call
- Fast LLM processing on simple data

## Case 2: "How many articles has user 2 approved?" ❌ (>120 seconds, timeout)

### Step-by-Step Flow

1. **First LLM Call** (~15-25s)
   - Input: System prompt + user message
   - Problem: Ambiguous - user wants COUNT but tool returns LIST
   - LLM decision: Use `get_articles_by_user` tool (only available option)
   - Output: `TOOL_CALL: get_articles_by_user` with `user_id=2, is_approved=True`

2. **Tool Execution** (~5-10s)
   - Function: `get_approved_articles_by_user(user_id=2, is_approved=True, limit=100)`
   - SQL: Returns ALL fields for up to 100 articles:
     ```sql
     SELECT id, userId, articleId, isApproved,
            headlineForPdfReport, publicationNameForPdfReport,
            publicationDateForPdfReport, textForPdfReport,
            urlForPdfReport, kmNotes, createdAt, updatedAt
     FROM ArticleApproveds
     WHERE userId = 2 AND isApproved = 1
     ORDER BY createdAt DESC
     LIMIT 100
     ```
   - Result: Array of up to 100 article objects with `textForPdfReport` (potentially very long)
   - Data size: Potentially 100s of KB

3. **Second LLM Call** (>120s → **TIMEOUT** ⚠️)
   - Input: Massive formatted article list
   - Processing: LLM tries to process hundreds of KB of article data
   - Problem: Processing exceeds 120-second timeout (`src/llm/ollama_client.py:26`)
   - Exception: `httpx.ReadTimeout` or similar
   - Caught at: `src/api/websocket.py:146-151`
   - Error message: "Error processing message:" (exception string may be empty/truncated)

### Why It Fails

1. **Tool Mismatch**: User wants a COUNT, but only LIST tool exists for user queries
2. **Excessive Data Transfer**: Returns 100 full articles instead of a count
3. **LLM Context Overload**: Second LLM call receives hundreds of KB of text
4. **Timeout**: 120-second timeout in `OllamaProvider.__init__()` is exceeded
5. **Poor Error Message**: Exception caught but string representation is minimal

## Root Cause

**Primary Issue**: The second LLM call times out when processing excessive article data.

**Contributing Factors**:
- No `count_articles_by_user` tool available (forces use of list tool)
- `get_articles_by_user` returns full article objects with potentially massive `textForPdfReport` fields
- Default limit of 100 articles creates very large payload
- 120-second timeout (`src/llm/ollama_client.py:26`) is insufficient for large context processing
- Remote Ollama instance may have additional latency

## Location References

- Timeout configuration: `src/llm/ollama_client.py:26`
- Error handling: `src/api/websocket.py:146-151`
- Tool execution: `src/agent/agent.py:144-147`
- Second LLM call: `src/agent/agent.py:177`
- Query function: `src/queries/queries_approved_articles.py:118-171`

## Potential Solutions

1. **Add specialized count tool**: Create `count_articles_by_user(user_id, is_approved)` that returns just an integer
2. **Increase timeout**: Raise timeout beyond 120s (not ideal, addresses symptom not cause)
3. **Reduce data payload**: Modify `get_articles_by_user` to exclude `textForPdfReport` when only count is needed
4. **Improve LLM prompt**: Better instruct LLM to request count vs list operations
5. **Add result summarization**: Pre-process tool results before sending to LLM
