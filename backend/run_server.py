from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from server import app


if __name__ == "__main__":
    host = os.getenv("CHATBOT_HOST", "127.0.0.1")
    port = int(os.getenv("CHATBOT_PORT", "8000"))
    reload_flag = os.getenv("CHATBOT_RELOAD", "false").lower() == "true"

    uvicorn.run(app, host=host, port=port, reload=reload_flag)
