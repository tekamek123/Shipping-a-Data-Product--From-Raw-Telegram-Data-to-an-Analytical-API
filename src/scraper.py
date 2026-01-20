"""
Telegram Channel Scraper for Medical Products Data

This script scrapes messages and images from public Telegram channels
and stores them in a raw data lake structure.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')
SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'telegram_session')

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data' / 'raw'
IMAGES_DIR = DATA_DIR / 'images'
MESSAGES_DIR = DATA_DIR / 'telegram_messages'
LOGS_DIR = BASE_DIR / 'logs'

# Create directories if they don't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MESSAGES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
log_file = LOGS_DIR / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramScraper:
    """Scraper for Telegram channels"""
    
    def __init__(self, api_id: str, api_hash: str, phone: str, session_name: str = 'telegram_session'):
        """
        Initialize the Telegram scraper
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone: Phone number with country code
            session_name: Name for the session file
        """
        if not api_id or not api_hash:
            raise ValueError("API_ID and API_HASH must be provided")
        
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.phone = phone
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        self.scraped_channels = set()
        self.scraped_dates = set()
        
    async def connect(self):
        """Connect to Telegram"""
        await self.client.start(phone=self.phone)
        logger.info("Connected to Telegram")
        
    async def scrape_channel(
        self, 
        channel_username: str, 
        limit: Optional[int] = None,
        offset_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Scrape messages from a Telegram channel
        
        Args:
            channel_username: Username of the channel (without @)
            limit: Maximum number of messages to scrape (None for all)
            offset_date: Only scrape messages after this date
            
        Returns:
            List of message dictionaries
        """
        messages = []
        channel_name = channel_username
        
        try:
            logger.info(f"Starting to scrape channel: {channel_username}")
            
            # Get channel entity
            entity = await self.client.get_entity(channel_username)
            channel_name = entity.title if hasattr(entity, 'title') else channel_username
            logger.info(f"Channel title: {channel_name}")
            
            # Scrape messages
            async for message in self.client.iter_messages(
                entity, 
                limit=limit,
                offset_date=offset_date
            ):
                if isinstance(message, Message):
                    message_data = self._extract_message_data(message, channel_name)
                    messages.append(message_data)
                    
                    # Download image if present
                    if message_data.get('has_media') and message_data.get('image_path'):
                        await self._download_image(message, message_data['image_path'])
            
            logger.info(f"Scraped {len(messages)} messages from {channel_username}")
            self.scraped_channels.add(channel_username)
            
        except Exception as e:
            logger.error(f"Error scraping channel {channel_username}: {str(e)}", exc_info=True)
            
        return messages
    
    def _extract_message_data(self, message: Message, channel_name: str) -> Dict:
        """
        Extract relevant data from a Telegram message
        
        Args:
            message: Telegram message object
            channel_name: Name of the channel
            
        Returns:
            Dictionary with message data
        """
        message_data = {
            'message_id': message.id,
            'channel_name': channel_name,
            'message_date': message.date.isoformat() if message.date else None,
            'message_text': message.text or '',
            'has_media': message.media is not None,
            'image_path': None,
            'views': message.views if hasattr(message, 'views') else None,
            'forwards': message.forwards if hasattr(message, 'forwards') else None,
        }
        
        # Check if message has photo media
        if message.media and isinstance(message.media, MessageMediaPhoto):
            image_filename = f"{channel_name}_{message.id}.jpg"
            # Sanitize channel name for filesystem
            safe_channel_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_channel_name = safe_channel_name.replace(' ', '_')
            image_dir = IMAGES_DIR / safe_channel_name
            image_dir.mkdir(parents=True, exist_ok=True)
            message_data['image_path'] = str(image_dir / image_filename)
        
        return message_data
    
    async def _download_image(self, message: Message, image_path: str):
        """
        Download image from a message
        
        Args:
            message: Telegram message object
            image_path: Path where to save the image
        """
        try:
            await self.client.download_media(message, file=image_path)
            logger.debug(f"Downloaded image: {image_path}")
        except Exception as e:
            logger.error(f"Error downloading image {image_path}: {str(e)}")
    
    def save_messages_to_datalake(self, messages: List[Dict], channel_name: str):
        """
        Save messages to the data lake in partitioned structure
        
        Args:
            messages: List of message dictionaries
            channel_name: Name of the channel
        """
        if not messages:
            return
        
        # Group messages by date
        messages_by_date = {}
        for msg in messages:
            if msg.get('message_date'):
                try:
                    date = datetime.fromisoformat(msg['message_date']).date()
                    date_str = date.strftime('%Y-%m-%d')
                    
                    if date_str not in messages_by_date:
                        messages_by_date[date_str] = []
                    messages_by_date[date_str].append(msg)
                    self.scraped_dates.add(date_str)
                except Exception as e:
                    logger.warning(f"Error parsing date for message {msg.get('message_id')}: {e}")
        
        # Save messages partitioned by date
        for date_str, date_messages in messages_by_date.items():
            date_dir = MESSAGES_DIR / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Sanitize channel name for filename
            safe_channel_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_channel_name = safe_channel_name.replace(' ', '_')
            filename = f"{safe_channel_name}.json"
            filepath = date_dir / filename
            
            # Load existing messages if file exists
            existing_messages = []
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_messages = json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading existing file {filepath}: {e}")
            
            # Merge with existing messages (avoid duplicates)
            existing_ids = {msg.get('message_id') for msg in existing_messages}
            new_messages = [msg for msg in date_messages if msg.get('message_id') not in existing_ids]
            all_messages = existing_messages + new_messages
            
            # Save to file
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(all_messages, f, ensure_ascii=False, indent=2)
                logger.info(f"Saved {len(new_messages)} new messages to {filepath}")
            except Exception as e:
                logger.error(f"Error saving messages to {filepath}: {e}")
    
    def get_scraping_summary(self) -> Dict:
        """Get summary of scraping activity"""
        return {
            'channels_scraped': list(self.scraped_channels),
            'dates_scraped': sorted(list(self.scraped_dates)),
            'total_channels': len(self.scraped_channels),
            'total_dates': len(self.scraped_dates)
        }


