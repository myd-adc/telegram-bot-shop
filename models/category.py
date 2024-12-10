# компоненти бібліотеки для опису структури таблиці
from sqlalchemy import Column, String, Integer, Boolean

from data_base.dbcore import Base


class Category(Base):
    """
    Клас-модель для опису таблиці "Категорія товару",
    заснований на декларативному стилі SQLAlchemy
    """
    # назва таблиці
    __tablename__ = 'category'

    # поля таблиці
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    is_active = Column(Boolean)

    def __repr__(self):
        """
        Метод повертає формальне строкове представлення вказаного об'єкта
        """
        return self.name
