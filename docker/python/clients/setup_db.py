import pandas as pd
import os
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
    self.file_name = 'data/wienerlinien-ogd-haltepunkte.csv'
    self.db_table = os.getenv('DB_TABLE')

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
    self.logger.info('***** Setting up tables in dsi_projekt database *****')
    Delay.metadata.create_all(self.engine)
    WeatherData.metadata.create_all(self.engine)
    ProducerDelaysCheckpoint.metadata.create_all(self.engine)
    ProducerWeatherCheckpoint.metadata.create_all(self.engine)

    self.logger.info('***** Setting up stops table in dsi_projekt database *****')
    df_stations = pd.read_csv(self.file_name, sep=';', usecols=[0,2,5,6], names=['id','name','longitude','latitude'], header=0)
    df_stations = df_stations.dropna()
    df_stations = df_stations.drop_duplicates('name')

    df_stations.to_sql(self.db_table, self.engine, if_exists='replace', index=False)
    self.logger.info('Data Inserted into Table')

    # Query to select the first 10 rows from the table
    query = "SELECT * FROM stops LIMIT 10"
    result = pd.read_sql(query, self.engine)
    self.logger.info(f"First 10 rows from the '{self.db_table}' table:")
    self.logger.info(result)