async def main():
    """Main function to run the scraper"""
    
    # Validate credentials
    if not API_ID or not API_HASH:
        logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
        return
    
    if not PHONE:
        logger.error("TELEGRAM_PHONE must be set in .env file")
        return
    
    # Initialize scraper
    scraper = TelegramScraper(API_ID, API_HASH, PHONE, SESSION_NAME)
    
    # Channels to scrape
    channels = [
        'CheMed123',  # CheMed Telegram Channel
        'lobelia4cosmetics',  # Lobelia Cosmetics
        'tikvahpharma',  # Tikvah Pharma
        'Thequorachannel',  # Doctors Online
        'tenamereja',  # Medical Information
        # Add more channels as needed
    ]
    
    try:
        # Connect to Telegram
        await scraper.connect()
        
        # Scrape each channel
        for channel in channels:
            logger.info(f"Processing channel: {channel}")
            try:
                messages = await scraper.scrape_channel(channel, limit=None)
                scraper.save_messages_to_datalake(messages, channel)
            except Exception as e:
                logger.error(f"Failed to scrape channel {channel}: {e}", exc_info=True)
        
        # Print summary
        summary = scraper.get_scraping_summary()
        logger.info("Scraping Summary:")
        logger.info(f"  Channels scraped: {summary['total_channels']}")
        logger.info(f"  Dates covered: {summary['total_dates']}")
        logger.info(f"  Channels: {', '.join(summary['channels_scraped'])}")
        
    except Exception as e:
        logger.error(f"Error in main scraping process: {e}", exc_info=True)
    finally:
        await scraper.client.disconnect()
        logger.info("Disconnected from Telegram")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

