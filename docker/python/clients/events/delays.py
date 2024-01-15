from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import json

Base = declarative_base()

# Define the delays table
class Delay(Base):
  # Define table schema
  __tablename__ = 'delays'
  __table_args__ = {'schema': 'public'}
  id = Column(Integer, primary_key=True)
  id_delays = Column(Integer, primary_key=True)
  title = Column(String)
  behoben = Column(Boolean)
  lines = Column(JSON)
  stations = Column(JSON)
  time_start_original = Column(DateTime)
  time_start = Column(DateTime)
  time_end = Column(DateTime)

  def __init__(self, event):
    event_json = json.loads(event)
    start_str = event_json["start"]
    end_str = event_json["end"]
    # Parse the timestamp strings to datetime objects
    start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
    end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
    
    self.time_start_original = start
    self.time_start, self.time_end = self.assign_hour([start, end])
    self.id_delays = event_json.get("id", None)
    self.title = event_json.get("title", None)
    self.behoben = event_json.get("behoben", None)
    self.lines = event_json.get("lines", [])
    self.stations = event_json.get("stations", [])
  
  # set time to the nearest full hour (better visualization)
  def assign_hour(self, datetimes):
    rounded_datetimes = []
    for dt in datetimes:
      # Round down if minutes < 30, else round up
      if dt.minute < 30:
          rounded_dt = dt.replace(minute=0)
      else:
          rounded_dt = dt.replace(minute=0) + timedelta(hours=1)
      rounded_datetimes.append(rounded_dt)
    return rounded_datetimes
  

