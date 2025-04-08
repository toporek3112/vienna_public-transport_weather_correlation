from sqlalchemy import Column, Integer, NUMERIC, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import json

Base = declarative_base()
class Delay(Base):
  # Define table schema
  __tablename__ = 'delays'
  __table_args__ = {'schema': 'public'}

  id = Column(Integer, primary_key=True)
  id_delays = Column(Integer)
  title = Column(String)
  behoben = Column(Boolean)
  lines = Column(JSONB)
  stations = Column(JSONB)
  time_start_original = Column(DateTime)
  time_start = Column(DateTime)
  time_end = Column(DateTime)
  page = Column(String)

  def __init__(self, event):
    json_event = json.loads(event)
    start_str = json_event["start"]
    end_str = json_event["end"]
    # Parse the timestamp strings to datetime objects
    start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
    end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
    
    self.time_start_original = start
    self.time_start, self.time_end = self.__assign_hour([start, end])
    self.id_delays = json_event["id"]
    self.title = json_event["title"]
    self.behoben = json_event["behoben"]
    self.lines = json_event["lines"]
    self.stations = json_event["stations"]
    self.page = json_event["page"]
  
  # set time to the nearest full hour (better visualization)
  def __assign_hour(self, datetimes):
    rounded_datetimes = []
    for dt in datetimes:
      # Round down if minutes < 30, else round up
      if dt.minute < 30:
          rounded_dt = dt.replace(minute=0)
      else:
          rounded_dt = dt.replace(minute=0) + timedelta(hours=1)
      rounded_datetimes.append(rounded_dt)
    return rounded_datetimes
