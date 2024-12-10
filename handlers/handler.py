# імпортуємо бібліотеку abc для реалізації абстрактних класів
import abc
# імпортуємо розмітку клавіатури та клавіш
from markup.markup import Keyboards
# імпортуємо клас-менеджер для роботи з бібліотекою
from data_base.dbalchemy import DBManager


class Handler(metaclass=abc.ABCMeta):

    def __init__(self, bot):
        # отримуємо об'єкт бота
        self.bot = bot
        # ініціалізуємо розмітку кнопок
        self.keybords = Keyboards()
        # ініціалізуємо менеджер для роботи з БД
        self.BD = DBManager()

    @abc.abstractmethod
    def handle(self):
        pass
