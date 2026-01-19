# Telegram Scraper

## Setup Instructions

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy your `api_id` and `api_hash`

### 2. Configure Environment Variables

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+251912345678
   ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Scraper

```bash
python src/scraper.py
```

The first time you run it, Telegram will send you a verification code. Enter it when prompted.

## Output Structure

- **Raw Messages**: `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`
- **Images**: `data/raw/images/channel_name/message_id.jpg`
- **Logs**: `logs/scraper_YYYYMMDD_HHMMSS.log`

## Features

- Scrapes messages from multiple Telegram channels
- Downloads images from messages
- Stores data in partitioned JSON structure (by date)
- Comprehensive logging
- Handles rate limiting and errors gracefully
- Avoids duplicate messages when re-running
