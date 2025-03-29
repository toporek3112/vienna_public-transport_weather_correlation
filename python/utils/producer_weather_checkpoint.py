from sqlalchemy import Column, Integer, Date
from sqlalchemy.ext.declarative import declarative_base
from utils.database import Database
from datetime import date
import logging

Base = declarative_base()

class ProducerWeatherCheckpoint(Base):
  __tablename__ = 'producer_weather_checkpoint'
  id = Column(Integer, primary_key=True)
  date = Column(Date)

  def __init__(self):
   logging.basicConfig(level=logging.INFO)
   self.logger = logging.getLogger(__name__)

  def get_checkpoint(self):
    session = Database.get_session()

    self.logger.info('Fetching weather producer checkpoint from database')
    latest_checkpoint = session.query(self.__class__).order_by(self.__class__.id.desc()).first()
    if latest_checkpoint:
      return latest_checkpoint
    else:
      checkpoint = ProducerWeatherCheckpoint()
      checkpoint.date = None
      return checkpoint
      
  
  def save_checkpoint(self, checkpoint):
    # Get the session from the singleton Database instance
    session = Database.get_session()
    try:
        new_checkpoint = checkpoint
        session.merge(new_checkpoint)
        session.commit()
        self.logger.info("Checkpoint saved successfully.")
    except Exception as e:
        self.logger.info(f"An error occurred while saving the checkpoint: {e}")
        session.rollback()