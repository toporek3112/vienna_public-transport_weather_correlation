from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

class Database:
  _instance = None

  def __new__(cls, db_url=None):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info('***** Initializing Database *****')
    logger.info(f'Connection string: {db_url}')
    
    if cls._instance is None and db_url is not None:
      cls._instance = super(Database, cls).__new__(cls)
      cls._instance.engine = create_engine(db_url)
      cls._instance.Session = sessionmaker(bind=cls._instance.engine)
    return cls._instance

  @classmethod
  def get_engine(cls):
    if cls._instance is None:
      raise Exception("Database instance not initialized")
    return cls._instance.engine

  @classmethod
  def get_session(cls):
    if cls._instance is None:
      raise Exception("Database instance not initialized")
    return cls._instance.Session()
