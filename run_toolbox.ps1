$ErrorActionPreference = "Stop"
python -m uvicorn web_toolbox.app:app --host 127.0.0.1 --port 8765 --reload
