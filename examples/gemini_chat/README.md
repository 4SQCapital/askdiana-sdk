# Ask Gemini — AI Chat Extension

An Ask DIANA extension that adds **"Ask Gemini"** as a chat mode. Users select it from the chat dropdown and their messages are processed by Google's Gemini API.

## Features

- Adds a new chat mode to the Ask DIANA chat dropdown
- Multi-turn conversations with full history context
- Users can bring their own Gemini API key (or use the developer's default)
- Model selection: Gemini 2.0 Flash, Flash Lite, or 2.5 Pro
- Error handling for invalid keys, safety filters, and API failures

## Architecture

```
User selects "Ask Gemini" in chat dropdown
    → Types a message
    → Ask DIANA proxies to POST /api/chat
    → GeminiChatService.respond() called
    → Builds conversation from history
    → Calls Gemini API
    → Returns response text
    → Displayed in Ask DIANA chat UI
```

## Setup

### 1. Get a Gemini API Key

Go to [Google AI Studio](https://aistudio.google.com/apikey) and create an API key.

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python app.py
```

The server starts on port 5003 (configurable via `PORT` env var).

### 5. Expose with ngrok (for development)

```bash
ngrok http 5003
```

### 6. Register in Ask DIANA

1. Go to **Developer Portal** > **My Extensions** > **Create Extension**
2. Fill in name: "Ask Gemini", slug: "ask-gemini", type: "AI/ML"
3. Submit a version with the `manifest.json` contents
4. Set the **webhook URL** to your ngrok URL
5. Install the extension

### 7. Start Chatting

The "Ask Gemini" option appears in the chat mode dropdown alongside Knowledge and Analytics. Select it and start chatting!

## Files

| File | Description |
|------|-------------|
| `app.py` | Flask app entry point, webhook handlers |
| `gemini_service.py` | GeminiChatService — core AI logic |
| `manifest.json` | Extension manifest for Ask DIANA |
| `.env.example` | Environment variables template |
| `requirements.txt` | Python dependencies |

## How ChatService Works

`ChatService` is the SDK base class for AI chat extensions. You only need to implement one method:

```python
class GeminiChatService(ChatService):
    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        # Your AI logic here
        return "AI response text"
```

`register_routes(app)` automatically wires up `POST /api/chat` with signature verification.

### Built-in Helpers

- `get_api_key(install_id)` — Read user's stored API key
- `get_config(install_id, key)` — Read any config value
- `set_config(install_id, key, value)` — Write config value
- `store_conversation(install_id, chat_id, msg, response)` — Store in ext data

## Configuration

Users can configure the extension after installing:

| Setting | Description |
|---------|-------------|
| **API Key** | Optional. If provided, uses the user's own Gemini key instead of the developer's default |
| **Model** | Choose between Gemini 2.0 Flash (fast), Flash Lite (fastest), or 2.5 Pro (most capable) |
