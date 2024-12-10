import time
from telebot.apihelper import ApiException, READ_TIMEOUT
from functools import lru_cache
# імпортуємо відповідь користувачу
from settings.message import MESSAGES 
from settings import config, utility
# імпортуємо клас-батько
from handlers.handler import Handler
from settings.config import KEYBOARD, CATEGORY
from requests.exceptions import ReadTimeout

class HandlerAllText(Handler):
    """
    Клас обробляє вхідні текстові повідомлення від натискання на кнопки
    """
    def __init__(self, bot):
        super().__init__(bot)
        # крок в замовленні 
        self.step = 0
        self._message_cache = set()
        self.max_retries = 3
        self.retry_delay = 5
        self.timeout = 15  # Reduce timeout
        # Fix: use consistent naming for keyboard
        self.keyboard = self.keybords  # Add this line to alias keybords as keyboard
        self.message_cache = set()  # For duplicate detection
        self.last_message_time = {}  # Track message timing
        self.product_cache = {}  # Cache for products
        self.category_cache = {}  # Cache for categories

    def safe_send_message(self, chat_id, text, **kwargs):
        """Safely send message with retries and increased timeout"""
        kwargs['timeout'] = self.timeout
        for attempt in range(self.max_retries):
            try:
                return self.bot.send_message(chat_id, text, **kwargs)
            except (ApiException, ReadTimeout) as e:
                print(f"Message send error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    print("Failed to send message after maximum retries")
                    raise
                time.sleep(self.retry_delay)

    def is_duplicate_message(self, message):
        """Check if message is a duplicate within timeframe"""
        msg_id = f"{message.chat.id}:{message.text}"
        current_time = time.time()
        
        # Remove old messages
        self.message_cache = {
            m for m in self.message_cache 
            if current_time - self.last_message_time.get(m, 0) < 2
        }
        
        if msg_id in self.message_cache:
            return True
            
        self.message_cache.add(msg_id)
        self.last_message_time[msg_id] = current_time
        return False

    def pressed_btn_category(self, message):
        """
        Обробка події натискання кнопки категорії товару
        """
        if self.is_duplicate_message(message):
            return
            
        try:
            for category, keyboard_text in [
                ('CLOTHES', config.KEYBOARD['CLOTHES']),
                ('SHOES', config.KEYBOARD['SHOES']),
                ('ACCESSORIES', config.KEYBOARD['ACCESSORIES'])
            ]:
                if message.text == keyboard_text:
                    self.safe_send_message(
                        message.chat.id,
                        f"Ви вибрали категорію {keyboard_text.split()[1]}", # Get category name
                        reply_markup=self.keybords.set_select_category(config.CATEGORY[category])
                    )
                    return
                    
        except Exception as e:
            print(f"Error in category selection: {e}")
            self.safe_send_message(message.chat.id, "Помилка з'єднання. Спробуйте ще раз.")

    def pressed_btn_info(self, message):
        """
        Обробка події натискання на кнопку 'Про магазин'
        """
        self.bot.send_message(message.chat.id, MESSAGES['trading_store'],
                              parse_mode="HTML",
                              reply_markup=self.keybords.info_menu())

    def pressed_btn_settings(self, message):
        """
        Обробка події натискання на кнопку 'Налаштування'
        """
        self.bot.send_message(message.chat.id, MESSAGES['settings'],
                              parse_mode="HTML",
                              reply_markup=self.keybords.settings_menu())

    def pressed_btn_back(self, message):
        """
        Обробка події натискання на кнопку 'Назад'
        """
        self.bot.send_message(message.chat.id, "Ви повернулись назад",
                            reply_markup=self.keybords.start_menu())

    def pressed_btn_product(self, message, product):
        """
        Обробка події натискання на кнопку 'Вибрати товар'
        """
        self.bot.send_message(
            message.chat.id, 
            'Категорія ' + config.KEYBOARD[product],
            reply_markup=self.keybords.set_select_category(config.CATEGORY[product])
        )
        # Removed redundant "Ок" message
        # Show available products immediately
        self.show_category_products(message, config.CATEGORY[product])

    @lru_cache(maxsize=100)
    def get_category_products(self, category_id):
        """Cache category products"""
        return self.BD.select_all_products_category(category_id)
        
    def show_category_products(self, message, category_id):
        """Optimized product display"""
        if category_id not in self.category_cache:
            self.category_cache[category_id] = self.get_category_products(category_id)
            
        products = self.category_cache[category_id]
        if products:
            self.safe_send_message(
                message.chat.id,
                "Доступні товари:",
                reply_markup=self.keybords.products_keyboard(products)
            )
        else:
            self.safe_send_message(
                message.chat.id,
                "В даній категорії товари відсутні",
                reply_markup=self.keybords.category_menu()
            )

    def pressed_btn_order(self, message):
        """
        Обробляє вхідні текстові повідомлення від натискання на кнопку 'Замовлення'.
        """
        # обнуляємо дані кроку
        self.step = 0
        # отримуємо список всіх товарів в замовленні
        count = self.BD.select_all_product_id()
        # отримуємо кількість в кожній позиції товару в замовленні
        quantity = self.BD.select_order_quantity(count[self.step])

        # надсилаємо відповідь користувачу
        self.send_message_order(count[self.step], quantity, message)

    def send_message_order(self, product_id, quantity, message):
        """
        Надсилає відповідь користувачу при виконанні різних дій
        """
        self.bot.send_message(message.chat.id,MESSAGES['order_number'].format(
            self.step+1), parse_mode="HTML")
        self.bot.send_message(message.chat.id,
                              MESSAGES['order'].
                              format(self.BD.select_single_product_name(
                                  product_id),
                                     self.BD.select_single_product_title(
                                         product_id),
                                     self.BD.select_single_product_price(
                                         product_id),
                                     self.BD.select_order_quantity(
                                         product_id)),
                              parse_mode="HTML",
                              reply_markup=self.keybords.orders_menu(
                                  self.step, quantity))

    def pressed_btn_up(self, message):
        """
        Обробка натискання кнопки збільшення
        кількості певного товару в замовленні
        """
        # отримуємо список всіх товарів в замовленні
        count = self.BD.select_all_product_id()
        # отримуємо кількість конкретної позиції в замовленні
        quantity_order = self.BD.select_order_quantity(count[self.step])
        # отримуємо кількість конкретної позиції в продуктах
        quantity_product = self.BD.select_single_product_quantity(
            count[self.step])
        # якщо товар є
        if quantity_product > 0:
            quantity_order += 1
            quantity_product -= 1
            # вносим изменения в БД orders
            self.BD.update_order_value(count[self.step],
                                       'quantity', quantity_order)
            # вносим изменения в БД product
            self.BD.update_product_value(count[self.step],
                                         'quantity', quantity_product)
        # отправляем ответ пользователю
        self.send_message_order(count[self.step], quantity_order, message)

    def pressed_btn_douwn(self, message):
        """
        Обработка нажатия кнопки уменьшения
        количества определенного товара в заказе
        """
        # получаем список всех товаров в заказе
        count = self.BD.select_all_product_id()
        # получаем количество конкретной позиции в заказе
        quantity_order = self.BD.select_order_quantity(count[self.step])
        # получаем количество конкретной позиции в пролуктов
        quantity_product = self.BD.select_single_product_quantity(
            count[self.step])
        # если товар в заказе есть
        if quantity_order > 0:
            quantity_order -= 1
            quantity_product += 1
            # вносим изменения в БД orders
            self.BD.update_order_value(count[self.step],
                                       'quantity', quantity_order)
            # вносим изменения в БД product
            self.BD.update_product_value(count[self.step],
                                         'quantity', quantity_product)
        # отправляем ответ пользователю
        self.send_message_order(count[self.step], quantity_order, message)

    def pressed_btn_x(self, message):
        """
        Обработка нажатия кнопки удаления
        товарной позиции заказа
        """
        # получаем список всех product_id заказа
        count = self.BD.select_all_product_id()
        # если список не пуст
        if count.__len__() > 0:
            # получаем количество конкретной позиции в заказе
            quantity_order = self.BD.select_order_quantity(count[self.step])
            # получаем количество товара к конкретной
            # позиции заказа для возврата в product
            quantity_product = self.BD.select_single_product_quantity(
                count[self.step])
            quantity_product += quantity_order
            # вносим изменения в БД orders
            self.BD.delete_order(count[self.step])
            # вносим изменения в БД product
            self.BD.update_product_value(count[self.step],
                                         'quantity', quantity_product)
            # уменьшаем шаг
            self.step -= 1

        count = self.BD.select_all_product_id()
        # если список не пуст
        if count.__len__() > 0:

            quantity_order = self.BD.select_order_quantity(count[self.step])
            # отправляем пользователю сообщение
            self.send_message_order(count[self.step], quantity_order, message)

        else:
            # если товара нет в заказе отправляем сообщение
            self.bot.send_message(message.chat.id, MESSAGES['no_orders'],
                                  parse_mode="HTML",
                                  reply_markup=self.keybords.category_menu())

    def pressed_btn_back_step(self, message):
        """
        Обработка нажатия кнопки перемещения
        к более ранним товарным позициям заказа
        """
        # уменьшаем шаг пока шаг не будет равет "0"
        if self.step > 0:
            self.step -= 1
        # получаем список всех товаров в заказе
        count = self.BD.select_all_product_id()
        quantity = self.BD.select_order_quantity(count[self.step])

        # отправляем ответ пользователю
        self.send_message_order(count[self.step], quantity, message)

    def pressed_btn_next_step(self, message):
        """
        Обработка нажатия кнопки перемещения
        к более поздним товарным позициям заказа
        """
        # увеличиваем шаг пока шаг не будет равет количеству строк
        # полей заказа с расчетом цены деления начиная с "0"
        if self.step < self.BD.count_rows_order() - 1:
            self.step += 1
        # получаем список всех товаров в заказе
        count = self.BD.select_all_product_id()
        # получаем еоличество конкретного товара в соответствие с шагом выборки
        quantity = self.BD.select_order_quantity(count[self.step])

        # отправляем ответ пользователю
        self.send_message_order(count[self.step], quantity, message)

    def pressed_btn_apllay(self, message):
        """
        обрабатывает входящие текстовые сообщения
        от нажатия на кнопку 'Оформить заказ'.
        """
        # отправляем ответ пользователю
        self.bot.send_message(message.chat.id,
                              MESSAGES['applay'].format(
                                  utility.get_total_coas(self.BD),

                                  utility.get_total_quantity(self.BD)),
                              parse_mode="HTML",
                              reply_markup=self.keybords.category_menu())
        # отчищаем данные с заказа
        self.BD.delete_all_order()

    def handle_category_selection(self, message):
        """
        Обробляє вибір категорії товару
        """
        category_name = message.text.split(' ')[-1]  # Extract category name from message
        products = self.BD.select_all_products_category(category_name)
        
        if not products:
            self.bot.send_message(message.chat.id,
                                  f'В даній категорії товари відсутні',
                                  reply_markup=self.keybords.category_menu())
        else:
            # Handle case where products are available
            self.bot.send_message(message.chat.id,
                                  f'Категорія {category_name}',
                                  reply_markup=self.keybords.set_select_category(category_name))

    def handle(self):
        # обработчик(декоратор) сообщений,
        # который обрабатывает входящие текстовые сообщения от нажатия кнопок.
        @self.bot.message_handler(func=lambda message: True)
        def handle(message):
            # ********** меню ********** #

            if message.text == config.KEYBOARD['CHOOSE_GOODS']:
                self.pressed_btn_category(message)

            if message.text == config.KEYBOARD['INFO']:
                self.pressed_btn_info(message)

            if message.text == config.KEYBOARD['SETTINGS']:
                self.pressed_btn_settings(message)

            if message.text == config.KEYBOARD['<<']:
                self.pressed_btn_back(message)

            if message.text == config.KEYBOARD['ORDER']:
                # если есть заказ
                if self.BD.count_rows_order() > 0:
                    self.pressed_btn_order(message)
                else:
                    self.bot.send_message(message.chat.id,
                                          MESSAGES['no_orders'],
                                          parse_mode="HTML",
                                          reply_markup=self.keybords.
                                          category_menu())

            # ********** меню (категорії товару, Одяг, Кросівки, Аксесуари)******
            if message.text == config.KEYBOARD['CLOTHES']:
                self.pressed_btn_product(message, 'CLOTHES')

            if message.text == config.KEYBOARD['SHOES']:
                self.pressed_btn_product(message, 'SHOES')

            if message.text == config.KEYBOARD['ACCESSORIES']:
                self.pressed_btn_product(message, 'ACCESSORIES')

            # ********** меню (Заказа)**********

            if message.text == config.KEYBOARD['UP']:
                self.pressed_btn_up(message)

            if message.text == config.KEYBOARD['DOUWN']:
                self.pressed_btn_douwn(message)

            if message.text == config.KEYBOARD['X']:
                self.pressed_btn_x(message)

            if message.text == config.KEYBOARD['BACK_STEP']:
                self.pressed_btn_back_step(message)

            if message.text == config.KEYBOARD['NEXT_STEP']:
                self.pressed_btn_next_step(message)

            if message.text == config.KEYBOARD['APPLAY']:
                self.pressed_btn_apllay(message)
            else:
                self.bot.send_message(message.chat.id, message.text)

        @self.bot.message_handler(func=lambda message: message.text in ['👕 Одяг', '👟 Кросівки', '🎒 Аксесуари'])
        def handle_category(message):
            self.handle_category_selection(message)