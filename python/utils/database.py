from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
import logging
import time
class Database:
  _instance = None

  def __new__(cls, db_url=None):
    logger = logging.getLogger(__name__)
    
    logger.info('***** Initializing Database *****')
    logger.info(f'Connection string: {db_url}')
    time.sleep(5)
    
    if cls._instance is None and db_url is not None:
      cls._instance = super(Database, cls).__new__(cls)
      cls._instance.engine = create_engine(db_url, echo=False, pool_pre_ping=True, connect_args={"connect_timeout": 10})
      cls._instance.Session = sessionmaker(bind=cls._instance.engine)
    return cls._instance

  @classmethod
  def get_engine(cls) -> Engine:
    if cls._instance is None:
      raise Exception("Database instance not initialized")
    return cls._instance.engine

  @classmethod
  def get_session(cls) -> Session:
    if cls._instance is None:
      raise Exception("Database instance not initialized")
    return cls._instance.Session()
