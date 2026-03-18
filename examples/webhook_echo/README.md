# Webhook Echo

The simplest possible Ask DIANA extension. Receives any webhook, logs it, responds 200.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
export ASKDIANA_API_KEY="askd_your_key"
python app.py
```

Server starts on `http://localhost:5001`.

## Test with ngrok

```bash
ngrok http 5001
```

Use the ngrok URL as your webhook URL in the extension manifest:

```json
{
  "name": "Webhook Echo",
  "version": "1.0.0",
  "type": "communication",
  "description": "Echoes all webhook events to the console",
  "permissions": [],
  "webhooks": {
    "on_install": "https://your-ngrok-url.ngrok.io/webhooks",
    "on_uninstall": "https://your-ngrok-url.ngrok.io/webhooks",
    "on_event": "https://your-ngrok-url.ngrok.io/webhooks"
  }
}
```
