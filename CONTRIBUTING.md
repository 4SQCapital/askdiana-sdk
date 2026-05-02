# Contributing to the Ask DIANA Extension SDK

Thank you for your interest in contributing! This guide covers how to set up
a local development environment, run the tests, and submit changes.

## Prerequisites

- Python 3.8 or newer
- Git
- [ngrok](https://ngrok.com) (for webhook testing)

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/4SQCapital/ask.git
cd ask

# 2. Create a virtual environment
python -m venv .venv

# Activate it:
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install the SDK in editable mode with all extras
pip install -e ".[app]"

# 4. Verify the install
python -c "import askdiana; print(askdiana.__version__)"
```

## Running Tests

```bash
python test_sdk.py
```

The test suite covers:
- Field serialization (all field types)
- Schema generation and validation
- Model inheritance
- `register_all_models` batch registration

## Running an Example

Each example has its own `.env.example`. Copy and fill it in, then run:

```bash
cd examples/gamma
cp .env.example .env
# Edit .env with your credentials
python app.py
```

To receive webhooks locally, expose your server with ngrok:

```bash
ngrok http 5004
# Copy the https://xxxx.ngrok.io URL and set it as your webhook URL
# in the extension settings on Ask DIANA.
```

### SSL on Windows

If you encounter SSL errors during local development, add to your `.env`:

```
ASKDIANA_VERIFY_SSL=false
```

## Project Structure

```
askdiana/               Core SDK package
├── client.py           AskDianaClient — all API calls
├── models.py           ExtModel and field classes
├── webhooks.py         Bearer token verification
├── app.py              ExtensionApp (Flask wrapper with auto-discovery)
├── service.py          ExtensionService base class
├── chat.py             ChatService for AI chat extensions
├── connector.py        ConnectorService for file sync extensions
├── controller.py       Flask decorators (webhook_required, install_id_required)
├── discovery.py        Auto-discovery of models and blueprints
└── cli.py              CLI tools (askdiana init, scaffold)
examples/               Reference implementations
connectors/             Production connector implementations
test_sdk.py             Feature test suite
```

## Making Changes

1. Create a feature branch: `git checkout -b feat/your-change`
2. Make your changes and add tests in `test_sdk.py` if applicable
3. Run `python test_sdk.py` — all tests must pass
4. Open a pull request against `main` with a clear description of the change

## Code Style

- Follow the existing docstring style (Google-style, `Args:` / `Returns:` / `Raises:`)
- Keep exception handling explicit — avoid bare `except Exception` without logging
- New public methods must have a docstring with at least `Args` and `Returns` sections
- Table names must start with `ext_` and be unique within an extension

## Reporting Issues

Open an issue at https://github.com/4SQCapital/ask/issues with:
- SDK version (`python -c "import askdiana; print(askdiana.__version__)"`)
- Python version (`python --version`)
- Minimal reproduction steps
- Full error traceback
