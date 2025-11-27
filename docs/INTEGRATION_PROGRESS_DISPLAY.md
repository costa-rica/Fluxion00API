# Agent Progress Display Integration Guide for Fluxion00Web

This guide explains how to implement real-time agent progress tracking in the Fluxion00Web NextJS frontend.

## Overview

Fluxion00API now sends real-time progress updates via WebSocket, showing exactly what the agent is doing as it processes user messages. This includes:
- Initial message analysis
- Tool selection and execution
- SQL query generation and execution
- LLM calls and response generation

These updates mirror what currently appears in the server terminal logs.

## Backend Progress Updates

The agent sends `agent_progress` messages at key stages:

| Stage | When | Example Message |
|-------|------|-----------------|
| `processing` | Message received | "Processing message..." |
| `analyzing` | Analyzing question | "Analyzing your question..." |
| `tool_execution` | Starting tool | "Executing tool: search_approved_articles" |
| `tool_success` | Tool succeeded | "Tool 'search_approved_articles' executed successfully" |
| `tool_error` | Tool failed | "Tool failed: Connection timeout" |
| `sql_generation` | Generating SQL (SQL mode) | "Generating SQL query from your question..." |
| `sql_executed` | SQL ran successfully | "SQL query executed successfully. Found 42 result(s)." |
| `sql_error` | SQL failed | "SQL execution failed: Invalid syntax" |
| `llm_summarizing` | Generating summary | "Generating natural language summary of results..." |
| `generating_response` | Final LLM call | "Generating final response..." |
| `completed` | Processing done | "Response generated" |

## Message Format

```typescript
interface AgentProgressMessage {
  type: "agent_progress";
  stage: string;
  message: string;
  timestamp: number;  // Unix timestamp
  details?: {
    tool?: string;
    arguments?: Record<string, any>;
    sql?: string;
    row_count?: number;
    error?: string;
    output_length?: number;
    [key: string]: any;
  };
}
```

## Implementation

### Step 1: TypeScript Types

```typescript
// types/websocket.ts
export type ProgressStage =
  | 'processing'
  | 'analyzing'
  | 'tool_execution'
  | 'tool_success'
  | 'tool_error'
  | 'sql_generation'
  | 'sql_executed'
  | 'sql_error'
  | 'llm_summarizing'
  | 'generating_response'
  | 'completed';

export interface ProgressUpdate {
  stage: ProgressStage;
  message: string;
  timestamp: number;
  details?: Record<string, any>;
}

export interface ProgressState {
  current: ProgressUpdate | null;
  history: ProgressUpdate[];
}
```

### Step 2: Redux Slice for Progress

```typescript
// store/slices/progressSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ProgressUpdate, ProgressState } from '@/types/websocket';

const initialState: ProgressState = {
  current: null,
  history: []
};

const progressSlice = createSlice({
  name: 'progress',
  initialState,
  reducers: {
    addProgress: (state, action: PayloadAction<ProgressUpdate>) => {
      state.current = action.payload;
      state.history.push(action.payload);
    },

    clearProgress: (state) => {
      state.current = null;
      state.history = [];
    },

    // Clear history but keep current
    resetHistory: (state) => {
      state.history = state.current ? [state.current] : [];
    }
  }
});

export const { addProgress, clearProgress, resetHistory } = progressSlice.actions;
export default progressSlice.reducer;
```

### Step 3: WebSocket Handler Update

```typescript
// hooks/useWebSocket.ts or similar
import { useDispatch } from 'react-redux';
import { addProgress, clearProgress } from '@/store/slices/progressSlice';

export function useFluxionWebSocket() {
  const dispatch = useDispatch();

  const handleMessage = (event: MessageEvent) => {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case 'agent_progress':
        // Add progress update to store
        dispatch(addProgress({
          stage: message.stage,
          message: message.message,
          timestamp: message.timestamp,
          details: message.details
        }));
        break;

      case 'agent_message':
        // Final response received - can clear progress
        // or mark as completed
        break;

      case 'error':
        // Handle error
        break;

      // ... other message types
    }
  };

  // When connecting, clear old progress
  const connect = () => {
    dispatch(clearProgress());
    // ... create websocket connection
    websocket.onmessage = handleMessage;
  };

  return { connect };
}
```

### Step 4: Progress Display Component

