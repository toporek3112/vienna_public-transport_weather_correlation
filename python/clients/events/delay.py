from sqlalchemy import Column, Integer, NUMERIC, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
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
    start_str = event["start"]
    end_str = event["end"]
    # Parse the timestamp strings to datetime objects
    start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
    end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
    
    self.time_start_original = start
    self.time_start, self.time_end = self.assign_hour([start, end])
    self.id_delays = event["id"]
    self.title = event["title"]
    self.behoben = event["behoben"]
    self.lines = event["lines"]
    self.stations = event["stations"]
    self.page = event["page"]
  
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
  
  def to_json(self):
    return json.dumps({
      "id": self.id_delays,
      "title": self.title,
      "behoben": self.behoben,
      "lines": self.lines,
      "stations": self.stations,
      "start": self.time_start_original.strftime('%d.%m.%Y %H:%M'),
      "end": self.time_end.strftime('%d.%m.%Y %H:%M'),
      "page": self.page
    })