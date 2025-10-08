import asyncio
import random
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from dateutil import parser as dateparser

ua = UserAgent()


# ======================================
# 🔹 2. Парсинг контента отдельной статьи
# ======================================