```typescript
// components/AgentProgress.tsx
'use client';

import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { CheckCircle, Loader2, XCircle, Database, Sparkles } from 'lucide-react';

export default function AgentProgress() {
  const { current, history } = useSelector((state: RootState) => state.progress);

  if (!current) return null;

  return (
    <div className="agent-progress bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      {/* Current Progress */}
      <div className="flex items-center gap-3">
        {getStageIcon(current.stage)}
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{current.message}</p>
          {current.details && (
            <div className="mt-1 text-xs text-gray-500">
              {formatDetails(current.details)}
            </div>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {formatTimestamp(current.timestamp)}
        </span>
      </div>

      {/* Progress History (collapsible) */}
      {history.length > 1 && (
        <details className="mt-3">
          <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
            View all steps ({history.length})
          </summary>
          <div className="mt-2 space-y-2">
            {history.map((update, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-gray-600 pl-4">
                <span className="text-gray-400">{i + 1}.</span>
                <span>{update.message}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

function getStageIcon(stage: string) {
  switch (stage) {
    case 'completed':
    case 'tool_success':
    case 'sql_executed':
      return <CheckCircle className="w-5 h-5 text-green-500" />;

    case 'tool_error':
    case 'sql_error':
      return <XCircle className="w-5 h-5 text-red-500" />;

    case 'tool_execution':
    case 'sql_generation':
      return <Database className="w-5 h-5 text-blue-500 animate-pulse" />;

    case 'analyzing':
    case 'llm_summarizing':
    case 'generating_response':
      return <Sparkles className="w-5 h-5 text-purple-500 animate-pulse" />;

    default:
      return <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />;
  }
}

function formatDetails(details: Record<string, any>): string {
  if (details.tool) {
    return `Tool: ${details.tool}`;
  }
  if (details.sql) {
    return `SQL: ${details.sql.substring(0, 50)}...`;
  }
  if (details.row_count !== undefined) {
    return `Rows: ${details.row_count}`;
  }
  if (details.error) {
    return `Error: ${details.error}`;
  }
  return '';
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleTimeString();
}
```

### Step 5: Alternative - Inline Progress Display

For a simpler UI, show progress inline with messages:

```typescript
// components/ChatMessage.tsx
export function ChatMessage({ message }: { message: Message }) {
  const progress = useSelector((state: RootState) => state.progress.current);

  return (
    <div className="message-container">
      {/* User message */}
      {message.type === 'user' && (
        <div className="user-message">{message.content}</div>
      )}

      {/* Agent is processing - show progress */}
      {message.type === 'agent' && message.isProcessing && progress && (
        <div className="agent-processing">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{progress.message}</span>
          </div>
        </div>
      )}

      {/* Final agent response */}
      {message.type === 'agent' && !message.isProcessing && (
        <div className="agent-message">{message.content}</div>
      )}
    </div>
  );
}
```

### Step 6: Progress Bar Component

Show visual progress through stages:

```typescript
// components/ProgressBar.tsx
const PROGRESS_STAGES = [
  'processing',
  'analyzing',
  'tool_execution',
  'generating_response',
  'completed'
] as const;

export function ProgressBar() {
  const current = useSelector((state: RootState) => state.progress.current);

  if (!current) return null;

  const currentIndex = PROGRESS_STAGES.indexOf(current.stage as any);
  const progress = ((currentIndex + 1) / PROGRESS_STAGES.length) * 100;

  return (
    <div className="progress-bar-container">
      <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-purple-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-gray-600">{current.message}</p>
    </div>
  );
}
```

## UI/UX Recommendations

### 1. Collapsible Progress Panel

```typescript
<div className="chat-container">
  {/* Collapsible progress panel */}
  <Collapsible>
    <CollapsibleTrigger>
      Agent Progress {current && `(${current.stage})`}
    </CollapsibleTrigger>
    <CollapsibleContent>
      <AgentProgress />
    </CollapsibleContent>
  </Collapsible>

  {/* Chat messages */}
  <ChatMessages />
</div>
```

### 2. Toast Notifications for Errors

```typescript
useEffect(() => {
  if (progress.current?.stage === 'tool_error' || progress.current?.stage === 'sql_error') {
    toast.error(progress.current.message);
  }
}, [progress.current]);
```

### 3. Debug Mode Toggle

```typescript
const [showProgress, setShowProgress] = useState(false);

// Only show progress in debug mode or when user enables it
{showProgress && <AgentProgress />}
```

### 4. Timing Information

