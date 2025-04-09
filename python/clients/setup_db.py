import pandas as pd
import logging
import gzip
import shutil
import os
import subprocess
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

    self.load_db_from_gz()

    self.logger.info('***** Tables created *****')

  def load_db_from_gz(self):
    # Unzip the SQL file
    here = os.path.dirname(os.path.abspath(__file__))  # points to clients/
    gz_file = os.path.join(here, '..', 'data', 'db.sql.gz')
    sql_file = os.path.join(here, '..', 'data', 'db.sql')

    self.logger.info("Unzipping SQL file...")
    with gzip.open(gz_file, 'rb') as f_in, open(sql_file, 'wb') as f_out:
      shutil.copyfileobj(f_in, f_out)

    # Step 2: Restore via psql
    # Adjust the connection parameters below (host, user, dbname, etc.)
    self.logger.info("Running psql to restore the database dump...")
    env = os.environ.copy()
    env["PGPASSWORD"] = "postgres"
    subprocess.run(
      [
        'psql',
        '-h', 'vptwc_postgres',
        '-p', '5432',
        '-U', 'postgres',
        '-d', 'vptwc_project',
        '-f', sql_file
      ],
      check=True,
      env=env
    )
    self.logger.info("Database dump restored successfully.")

    self.logger.info("SQL file loaded successfully.")

  def __initial_wl(self):
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
