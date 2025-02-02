# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
    MARKET_TIMEZONE = 'Asia/Riyadh'
    REPORT_FREQUENCY = os.getenv('REPORT_FREQUENCY', 'daily')
