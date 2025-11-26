# LLM Provider Switching Integration Guide for Fluxion00Web

This guide explains how to implement LLM provider and model selection in the Fluxion00Web NextJS frontend.

## Overview

Fluxion00API now supports multiple LLM providers with dynamic model selection:
- **Ollama**: Local instance with models like `mistral:instruct`
- **OpenAI**: Cloud-based GPT models like `gpt-4o-mini`, `gpt-4-turbo`

Provider and model are selected **at WebSocket connection time** via query parameters.

## Architecture

### Backend Behavior
- **No model validation**: Backend accepts any model string and passes it to the LLM API
- **Provider validation**: Only validates that provider is "ollama" or "openai"
- **Per-connection**: Each WebSocket connection uses one provider/model for its entire session
- **API determines validity**: If model doesn't exist, the LLM API (OpenAI/Ollama) returns an error

### Frontend Responsibility
- Store provider and model selection in Redux/state
- Build WebSocket URL with provider and model query params
- Handle connection errors for invalid providers/models
- Display model selector UI

## Implementation

### Step 1: Redux State Structure

```typescript
// types/llm.ts
export type LLMProvider = 'ollama' | 'openai';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
}

// Available models per provider (frontend only - not validated by backend)
export const PROVIDER_MODELS: Record<LLMProvider, string[]> = {
  ollama: ['mistral:instruct'],
  openai: ['gpt-4o-mini', 'gpt-4-turbo']
};

export const DEFAULT_LLM_CONFIG: LLMConfig = {
  provider: 'ollama',
  model: 'mistral:instruct'
};
```

### Step 2: Redux Slice

```typescript
// store/slices/llmSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { LLMConfig, LLMProvider, DEFAULT_LLM_CONFIG } from '@/types/llm';

interface LLMState {
  config: LLMConfig;
}

const initialState: LLMState = {
  config: DEFAULT_LLM_CONFIG
};

const llmSlice = createSlice({
  name: 'llm',
  initialState,
  reducers: {
    setProvider: (state, action: PayloadAction<LLMProvider>) => {
      state.config.provider = action.payload;

      // Reset to default model for the selected provider
      if (action.payload === 'ollama') {
        state.config.model = 'mistral:instruct';
      } else if (action.payload === 'openai') {
        state.config.model = 'gpt-4o-mini';
      }
    },

    setModel: (state, action: PayloadAction<string>) => {
      state.config.model = action.payload;
    },

    setConfig: (state, action: PayloadAction<LLMConfig>) => {
      state.config = action.payload;
    }
  }
});

export const { setProvider, setModel, setConfig } = llmSlice.actions;
export default llmSlice.reducer;
```

### Step 3: WebSocket Connection with Provider/Model

```typescript
// hooks/useWebSocket.ts or similar
import { useSelector } from 'react-redux';
import { RootState } from '@/store';

export function useFluxionWebSocket() {
  const { token, user } = useSelector((state: RootState) => state.auth);
  const { config } = useSelector((state: RootState) => state.llm);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = useCallback(() => {
    const clientId = crypto.randomUUID();

    // Build WebSocket URL with provider and model
    const params = new URLSearchParams({
      token: token,
      provider: config.provider,
      model: config.model
    });

    const wsUrl = `${process.env.NEXT_PUBLIC_FLUXION_WS_URL}/ws/${clientId}?${params}`;

    console.log(`Connecting to Fluxion with ${config.provider} (${config.model})`);

    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('Connected to Fluxion00API');
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = (event) => {
      if (event.code === 4000) {
        // Provider/model error
        console.error('Provider error:', event.reason);
        // Show error to user
      }
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleMessage(message);
    };

    setWs(websocket);

    return websocket;
  }, [token, config.provider, config.model]);

  return { ws, connect };
}
```

### Step 4: Model Selector UI Component

```typescript
// components/ModelSelector.tsx
'use client';

import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store';
import { setProvider, setModel } from '@/store/slices/llmSlice';
import { PROVIDER_MODELS, LLMProvider } from '@/types/llm';

export default function ModelSelector() {
  const dispatch = useDispatch();
  const { config } = useSelector((state: RootState) => state.llm);

  const handleProviderChange = (provider: LLMProvider) => {
    dispatch(setProvider(provider));
  };

  const handleModelChange = (model: string) => {
    dispatch(setModel(model));
  };

  return (
    <div className="model-selector">
      <div className="provider-selector">
        <label htmlFor="provider">Provider:</label>
        <select
          id="provider"
          value={config.provider}
          onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
          className="border rounded px-3 py-2"
        >
          <option value="ollama">Ollama (Local)</option>
          <option value="openai">OpenAI (Cloud)</option>
        </select>
      </div>

      <div className="model-selector">
        <label htmlFor="model">Model:</label>
        <select
          id="model"
          value={config.model}
          onChange={(e) => handleModelChange(e.target.value)}
          className="border rounded px-3 py-2"
        >
          {PROVIDER_MODELS[config.provider].map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>

      <div className="current-config text-sm text-gray-600 mt-2">
        Current: {config.provider} / {config.model}
      </div>
    </div>
  );
}
```

### Step 5: Alternative - Custom Model Input

For advanced users who want to enter custom model names:

