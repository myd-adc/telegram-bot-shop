from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os
from settings import config
import time

class Singleton(type):
    """Патерн Singleton для підключення до БД"""
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DBManager(metaclass=Singleton):
    def __init__(self):
        self.engine = create_engine(
            config.DATABASE,
            echo=False,
            pool_size=10,  # Increase pool size
            max_overflow=20,  # Allow more connections
            pool_pre_ping=True,
            pool_recycle=300,  # Reduce recycle time to 5 minutes
            connect_args={'timeout': 10}  # Reduce timeout
        )
        self.Session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False  # Prevent unnecessary db hits
        )
        self._session = self.Session()
        
    def get_session(self):
        try:
            self._session.execute('SELECT 1')  # Quick connection test
            return self._session
        except:
            self._session = self.Session()
            return self._session

Base = declarative_base()
