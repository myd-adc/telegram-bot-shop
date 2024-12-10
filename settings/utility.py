# конвертує список з p[(5,),(8,),...] до [5,8,...]
def _convert(list_convert):
    return [itm[0] for itm in list_convert]


# обчислює загальну суму замовлення і повертає результат
def total_coast(list_quantity, list_price):
    order_total_cost = 0
    for ind, itm in enumerate(list_price):
        order_total_cost += list_quantity[ind] * list_price[ind]
    return order_total_cost


# обчислює загальну кількість замовленої одиниці товару і повертає результат
def total_quantity(list_quantity):
    order_total_quantity = 0
    for itm in list_quantity:
        order_total_quantity += itm
    return order_total_quantity


def get_total_coas(BD):
    """
    Повертає загальну вартість товару
    """
    # отримуємо список всіх product_id замовлення
    all_product_id = BD.select_all_product_id()
    # отримуємо список вартості по всіх позиціях замовлення у вигляді звичайного списку
    all_price = [BD.select_single_product_price(itm) for itm in all_product_id]
    # отримуємо список кількості по всіх позиціях замовлення у вигляді звичайного списку
    all_quantity = [BD.select_order_quantity(itm) for itm in all_product_id]
    # Повертає загальну вартість товару
    return total_coast(all_quantity,all_price)


def get_total_quantity(BD):
    """
    Повертає загальну кількість замовленої одиниці товару
    """
    # отримуємо список всіх product_id замовлення
    all_product_id = BD.select_all_product_id()
    # отримуємо список кількості по всіх позиціях замовлення у вигляді звичайного списку
    all_quantity = [BD.select_order_quantity(itm) for itm in all_product_id]
    # Повертає кількість товарних позицій
    return total_quantity(all_quantity)