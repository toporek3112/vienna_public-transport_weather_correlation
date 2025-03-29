from sqlalchemy import Column, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

# Define the weather_data table
class WeatherData(Base):
  __tablename__ = 'weather_data'
  __table_args__ = {'schema': 'public'}
  id = Column(Integer, primary_key=True)
  time = Column(DateTime)
  temperature_2m = Column(Float)
  relative_humidity_2m = Column(Float)
  wind_speed_10m = Column(Float)

  def __init__(self, event):
    event_json = json.loads(event)

    time_str = event_json["time"]

    self.time = datetime.strptime(time_str, '%d/%m/%y %H:%M:%S.%f')
    self.temperature_2m = event_json["temperature_2m"]
    self.relative_humidity_2m = event_json["relative_humidity_2m"]
    self.wind_speed_10m = event_json["wind_speed_10m"]