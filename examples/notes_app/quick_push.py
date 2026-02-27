"""
quick_push.py — Push extension schema directly (bypasses CLI entry point).

Usage:
    cd notes_app/
    python quick_push.py
"""

from dotenv import load_dotenv
load_dotenv()

import os
import sys

# Ensure the parent directory is on sys.path so `askdiana` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Also ensure current dir is on path so `models` package is importable
sys.path.insert(0, os.path.dirname(__file__) or os.getcwd())

from askdiana.client import AskDianaClient
from askdiana.discovery import discover_models
from askdiana.models import register_all_models

api_key = os.environ.get("ASKDIANA_API_KEY", "")
base_url = os.environ.get("ASKDIANA_BASE_URL", "https://app.askdiana.ai")
install_id = os.environ.get("ASKDIANA_INSTALL_ID", "")

if not api_key:
    print("Error: ASKDIANA_API_KEY not found in .env")
    sys.exit(1)
if not install_id:
    print("Error: ASKDIANA_INSTALL_ID not found in .env")
    sys.exit(1)

print(f"API key : {api_key[:12]}...")
print(f"Base URL: {base_url}")
print(f"Install : {install_id}")
print()

client = AskDianaClient(api_key=api_key, base_url=base_url)

models = discover_models("models")
if not models:
    print("No models found in models/ directory.")
    sys.exit(1)

print(f"Found {len(models)} model(s): {[m.__name__ for m in models]}")

# Register all models in one call
result = register_all_models(client, install_id, "1.0.0", *models)
print(f"Registered: {result}")

# Apply each table
for m in models:
    res = m.apply(client, install_id)
    print(f"Applied {m.__tablename__}: {res}")

print()
print("Done! Schema pushed successfully.")
