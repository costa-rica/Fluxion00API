# SQL Mode Integration Guide for Fluxion00Web

This guide explains how to implement SQL mode in the Fluxion00Web NextJS frontend.

## Overview

SQL mode allows users to explicitly trigger Text-to-SQL queries, bypassing the agent's normal tool selection. The backend supports **two methods**:

1. **UI-driven** (recommended): Add `mode: "sql"` to the message payload
2. **User-driven**: Users type `/sql` prefix in their message

## Implementation Options

### Option 1: UI Toggle (Recommended)

Add a toggle or button in your chat interface that sets SQL mode.

**NextJS/TypeScript Example**:

```typescript
// State for SQL mode
const [useSqlMode, setUseSqlMode] = useState(false);

// Send message function
const sendMessage = (userInput: string) => {
  const message = {
    type: 'user_message',
    content: userInput,
    mode: useSqlMode ? 'sql' : 'auto'  // Add mode field
  };

  websocket.send(JSON.stringify(message));
};

// UI Component
<div className="chat-controls">
  <input
    type="text"
    value={input}
    onChange={(e) => setInput(e.target.value)}
    onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
  />

  <label>
    <input
      type="checkbox"
      checked={useSqlMode}
      onChange={(e) => setUseSqlMode(e.target.checked)}
    />
    SQL Mode
  </label>

  <button onClick={() => sendMessage(input)}>
    Send
  </button>
</div>
```

**Benefits**:
- Clean UX - users don't see implementation details
- Works with all user input (no prefix stripping needed)
- Easy to add UI indicators (badge, icon, different styling)
- Can be toggled on/off mid-conversation

### Option 2: Command Prefix Detection

Users type `/sql` at the start of their message.

**NextJS/TypeScript Example**:

```typescript
const sendMessage = (userInput: string) => {
  // Frontend doesn't need to do anything special
  // Backend automatically detects /sql prefix
  const message = {
    type: 'user_message',
    content: userInput  // e.g., "/sql Show articles from California"
  };

  websocket.send(JSON.stringify(message));
};
```

**Optional: Auto-detect and show indicator**:

```typescript
const sendMessage = (userInput: string) => {
  const isSqlCommand = userInput.trim().startsWith('/sql');

  const message = {
    type: 'user_message',
    content: userInput
  };

  // Show SQL mode badge in UI
  if (isSqlCommand) {
    showSqlIndicator();
  }

  websocket.send(JSON.stringify(message));
};
```

**Benefits**:
- No UI changes needed
- Power users can quickly switch modes
- Works in any text input

### Option 3: Hybrid Approach (Best of Both)

Combine both methods for maximum flexibility.

```typescript
const [useSqlMode, setUseSqlMode] = useState(false);

const sendMessage = (userInput: string) => {
  // Check for /sql prefix in content
  const hasPrefix = userInput.trim().startsWith('/sql');

  const message = {
    type: 'user_message',
    content: userInput,
    mode: (useSqlMode || hasPrefix) ? 'sql' : 'auto'
  };

  websocket.send(JSON.stringify(message));

  // Show indicator if either method triggers SQL mode
  if (useSqlMode || hasPrefix) {
    showSqlModeIndicator();
  }
};
```

## UI/UX Recommendations

### Visual Indicators

Show users when SQL mode is active:

```typescript
// Badge in input area
{useSqlMode && (
  <span className="badge bg-purple-500">
    SQL Mode Active
  </span>
)}

// Different input styling
<input
  className={useSqlMode ? 'border-purple-500' : 'border-gray-300'}
  placeholder={useSqlMode ? 'Ask a question (SQL will be generated)...' : 'Ask a question...'}
/>
```

### Message Display

Show SQL mode in message history:

```typescript
interface Message {
  type: string;
  content: string;
  mode?: string;
  timestamp: string;
}

// Display component
const MessageBubble = ({ message }: { message: Message }) => (
  <div className="message">
    {message.mode === 'sql' && (
      <span className="text-xs text-purple-600">
        🔍 SQL Query
      </span>
    )}
    <p>{message.content}</p>
  </div>
);
```

### Toggle Button Styles

Example Tailwind CSS:

```tsx
<button
  onClick={() => setUseSqlMode(!useSqlMode)}
  className={`
    px-4 py-2 rounded-lg transition-colors
    ${useSqlMode
      ? 'bg-purple-600 text-white'
      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
    }
  `}
>
  {useSqlMode ? '🔍 SQL Mode ON' : 'SQL Mode'}
</button>
```

## Backend Behavior

When SQL mode is triggered (either method):

1. **Logging**: Server logs `[SQL MODE]` indicator
2. **Processing**: Bypasses normal tool selection
3. **Execution**: Directly calls `execute_custom_sql` tool
4. **Security**: All queries validated (SELECT only, injection prevention, result limits)
5. **Response**: Natural language summary with SQL shown

**Server Logs Example**:
```
[AGENT] [SQL MODE] nickrodriguez (client_id: abc-123) | Message: "Show articles from California"
[TOOL] Executing: execute_custom_sql (forced)
[TOOL] Success | Output length: 2450 chars
```

## Complete Example Component

```typescript
import { useState, useEffect } from 'react';

interface ChatMessage {
  type: string;
  content: string;
  mode?: string;
}

export default function ChatInterface() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [useSqlMode, setUseSqlMode] = useState(false);

  useEffect(() => {
    const clientId = crypto.randomUUID();
    const token = getAuthToken(); // Your auth token
    const websocket = new WebSocket(
      `ws://localhost:8000/ws/${clientId}?token=${token}`
    );

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'agent_message') {
        setMessages(prev => [...prev, message]);
      }
    };

    setWs(websocket);

    return () => websocket.close();
  }, []);

  const sendMessage = () => {
    if (!ws || !input.trim()) return;

    const message = {
      type: 'user_message',
      content: input,
      mode: useSqlMode ? 'sql' : 'auto'
    };

    ws.send(JSON.stringify(message));

    // Add to local messages
    setMessages(prev => [...prev, {
      type: 'user_message',
      content: input,
      mode: useSqlMode ? 'sql' : 'auto'
    }]);

    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.type}`}>
            {msg.mode === 'sql' && (
              <span className="sql-badge">SQL Query</span>
            )}
            <p>{msg.content}</p>
          </div>
        ))}
      </div>

      <div className="input-area">
        <button
          onClick={() => setUseSqlMode(!useSqlMode)}
          className={useSqlMode ? 'active' : ''}
        >
          🔍 SQL
        </button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder={useSqlMode
            ? 'Ask a question (SQL will be generated)...'
            : 'Ask a question...'
          }
        />

        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
```

## Testing

Test both methods:

### Test 1: UI Toggle Method
```typescript
// Enable SQL mode via toggle
setUseSqlMode(true);
sendMessage("Show articles published in the last 7 days");
// Expected: Backend logs "[SQL MODE]" and uses Text-to-SQL
```

### Test 2: Command Prefix Method
```typescript
// Use /sql prefix
sendMessage("/sql Show articles published in the last 7 days");
// Expected: Same result as Test 1
```

### Test 3: Normal Mode
```typescript
// No SQL mode
setUseSqlMode(false);
sendMessage("How many articles are approved?");
// Expected: Agent decides which tool to use (may or may not use SQL)
```

## Security Notes

- All SQL queries are validated on the backend (SELECT only)
- SQL injection prevention is active
- Results are limited to prevent large payloads
- Read-only database connection is used
- User authentication still required via JWT

## Questions?

Contact the Fluxion00API team or see `/docs/API_REFERENCE.md` for complete API documentation.
