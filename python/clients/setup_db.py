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
    self.stops_url = 'https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/stops.txt'
    self.stops_file = 'data/stops.txt'
    self.db_table_stops = 'stops'

    self.shapes_url = 'https://www.wienerlinien.at/ogd_realtime/doku/ogd/gtfs/shapes.txt'
    self.shapes_file = 'data/shapes.txt'
    self.db_table_shapes = 'shapes'

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
    self._load_stops()
    self._load_shapes()

  def _load_stops(self):
    self.logger.info('***** Setting up stops table in database *****')
    try:
      # Try reading from URL
      df_stops = pd.read_csv(self.stops_url)
    except Exception:
      # Fallback: read from file
      df_stops = pd.read_csv(self.stops_file)

    df_stops.columns = ["id", "name", "latitude", "longitude", "zone_id"]
    df_stops.to_sql(self.db_table_stops, self.engine, if_exists='replace', index=False)
    self.logger.info('Data Inserted into Table')

    # Query to select the first 10 rows from the table
    query = f"SELECT * FROM {self.db_table_stops} LIMIT 10"
    result = pd.read_sql(query, self.engine)
    self.logger.info(f"First 10 rows from the '{self.db_table_stops}' table:")
    self.logger.info(result)

  def _load_shapes(self):
    self.logger.info('***** Setting up shapes table in database *****')
    try:
      # Try reading from URL
      df_shapes = pd.read_csv(self.shapes_url)
    except Exception:
      # Fallback: read from file
      df_shapes = pd.read_csv(self.shapes_file)

    # rename columns 
    df_shapes.columns = ["id", "latitude", "longitude", "sequence", "shape_dist_traveled"]

    # Filter for lines with 'H' in the ID indicating the line direction
    # H = Hin, R = Retour (just an assumption)
    df_shapes_filtered = df_shapes[df_shapes['id'].str.contains(r'.*H', regex=True)].copy()

    # Extract version and line from the ID
    df_shapes_filtered['version'] = df_shapes_filtered['id'].str.extract(r'-j25-(.*)\.H').astype(float)
    df_shapes_filtered['line'] = df_shapes_filtered['id'].str.extract(r'^[^-]+-([^-]+)-')

    # Get row count per id, version, and line
    rows_count = df_shapes_filtered.groupby(['id', 'version', 'line']).size().reset_index(name='count')
    df_shapes_clean = rows_count.sort_values(
                                by=['line', 'count', 'version'],
                                ascending=[True, False, False]
                              ).groupby('line').head(1)

    # Save to DB
    df_shapes_filtered[df_shapes_filtered['id'].isin(df_shapes_clean['id'])].to_sql(self.db_table_shapes, self.engine, if_exists='replace', index=False)
    self.logger.info('Data Inserted into Table')

    # Show preview
    query = f"SELECT * FROM {self.db_table_shapes} LIMIT 10"
    result = pd.read_sql(query, self.engine)
    self.logger.info(f"First 10 rows from the '{self.db_table_shapes}' table:")
    self.logger.info(f"\n{result}")
