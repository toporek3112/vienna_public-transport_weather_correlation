import pandas as pd
import logging
from clients.events.delay import Delay
from clients.events.weather_data import WeatherData
from utils.producer_delays_checkpoint import ProducerDelaysCheckpoint
from utils.producer_weather_checkpoint import ProducerWeatherCheckpoint
from utils.database import Database

class SetupDB():
  def __init__(self):
    self.logger = logging.getLogger(__name__)

    # Get the engine from the Database singleton
    self.engine = Database.get_engine()

    # Test database connection
    try:
      self.engine.connect()
      self.logger.info("Successfully connected to the database.")
    except Exception as e:
      self.logger.error(f"Error connecting to the database: {e}")
      raise e

  def run(self):
    self.logger.info('***** Setting up tables in database *****')
    Delay.metadata.create_all(self.engine)
    WeatherData.metadata.create_all(self.engine)
    ProducerDelaysCheckpoint.metadata.create_all(self.engine)
    ProducerWeatherCheckpoint.metadata.create_all(self.engine)

    routes = pd.read_csv('data/routes.txt')
    routes.to_sql("routes",self.engine, if_exists='replace', index=False)
    trips = pd.read_csv('data/trips.txt')
    trips.to_sql("trips",self.engine, if_exists='replace', index=False)
    stop_times = pd.read_csv('data/stop_times.txt')
    stop_times.to_sql("stops_times",self.engine, if_exists='replace', index=False)
    stop_shapes = pd.read_csv('data/shapes.txt')
    stop_shapes.to_sql("shapes",self.engine, if_exists='replace', index=False)
    stop_stops = pd.read_csv('data/stops.txt')
    stop_stops.to_sql("stops",self.engine, if_exists='replace', index=False)

    self.logger.info('***** Tables created *****')
