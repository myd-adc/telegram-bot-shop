import os
from dotenv import load_dotenv
# імпортуємо модуль emoji для відображення емоджі
from emoji import emojize


load_dotenv()  # Завантаження змінних з файлу .env

# токен видається при реєстрації додатку
TOKEN = os.getenv('TOKEN')

# DEBUG = True

# назва БД
NAME_DB = os.getenv('NAME_DB')

# версія додатку
VERSION = os.getenv('VERSION')

# автор додатку
AUTHOR = os.getenv('AUTHOR')

# Admin chat ID
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# батьківська директорія
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# шлях до бази даних
DATABASE = os.path.join('sqlite:///'+BASE_DIR, NAME_DB)

COUNT = 0

# Balanced timeout settings
CONNECT_TIMEOUT = 5.0     # Connection timeout
READ_TIMEOUT = 5.0        # Read timeout
REQUEST_TIMEOUT = 5.0     # General request timeout
POLLING_INTERVAL = 0.5    # Polling interval
LONG_POLLING_TIMEOUT = 5.0  # Long polling timeout

# More reliable retry settings
MAX_RETRIES = 2           # Number of retries
RETRY_DELAY = 0.5         # Delay between retries
MAX_RESET_RETRIES = 2     # Reset retries

# Connection pooling
POOL_CONNECTIONS = 20     # Pool size
POOL_MAXSIZE = 20        # Max pool size
POOL_BLOCK = False       # Non-blocking

# Connection retry settings
RETRY_CODES = [54, 104, 110, 'reset by peer']  # Common connection reset errors
CONNECTION_RESET_WAIT = 5.0  # Wait time after connection reset

# Remove tuple timeout configuration
MAX_RETRIES_ON_ERROR = 3
RETRY_BACKOFF_FACTOR = 1.5

# Optional proxy settings (uncomment and configure if needed)
# PROXY_URL = os.getenv('PROXY_URL')
# PROXY_CONFIG = {'https': PROXY_URL} if PROXY_URL else None

# Database settings
DB_CONNECT_RETRY = 2
DB_CONNECT_TIMEOUT = 5
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# Construct database path correctly
DB_PATH = os.path.join(BASE_DIR, NAME_DB)
DATABASE = f'sqlite:///{DB_PATH}?timeout={DB_CONNECT_TIMEOUT}'

# Cache settings
CACHE_TIMEOUT = 300  # 5 minutes
MAX_CACHE_ITEMS = 1000

# кнопки керування
KEYBOARD = {
    'CHOOSE_GOODS': emojize(':open_file_folder: Вибрати товар'),
    'INFO': emojize(':speech_balloon: Про магазин'),
    'SETTINGS': emojize('⚙️ Налаштування'),
    'CLOTHES': emojize('👕 Одяг'),
    'SHOES': emojize('👟 Кросівки'),
    'ACCESSORIES': emojize('🎒 Аксесуари'),
    '<<': emojize('⏪'),
    '>>': emojize('⏩'),
    'BACK_STEP': emojize('◀️'),
    'NEXT_STEP': emojize('▶️'),
    'ORDER': emojize('✅ ЗАМОВЛЕННЯ'),
    'X': emojize('❌'),
    'DOUWN': emojize('🔽'),
    'AMOUNT_PRODUCT': COUNT,
    'AMOUNT_ORDERS': COUNT,
    'UP': emojize('🔼'),
    'APPLAY': '✅ Оформити заамовлення',
    'COPY': '©️'
}

# Ensure category IDs match keyboard entries
CATEGORY = {
    'CLOTHES': 1,
    'SHOES': 2,
    'ACCESSORIES': 3,
}

# назви команд
COMMANDS = {
    'START': "start",
    'HELP': "help",
}
