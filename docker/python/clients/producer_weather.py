from kafka import KafkaProducer, KafkaConsumer
from datetime import date, datetime
import json
import os
import time
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import logging

class ProducerWeather():
    def __init__(self):
      # Inizialize logger
      logging.basicConfig(level=logging.INFO)
      self.logger = logging.getLogger(__name__)

      self.source_url = os.getenv('SOURCE_URL')
      self.kafka_host = os.getenv('KAFKA_HOST')
      self.kafka_topic = os.getenv('KAFKA_TOPIC')
      self.kafka_delays_topic = os.getenv('KAFKA_INTERRUPTION_TOPIC')
      self.cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
      self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
      self.openmeteo = openmeteo_requests.Client(session = self.retry_session)

      self.producer = KafkaProducer(
          bootstrap_servers=self.kafka_host,
          value_serializer=lambda v: json.dumps(v).encode('utf-8')
      )
      self.consumer = KafkaConsumer(
          self.kafka_delays_topic,
          bootstrap_servers=self.kafka_host,
          value_deserializer=lambda m: json.loads(m.decode('utf-8')),
          group_id='producer_weather'
      )

      self.checkpoint_file_path = 'checkpoint_weather.txt'
      
      # Default value if the file doesn't exist or is empty/invalid
      self.latest_requested_date = date.min
      # If the file doesn't exist, log and use the default value
      if not os.path.exists(self.checkpoint_file_path):
          self.logger.info(f'Checkpoint file not found. Using default latest_requested_date: {self.latest_requested_date}')
          return
      # Try reading the file
      try:
          with open(self.checkpoint_file_path, 'r') as file:
              file_content = file.read().strip()
          # If the file is empty, log and use the default value
          if not file_content:
              self.logger.info(f'Empty checkpoint file. Using default latest_requested_date: {self.latest_requested_date}')
              return
          # Try converting the content to a datetime object
          self.latest_requested_date = date.fromisoformat(file_content)
          self.logger.info(f'Using latest_requested_date: {self.latest_requested_date}')
      except ValueError:
          self.logger.info(f'Invalid checkpoint file. Using default latest_requested_date: {self.latest_requested_date}')


      self.logger.info('Initializing Weather Producer')
      self.logger.info(f'Source Url: {self.source_url}')
      self.logger.info(f'Kafka Host: {self.kafka_host}')
      self.logger.info(f'Weather Topic (Write): {self.kafka_topic}')
      self.logger.info(f'Delays Topic (Read): {self.kafka_delays_topic}')

    def __listen_for_delays(self):
      self.logger.info("*** Listening for interruption events from Kafka ***")
    
      batch_size = 20
      batch_timeout = 35  # in seconds
      batch = []
      start_time = time.time()

      # Listen for new messages on the interruption topic
      for message in self.consumer:
        batch.append(message.value)  # Assuming message.value contains the interruption event details
        current_time = time.time()

        # Check if batch size is reached or timeout has occurred
        if len(batch) >= batch_size or (current_time - start_time) >= batch_timeout:
          self.logger.info(f'Recived batch of {len(batch)} events')

          # Convert to DataFrame
          df_batch = pd.DataFrame(batch)
          df_batch['start'] = pd.to_datetime(df_batch['start'], format='%d.%m.%Y %H:%M')
          df_batch['end'] = pd.to_datetime(df_batch['end'], format='%d.%m.%Y %H:%M')
          yield df_batch
          
          batch = []  # Reset batch
          start_time = time.time()  # Reset start time for the new batch

      # After exiting the loop, if there are any remaining messages in the batch, yield them
      if batch:
        # Convert to DataFrame
        df_batch = pd.DataFrame(batch)
        df_batch['start'] = pd.to_datetime(df_batch['start'], format='%d.%m.%Y %H:%M')
        df_batch['end'] = pd.to_datetime(df_batch['end'], format='%d.%m.%Y %H:%M')
        yield df_batch

    def __fetch_weather(self, date_time):
      date_frame = [date_time[0], date_time[-1]]

      self.logger.info(f'Fetching weather data for dates from {date_frame[0]} to {date_frame[1]}')
      api_params = {
	        "latitude": 48.210033,
	        "longitude": 16.363449,
	        "start_date": date_time[0],
	        "end_date": date_time[-1],
	        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
      }

      responses = self.openmeteo.weather_api(self.source_url, params=api_params)
      response = responses[0]
      hourly = response.Hourly()
      hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
      hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
      hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
      #create dataframe
      hourly_data = {"time": pd.date_range(
      	start = pd.to_datetime(hourly.Time(), unit = "s"),
      	end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
      	freq = pd.Timedelta(seconds = hourly.Interval()),
      	inclusive = "left"
      )}
      hourly_data["temperature_2m"] = hourly_temperature_2m
      hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
      hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
      hourly_dataframe = pd.DataFrame(data = hourly_data)
      #coonvert timestamps into correct format
      hourly_dataframe["time"]=hourly_dataframe["time"].dt.strftime('%d/%m/%y %H:%M:%S.%f')

      return hourly_dataframe
        
    def __write_weather_to_kafka(self, df_weather):
      self.logger.info('Writing weather data into kafka')
      for index, row in df_weather.iterrows():
        # Convert the row to JSON format
        row_as_json_string = row.to_json()
        row_json = json.loads(row_as_json_string)
        # Send the row as a message to Kafka
        self.producer.send(self.kafka_topic, value=row_json)

    def __check_if_weather_already_requested(self, latest_date):
      self.logger.info(f'Latest requested date is {self.latest_requested_date}')
      already_requested = True
      
      # Check if the latest_date is later than the latest_requested_date

      if latest_date > self.latest_requested_date:
          self.logger.info(f'Saving date {latest_date} to checkpoint_weather.txt file')
          already_requested = False
          with open(self.checkpoint_file_path, 'w') as file:
              file.write(latest_date.isoformat())
      
      return already_requested

    def run(self):
      self.logger.info('***** Starting Weather Producer *****')
      try:
        # Listen for interruption events
        for df_event_batch in self.__listen_for_delays():
          # Get the latest date from the DataFrame
          latest_date = df_event_batch['start'].max().date()
          self.logger.info(f'Event batch latest date is {latest_date}')

          already_requested = self.__check_if_weather_already_requested(latest_date)
          
          if not already_requested:
            df_weather = self.__fetch_weather([self.latest_requested_date, latest_date])
            self.latest_requested_date = latest_date
            self.__write_weather_to_kafka(df_weather)

          else:
             self.logger.info('Date frame for weather data already requested. Skipping...')
      except Exception as e:
        self.logger.error(e)
      finally:
        # Close the producer and consumer, ensuring it's done regardless of how the while loop exits
        self.logger.info('***** Closing Kafka producer and consumer *****')
        self.producer.close()
        self.consumer.close()
        self.logger.info('***** EXITING *****')

# debug = Producer_Weather()
# debug.run()