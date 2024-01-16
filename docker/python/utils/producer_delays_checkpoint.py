from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, NUMERIC, TIMESTAMP, Boolean
from utils.database import Database
import logging

Base = declarative_base()

class ProducerDelaysCheckpoint(Base):
  __tablename__ = 'producer_delays_checkpoint'
  id = Column(Integer, primary_key=True)
  page = Column(NUMERIC)
  behoben = Column(Boolean)
  delay_id = Column(NUMERIC)
  last_scrape_time = Column(TIMESTAMP)

  def __init__(self):
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)

  def get_checkpoint(self):
    session = Database.get_session()
    self.logger.info('Fetching delays producer checkpoint from database')
    latest_checkpoint = session.query(self.__class__).order_by(self.__class__.id.desc()).first()
    if latest_checkpoint:
      return latest_checkpoint
    else:
      checkpoint = ProducerDelaysCheckpoint()
      checkpoint.id = 0
      checkpoint.page = 0
      checkpoint.behoben = False
      checkpoint.delay_id = 0
      checkpoint.last_scrape_time = 0
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