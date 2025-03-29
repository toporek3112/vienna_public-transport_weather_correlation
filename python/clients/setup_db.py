import pandas as pd
import logging
from clients.events.delay import Delay
from clients.events.weather_data import WeatherData
from utils.producer_delays_checkpoint import ProducerDelaysCheckpoint
from utils.producer_weather_checkpoint import ProducerWeatherCheckpoint
from utils.database import Database

class SetupDB():
  def __init__(self):
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)
    self.stops_url = 'https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/stops.txt'
    self.stops_file = 'data/wienerlinien-ogd-haltepunkte.csv'
    self.db_table = 'stops'

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

    self.logger.info('***** Setting up stops table in database *****')
    try:
      # Try reading from URL
      df_stations = pd.read_csv(self.stops_url)
    except Exception:
      # Fallback: read from file
      df_stations = pd.read_csv(self.stops_file)

    df_stations.to_sql(self.db_table, self.engine, if_exists='replace', index=False)
    self.logger.info('Data Inserted into Table')

    # Query to select the first 10 rows from the table
    query = f"SELECT * FROM {self.db_table} LIMIT 10"
    result = pd.read_sql(query, self.engine)
    self.logger.info(f"First 10 rows from the '{self.db_table}' table:")
    self.logger.info(result)
