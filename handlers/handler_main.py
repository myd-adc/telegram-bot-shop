from handlers.handler_com import HandlerCommands
from handlers.handler_all_text import HandlerAllText
from handlers.handler_inline_query import HandlerInlineQuery
from telebot.handler_backends import State, StatesGroup
from settings import config
from settings.config import KEYBOARD, CATEGORY, CONNECT_TIMEOUT, READ_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from telebot.apihelper import ApiException, ApiHTTPException
import requests.exceptions
import telebot
from time import sleep  # Change time import
from collections import deque
from time import time

class HandlerMain:
    """
    Клас компонувальник
    """
    def __init__(self, bot):
        # отримуємо нашого бота
        self.bot = bot
        # Use single timeout value
        telebot.apihelper.CONNECT_TIMEOUT = config.REQUEST_TIMEOUT
        telebot.apihelper.READ_TIMEOUT = config.REQUEST_TIMEOUT
        # Optional proxy configuration
        # telebot.apihelper.PROXY = {'https':'socks5://user:password@host:port'}
        # Initialize handlers only once
        self._init_handlers()
        # Message deduplication cache
        self.message_cache = deque(maxlen=100)  # Store last 100 messages
        self.duplicate_threshold = 2  # seconds
        
    def is_duplicate_message(self, message):
        """Check if message is a duplicate"""
        message_id = f"{message.chat.id}:{message.message_id}"
        current_time = time()
        
        # Remove old messages from cache
        while self.message_cache and (current_time - self.message_cache[0][1]) > self.duplicate_threshold:
            self.message_cache.popleft()
        
        # Check if message is in cache
        for cached_id, timestamp in self.message_cache:
            if cached_id == message_id:
                return True
                
        # Add new message to cache
        self.message_cache.append((message_id, current_time))
        return False

    def _init_handlers(self):
        """Initialize handlers with state management"""
        if not hasattr(self, 'handler_commands'):
            self.handler_commands = HandlerCommands(self.bot)
            self.handler_all_text = HandlerAllText(self.bot)
            self.handler_inline_query = HandlerInlineQuery(self.bot)

    def safe_api_call(self, func, *args, **kwargs):
        """Execute API calls with retry logic and proper exception handling"""
        for attempt in range(config.MAX_RETRIES):
            try:
                # Use single timeout value
                kwargs['timeout'] = config.REQUEST_TIMEOUT
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == config.MAX_RETRIES - 1:
                    raise
                wait_time = config.RETRY_DELAY * (2 ** attempt)
                print(f"API call error (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                print(f"Retrying in {wait_time} seconds...")
                sleep(wait_time)  # Use sleep() instead of time.sleep()

    def handle(self):
        try:
            # Quick webhook deletion with reliable timeout
            self.bot.delete_webhook(
                drop_pending_updates=True,
                timeout=10
            )
            
            self.handler_commands.handle()
            self.handler_all_text.handle()
            self.handler_inline_query.handle()
            
            print("Bot initialized successfully")
            
            # More stable polling configuration
            while True:
                try:
                    self.bot.infinity_polling(
                        timeout=5,                     # Reduced timeout
                        long_polling_timeout=5,        # Matching timeout
                        interval=0.5,                  # Reduced interval
                        allowed_updates=["message", "callback_query"],
                        skip_pending=True
                    )
                except Exception as e:
                    print(f"Polling error: {e}")
                    sleep(1)  # Short delay between retries
                    continue
                    
        except Exception as e:
            print(f"Critical error: {e}")
            raise