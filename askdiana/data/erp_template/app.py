import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from demo_data import generate as generate_demo_data

from askdiana import ExtensionApp
from askdiana.erp import ErpExtension

logging.basicConfig(level=logging.INFO)

HERE = Path(__file__).resolve().parent
PACK_PATH = HERE / "pack" / "__PACK__.yaml"
STATIC_DIR = HERE / "static"
DEFAULT_PORT = 5000

app = ExtensionApp(__name__, auto_discover=False)
erp = ErpExtension(PACK_PATH, demo_provider=generate_demo_data, static_dir=STATIC_DIR).mount(app)

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", DEFAULT_PORT)), debug=False)