```typescript
export default function AdvancedModelSelector() {
  const dispatch = useDispatch();
  const { config } = useSelector((state: RootState) => state.llm);
  const [customModel, setCustomModel] = useState(config.model);

  return (
    <div className="advanced-model-selector">
      <select
        value={config.provider}
        onChange={(e) => dispatch(setProvider(e.target.value as LLMProvider))}
      >
        <option value="ollama">Ollama</option>
        <option value="openai">OpenAI</option>
      </select>

      <input
        type="text"
        value={customModel}
        onChange={(e) => setCustomModel(e.target.value)}
        onBlur={() => dispatch(setModel(customModel))}
        placeholder={config.provider === 'ollama' ? 'mistral:instruct' : 'gpt-4o-mini'}
        className="border rounded px-3 py-2"
      />

      <p className="text-xs text-gray-500">
        Backend accepts any model name. Invalid models will error at connection time.
      </p>
    </div>
  );
}
```

## Complete Flow Example

### 1. User Selects Provider/Model

```
User in UI:
  - Selects "OpenAI" from provider dropdown
  - Selects "gpt-4o-mini" from model dropdown

Redux State Updated:
  { provider: "openai", model: "gpt-4o-mini" }
```

### 2. Connection Initiated

```typescript
// WebSocket connection built with query params
const wsUrl = `ws://localhost:8000/ws/abc-123?token=eyJ...&provider=openai&model=gpt-4o-mini`;

// Backend receives:
// - provider_type = "openai"
// - model = "gpt-4o-mini"

// Backend creates:
// - OpenAIProvider with default_model="gpt-4o-mini"
// - Agent with that provider
```

### 3. User Sends Message

```typescript
const message = {
  type: 'user_message',
  content: 'How many articles are approved?'
};

ws.send(JSON.stringify(message));

// Backend uses OpenAI gpt-4o-mini to process this message
// Response comes from GPT-4o-mini
```

## Error Handling

### Invalid Provider

```typescript
websocket.onclose = (event) => {
  if (event.code === 4000 && event.reason.includes('Invalid provider')) {
    // Show user-friendly error
    toast.error('Invalid LLM provider selected. Please try again.');

    // Reset to default
    dispatch(setConfig(DEFAULT_LLM_CONFIG));
  }
};
```

### Invalid Model

```typescript
// Backend doesn't validate models - the LLM API does
// If OpenAI returns error for invalid model, it comes as agent error message

websocket.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'error' && message.content.includes('model')) {
    toast.error(`Model error: ${message.content}`);
    // Optionally suggest falling back to default model
  }
};
```

## UI/UX Recommendations

### Connection Indicator

Show which provider/model is active:

```typescript
<div className="connection-status">
  {isConnected ? (
    <span className="text-green-600">
      ✓ Connected: {config.provider} ({config.model})
    </span>
  ) : (
    <span className="text-gray-500">Not connected</span>
  )}
</div>
```

### Changing Provider Mid-Session

Provider/model changes require reconnection:

```typescript
const handleProviderChange = async (newProvider: LLMProvider) => {
  // Update Redux
  dispatch(setProvider(newProvider));

  // Close existing connection
  if (ws) {
    ws.close();
  }

  // Show reconnecting indicator
  setReconnecting(true);

  // Reconnect with new provider
  await connect();

  setReconnecting(false);
};
```

### Settings Panel

```typescript
<div className="settings-panel">
  <h3>LLM Configuration</h3>

  <ModelSelector />

  <button
    onClick={() => {
      // Save to localStorage or backend
      localStorage.setItem('llm_config', JSON.stringify(config));
    }}
  >
    Save Preferences
  </button>

  <p className="help-text">
    Changes take effect on next connection.
  </p>
</div>
```

## Environment Variables

Add to `.env.local`:

```bash
NEXT_PUBLIC_FLUXION_WS_URL=ws://localhost:8000
NEXT_PUBLIC_DEFAULT_PROVIDER=ollama
NEXT_PUBLIC_DEFAULT_MODEL=mistral:instruct
```

## Testing Checklist

- [ ] Default connection (Ollama, mistral:instruct)
- [ ] Switch to OpenAI with gpt-4o-mini
- [ ] Switch to OpenAI with gpt-4-turbo
- [ ] Invalid provider shows error
- [ ] Invalid model handled gracefully
- [ ] Provider selection persists in state
- [ ] Reconnection works after provider change
- [ ] All chat features work with both providers

## Model Availability

**Ollama Models** (example - add your available models):
- `mistral:instruct` (default)
- `llama2`
- `codellama`

**OpenAI Models**:
- `gpt-4o-mini` (default, fastest/cheapest)
- `gpt-4-turbo` (more powerful)
- `gpt-4` (most powerful)
- `gpt-3.5-turbo` (legacy)

Frontend can define model list or fetch from `/api/info`.

## API Info Integration

Optionally fetch supported providers from backend:

```typescript
const fetchProviders = async () => {
  const response = await fetch('http://localhost:8000/api/info');
  const data = await response.json();

  // data.supported_providers contains:
  // {
  //   ollama: { default_model: "mistral:instruct", ... },
  //   openai: { default_model: "gpt-4o-mini", ... }
  // }

  return data.supported_providers;
};
```

## Summary

**Key Points:**
- Provider and model selected via WebSocket query parameters
- Redux stores current LLM configuration
- Backend accepts any model name (no validation)
- LLM API validates model and returns errors if invalid
- Each WebSocket session uses one provider/model
- Changing provider requires reconnection

**Integration Steps:**
1. Add LLM state to Redux
2. Create model selector UI component
3. Update WebSocket connection to include query params
4. Handle connection errors gracefully
5. Test with both Ollama and OpenAI

For questions or issues, see `/docs/API_REFERENCE.md` or contact the Fluxion00API team.
