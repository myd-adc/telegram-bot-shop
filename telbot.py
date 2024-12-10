import telebot
from telebot import TeleBot
from settings import config
from handlers.handler_main import HandlerMain
import sys
from time import sleep  # Change time import
import signal
import requests
from telebot.apihelper import ApiTelegramException
from urllib3 import PoolManager
import socket
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import Session

def is_connection_reset_error(e):
    """Check if error is a connection reset"""
    error_str = str(e).lower()
    return any(str(code) in error_str for code in config.RETRY_CODES)

class TelBot:
    """
    Основний клас телеграм бота (сервера), в основі якого
    використовується бібліотека pyTelegramBotAPI
    """

    __version__ = config.VERSION
    __author__ = config.AUTHOR

    def __init__(self):

        self.token = config.TOKEN
        self.bot = TeleBot(self.token)
        
        # Optimize session configuration
        session = Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=config.POOL_CONNECTIONS,
            pool_maxsize=config.POOL_MAXSIZE,
            pool_block=config.POOL_BLOCK
        )
        session.mount('https://', adapter)
        self.bot.session = session
        
        # Optimize timeouts
        self.bot.threaded = True  # Enable threading
        telebot.apihelper.CONNECT_TIMEOUT = config.CONNECT_TIMEOUT
        telebot.apihelper.READ_TIMEOUT = config.READ_TIMEOUT
        
        # Configure proxy if provided in settings
        if hasattr(config, 'PROXY_URL') and config.PROXY_URL:
            from telebot import apihelper
            apihelper.proxy = {'https': config.PROXY_URL}
            print(f"Using proxy: {config.PROXY_URL}")
        
        self.handler = HandlerMain(self.bot)
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Add connection pooling
        self.http = PoolManager(
            retries=3,
            timeout=60.0,
            maxsize=10,
            backoff_factor=0.3
        )

    def shutdown(self, signum, frame):
        """Handle shutdown gracefully"""
        print("\nReceived signal to terminate. Cleaning up...")
        try:
            if hasattr(self, 'bot'):
                print("Stopping bot polling...")
                self.bot.stop_polling()
                
            if hasattr(self, 'http'):
                print("Closing HTTP connections...")
                self.http.clear()
                
            print("Shutdown complete")
            sys.exit(0)
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            sys.exit(1)

    def cleanup_session(self):
        """Clear any existing bot sessions"""
        print("Starting cleanup process...")
        retry_count = 0
        reset_count = 0
        
        while retry_count < config.MAX_RETRIES:
            try:
                # Set longer timeout for initial connection
                socket.setdefaulttimeout(config.CONNECT_TIMEOUT * 2)
                
                # Use safe_request wrapper
                self.safe_request(
                    lambda: self.bot.delete_webhook(
                        drop_pending_updates=True,
                        timeout=config.REQUEST_TIMEOUT
                    )
                )
                print("Webhook deleted successfully")
                return True
                
            except Exception as e:
                if is_connection_reset_error(e):
                    reset_count += 1
                    print(f"Connection reset (attempt {reset_count}/{config.MAX_RESET_RETRIES})")
                    if reset_count >= config.MAX_RESET_RETRIES:
                        print("Too many connection resets, will retry later...")
                        break
                    sleep(config.CONNECTION_RESET_WAIT)
                    continue
                    
                retry_count += 1
                wait_time = config.RETRY_DELAY * (2 ** retry_count)
                print(f"Cleanup error (attempt {retry_count}/{config.MAX_RETRIES}): {e}")
                if retry_count >= config.MAX_RETRIES:
                    print("Max retries reached, continuing without webhook deletion")
                    break
                sleep(wait_time)
        
        return False

    def safe_request(self, operation):
        """Execute API request with proper error handling"""
        try:
            return operation()
        except requests.exceptions.RequestException as e:
            if "Connection reset by peer" in str(e):
                raise ConnectionResetError("Connection reset by peer")
            raise

    def run_bot(self):
        print("="*50)
        print(f"Initializing bot version {self.__version__}")
        print(f"Author: {self.__author__}")
        
        retry_count = 0
        while retry_count < config.MAX_RETRIES:
            try:
                print("Starting bot polling...")
                self.cleanup_session()
                
                if not hasattr(self, '_bot_initialized'):
                    self.handler = HandlerMain(self.bot)
                    self.handler.handle()
                    self._bot_initialized = True
                    
                # Use optimized polling configuration
                self.bot.infinity_polling(
                    interval=config.POLLING_INTERVAL,
                    timeout=config.REQUEST_TIMEOUT,
                    long_polling_timeout=config.LONG_POLLING_TIMEOUT,
                    allowed_updates=["message", "callback_query"],
                    skip_pending=True  # Skip pending updates
                )
                
            except requests.exceptions.ReadTimeout as e:
                retry_count += 1
                wait_time = config.RETRY_DELAY * (2 ** retry_count)
                print(f"Read timeout error (attempt {retry_count}/{config.MAX_RETRIES}): {e}")
                print(f"Waiting {wait_time} seconds before retry...")
                sleep(wait_time)
                continue
                
            except requests.exceptions.ConnectionError as e:
                retry_count += 1
                wait_time = config.RETRY_DELAY * (2 ** retry_count)
                print(f"Connection error (attempt {retry_count}/{config.MAX_RETRIES}): {e}")
                print(f"Waiting {wait_time} seconds before retry...")
                sleep(wait_time)
                continue
                
            except Exception as e:
                retry_count += 1
                wait_time = config.RETRY_DELAY * (2 ** retry_count)
                print(f"Unexpected error (attempt {retry_count}/{config.MAX_RETRIES}): {e}")
                print(f"Waiting {wait_time} seconds before retry...")
                sleep(wait_time)
                continue
                
        if retry_count >= config.MAX_RETRIES:
            print("Max retries reached. Please check your internet connection and try again.")
            sys.exit(1)


if __name__ == "__main__":
    bot = TelBot()
    bot.run_bot()