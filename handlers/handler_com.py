# імпортуємо клас-батько
from handlers.handler import Handler
from settings import config  # Correct import statement
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class HandlerCommands(Handler):
    """
    Клас обробляє вхідні команди /start та /help тощо.
    """
    def __init__(self, bot):
        super().__init__(bot)
        self.user_data = {}

    def pressed_btn_start(self, message):
        """
        обробляє вхідні /start команди
        """
        self.bot.send_message(message.chat.id,
                              f'{message.from_user.first_name},'
                              f' Привіт! Кажи, що робити!',
                              reply_markup=self.keybords.start_menu())

    def pressed_btn_choose_goods(self, message):
        """
        обробляє натискання кнопки "Вибрати товар"
        """
        self.bot.send_message(message.chat.id,
                              'Виберіть категорію товару:',
                              reply_markup=self.keybords.category_menu())

    def request_phone_number(self, message):
        """
        Запитує номер телефону у користувача
        """
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button = KeyboardButton('Надіслати номер телефону', request_contact=True)
        markup.add(button)
        self.bot.send_message(message.chat.id, 'Будь ласка, надішліть свій номер телефону:', reply_markup=markup)

    def request_delivery_city(self, message):
        """
        Запитує місто доставки у користувача
        """
        self.bot.send_message(message.chat.id, 'Будь ласка, вкажіть місто доставки:')

    def request_delivery_service(self, message):
        """
        Запитує поштову службу у користувача
        """
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Нова Пошта', 'Укр Пошта')
        self.bot.send_message(message.chat.id, 'Будь ласка, оберіть поштову службу:', reply_markup=markup)

    def request_branch(self, message):
        """
        Запитує відділення поштової служби у користувача
        """
        self.bot.send_message(message.chat.id, 'Будь ласка, вкажіть номер відділення:')

    def request_payment_method(self, message):
        """
        Запитує спосіб оплати у користувача
        """
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Накладний платіж (предоплата 200 грн)', 'Повна оплата')
        self.bot.send_message(message.chat.id, 'Будь ласка, оберіть спосіб оплати:', reply_markup=markup)

    def handle_contact(self, message):
        """
        Обробляє отримання номера телефону
        """
        self.user_data[message.chat.id]['phone_number'] = message.contact.phone_number
        self.request_delivery_city(message)

    def handle_city(self, message):
        """
        Обробляє отримання міста доставки
        """
        self.user_data[message.chat.id]['delivery_city'] = message.text
        self.request_delivery_service(message)

    def handle_delivery_service(self, message):
        """
        Обробляє отримання поштової служби
        """
        self.user_data[message.chat.id]['delivery_service'] = message.text
        self.request_branch(message)

    def handle_branch(self, message):
        """
        Обробляє отримання номера відділення
        """
        self.user_data[message.chat.id]['branch'] = message.text
        self.request_payment_method(message)

    def handle_payment_method(self, message):
        """
        Обробляє отримання способу оплати
        """
        self.user_data[message.chat.id]['payment_method'] = message.text
        self.confirm_order(message)

    def confirm_order(self, message):
        """
        Підтверджує замовлення та надсилає адміну
        """
        user_data = self.user_data[message.chat.id]
        order_details = (
            f"Деталі вашого замовлення:\n"
            f"Номер телефону: {user_data['phone_number']}\n"
            f"Місто доставки: {user_data['delivery_city']}\n"
            f"Поштова служба: {user_data['delivery_service']}\n"
            f"Номер відділення: {user_data['branch']}\n"
            f"Спосіб оплати: {user_data['payment_method']}\n"
        )
        admin_chat_id = config.ADMIN_CHAT_ID

        # Send order confirmation to user
        self.bot.send_message(message.chat.id,
                              'Ваше замовлення прийнято!',
                              reply_markup=self.keybords.start_menu())

        # Send order details to admin
        self.bot.send_message(admin_chat_id,
                              f'Нове замовлення від {message.from_user.first_name}:\n{order_details}')

        # Remove the order from the "Замовлення" section
        self.user_data.pop(message.chat.id, None)

    def handle(self):
        # обробник(декоратор) повідомлень,
        # який обробляє вхідні /start команди
        @self.bot.message_handler(commands=['start'])
        def handle(message):
            if message.text == '/start':
                self.pressed_btn_start(message)
        
        @self.bot.message_handler(func=lambda message: message.text == '📂 Вибрати товар')
        def handle_choose_goods(message):
            self.pressed_btn_choose_goods(message)
        
        @self.bot.message_handler(func=lambda message: message.text == '✅ Оформити заамовлення')
        def handle_order(message):
            self.user_data[message.chat.id] = {}
            self.request_phone_number(message)
        
        @self.bot.message_handler(content_types=['contact'])
        def handle_contact(message):
            self.handle_contact(message)
        
        @self.bot.message_handler(func=lambda message: message.chat.id in self.user_data and 'phone_number' in self.user_data[message.chat.id] and 'delivery_city' not in self.user_data[message.chat.id])
        def handle_city(message):
            self.handle_city(message)
        
        @self.bot.message_handler(func=lambda message: message.chat.id in self.user_data and 'delivery_city' in self.user_data[message.chat.id] and 'delivery_service' not in self.user_data[message.chat.id])
        def handle_delivery_service(message):
            self.handle_delivery_service(message)
        
        @self.bot.message_handler(func=lambda message: message.chat.id in self.user_data and 'delivery_service' in self.user_data[message.chat.id] and 'branch' not in self.user_data[message.chat.id])
        def handle_branch(message):
            self.handle_branch(message)
        
        @self.bot.message_handler(func=lambda message: message.chat.id in self.user_data and 'branch' in self.user_data[message.chat.id] and 'payment_method' not in self.user_data[message.chat.id])
        def handle_payment_method(message):
            self.handle_payment_method(message)