```typescript
// Calculate time between stages
const getStageTime = (current: ProgressUpdate, previous?: ProgressUpdate) => {
  if (!previous) return null;
  const duration = (current.timestamp - previous.timestamp) * 1000; // Convert to ms
  return `${duration.toFixed(0)}ms`;
};
```

## Example Full Integration

```typescript
// pages/chat.tsx
'use client';

import { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import AgentProgress from '@/components/AgentProgress';
import ChatMessages from '@/components/ChatMessages';

export default function ChatPage() {
  const [showDebug, setShowDebug] = useState(false);
  const progress = useSelector((state: RootState) => state.progress.current);

  return (
    <div className="flex flex-col h-screen">
      {/* Header with debug toggle */}
      <header className="border-b p-4">
        <div className="flex items-center justify-between">
          <h1>Fluxion Chat</h1>
          <button
            onClick={() => setShowDebug(!showDebug)}
            className="text-sm text-gray-600"
          >
            {showDebug ? 'Hide' : 'Show'} Agent Progress
          </button>
        </div>
      </header>

      {/* Main chat area */}
      <main className="flex-1 overflow-auto p-4">
        {/* Progress panel (when enabled) */}
        {showDebug && progress && (
          <AgentProgress />
        )}

        {/* Chat messages */}
        <ChatMessages />
      </main>

      {/* Input area */}
      <footer className="border-t p-4">
        {/* Progress indicator in input area */}
        {progress && !showDebug && (
          <div className="mb-2 text-xs text-gray-600">
            {progress.message}
          </div>
        )}

        <ChatInput />
      </footer>
    </div>
  );
}
```

## Testing the Progress Updates

### 1. Watch All Stages

Send a message that triggers tools:
```
User: "How many articles are approved?"

Expected progress:
1. processing: "Processing message..."
2. analyzing: "Analyzing your question..."
3. tool_execution: "Executing tool: count_approved_articles"
4. tool_success: "Tool 'count_approved_articles' executed successfully"
5. generating_response: "Generating final response..."
6. completed: "Response generated"
```

### 2. SQL Mode Progress

Use `/sql` prefix:
```
User: "/sql Show me articles from California"

Expected progress:
1. processing: "Processing SQL query..."
2. sql_generation: "Generating SQL query from your question..."
3. sql_executed: "SQL query executed successfully. Found 15 result(s)."
4. llm_summarizing: "Generating natural language summary of results..."
5. completed: "Response generated"
```

### 3. Error Handling

Send invalid request:
```
Expected progress:
1. processing: "Processing message..."
2. analyzing: "Analyzing your question..."
3. tool_execution: "Executing tool: get_article_by_id"
4. tool_error: "Tool 'get_article_by_id' failed: Invalid ID"
5. generating_response: "Generating final response..."
6. completed: "Response generated"
```

## Performance Considerations

- **Update Frequency**: Progress messages are lightweight (< 1KB each)
- **History Limit**: Consider limiting progress history to last 50 updates
- **Auto-clear**: Clear progress when user sends new message
- **Memory**: Each chat session stores its own progress history

## Styling Examples

### Minimalist

```tsx
<div className="text-xs text-gray-500 italic">
  {progress?.message}
</div>
```

### Detailed Panel

```tsx
<div className="bg-blue-50 border-l-4 border-blue-500 p-3">
  <div className="flex items-center gap-2">
    {icon}
    <span className="font-medium">{progress.message}</span>
  </div>
  {progress.details && (
    <pre className="mt-2 text-xs bg-white p-2 rounded">
      {JSON.stringify(progress.details, null, 2)}
    </pre>
  )}
</div>
```

## Summary

**Key Points:**
- Backend sends `agent_progress` messages at 11 different stages
- Messages include stage, message, timestamp, and optional details
- Frontend stores in Redux and displays in component
- Can show as inline status, panel, progress bar, or debug mode
- Provides visibility into agent's internal processing

**Integration Steps:**
1. Add progress types to TypeScript definitions
2. Create Redux slice for progress state
3. Update WebSocket handler to dispatch progress updates
4. Create `AgentProgress` component
5. Add to chat UI with toggle for showing/hiding
6. Style appropriately for your design system

The progress updates work automatically - no backend configuration needed! Just handle the `agent_progress` messages in your WebSocket listener.

For questions or issues, see `/docs/API_REFERENCE.md` for message format details.
