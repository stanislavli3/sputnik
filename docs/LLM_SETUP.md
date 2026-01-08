# LLM Integration Setup

Sputnik supports open source LLMs for intelligent query planning, SQL generation, and answer synthesis.

## Supported Providers

### 1. Ollama (Recommended for Local Development)

Ollama allows you to run open source models locally on your machine.

#### Installation

1. Install Ollama: https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3
   # or
   ollama pull mistral
   # or
   ollama pull codellama
   ```

#### Configuration

Set environment variables:

```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3
export OLLAMA_BASE_URL=http://localhost:11434  # Default
```

Or in a `.env` file:
```
LLM_PROVIDER=ollama
LLM_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```

### 2. OpenRouter (Cloud-based Open Source Models)

OpenRouter provides API access to many open source models.

#### Configuration

1. Get an API key from https://openrouter.ai
2. Set environment variables:

```bash
export LLM_PROVIDER=openrouter
export LLM_MODEL=meta-llama/llama-3-8b-instruct
export LLM_API_KEY=your_api_key_here
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Provider name (`ollama` or `openrouter`) | `ollama` |
| `LLM_MODEL` | Model name | `llama3` |
| `LLM_BASE_URL` | Base URL for the LLM service | Provider-specific |
| `LLM_API_KEY` | API key (for OpenRouter) | None |
| `USE_LLM_PLANNING` | Enable LLM for planning | `true` |
| `USE_LLM_SQL` | Enable LLM for SQL generation | `true` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |

## Disabling LLM Features

To use rule-based fallbacks instead of LLMs:

```bash
export USE_LLM_PLANNING=false
export USE_LLM_SQL=false
```

## Recommended Models

### For SQL Generation
- `codellama` (Code Llama) - Best for SQL
- `llama3` - Good general purpose
- `mistral` - Fast and efficient

### For Planning and Answer Generation
- `llama3` - Good balance
- `mistral` - Faster inference
- `llama3:70b` - Better quality (requires more RAM)

## Testing Your Setup

1. Start Ollama (if using local):
   ```bash
   ollama serve
   ```

2. Test the connection:
   ```python
   from sputnik.llm.client import create_llm_client
   import asyncio
   
   async def test():
       client = create_llm_client()
       response = await client.generate("Hello, world!")
       print(response)
   
   asyncio.run(test())
   ```

3. Run the Sputnik server:
   ```bash
   python scripts/start_server.py
   ```

## Troubleshooting

### Ollama Connection Errors

- Ensure Ollama is running: `ollama serve`
- Check the model is pulled: `ollama list`
- Verify the base URL matches your Ollama setup

### OpenRouter Errors

- Verify your API key is correct
- Check your account has credits
- Ensure the model name is correct (check OpenRouter docs)

### Fallback to Rule-based

If LLM calls fail, Sputnik automatically falls back to rule-based planning and SQL generation. Check logs for error messages.
