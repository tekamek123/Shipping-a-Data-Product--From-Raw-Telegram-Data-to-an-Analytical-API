"""
Helper script to create .env file from template
"""
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ENV_EXAMPLE = BASE_DIR / '.env.example'
ENV_FILE = BASE_DIR / '.env'

if ENV_EXAMPLE.exists() and not ENV_FILE.exists():
    shutil.copy(ENV_EXAMPLE, ENV_FILE)
    print(f"Created .env file from .env.example")
    print("Please edit .env and add your Telegram API credentials")
else:
    print(".env file already exists or .env.example not found")

