from kafka import KafkaProducer, KafkaConsumer
from utils.producer_weather_checkpoint import ProducerWeatherCheckpoint
from datetime import date, timedelta
from retry_requests import retry
import openmeteo_requests
import requests_cache
import pandas as pd
import json
import sys
import os
import time
import logging

class ProducerWeather():
    def __init__(self):
      # Inizialize logger
      self.logger = logging.getLogger(__name__)

      self.source_url = os.getenv('SOURCE_URL')
      self.kafka_host = os.getenv('KAFKA_HOST')
      self.kafka_topic = os.getenv('KAFKA_TOPIC')
      self.kafka_delays_topic = os.getenv('KAFKA_INTERRUPTION_TOPIC')

      self.cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
      self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
      self.openmeteo = openmeteo_requests.Client(session = self.retry_session)

      # Retry mechanism for Kafka connection
      max_retries = 5
      retry_count = 0
      while retry_count < max_retries:
        try:
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
          break
        except Exception as e:
            self.logger.warning(f"Attempt {retry_count + 1} failed to connect Kafka Producer: {e}")
            time.sleep(5)  # wait for 5 seconds before next attempt
            retry_count += 1

        if retry_count == max_retries:
          self.logger.error("Failed to connect to Kafka after multiple attempts.")
          sys.exit(1)

      self.db = ProducerWeatherCheckpoint()
      
      self.checkpoint = self.db.get_checkpoint()

      self.logger.info('Initializing Weather Producer')
      self.logger.info(f'Source Url: {self.source_url}')
      self.logger.info(f'Kafka Host: {self.kafka_host}')
      self.logger.info(f'Weather Topic (Write): {self.kafka_topic}')
      self.logger.info(f'Delays Topic (Read): {self.kafka_delays_topic}')
      self.logger.info(f'Last requested date: {self.checkpoint.date}')

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

    def __fetch_weather(self, latest_date):
      self.logger.info(f'Fetching weather data for dates from {self.checkpoint.date} to {latest_date}')
      api_params = {
	        "latitude": 48.210033,
	        "longitude": 16.363449,
	        "start_date": self.checkpoint.date,
	        "end_date": latest_date,
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

    def run(self):
      self.logger.info('***** Starting Weather Producer *****')
      try:
        # Listen for interruption events and get batch dataframe of events
        for df_event_batch in self.__listen_for_delays():

          # Get the latest date from the evets batch
          latest_date = df_event_batch['start'].max().date()
          self.logger.info(f'Checkpoint date: {self.checkpoint.date} | Events Batch latest date: {latest_date}')

          # Check if checkpoint date is None --> no weather data has been requested yet
          if self.checkpoint.date == None:
            self.checkpoint.date = latest_date - timedelta(days=1)
            self.logger.info(f'Checkpoint date is None, setting it to {self.checkpoint.date}')

          # Check if the weather data for the date has already been requested
          already_requested = True
          if latest_date > self.checkpoint.date:
            already_requested = False
          
          if not already_requested:
            df_weather = self.__fetch_weather(latest_date)
            self.checkpoint.date = latest_date
            self.__write_weather_to_kafka(df_weather)

            self.checkpoint.date = latest_date
            self.db.save_checkpoint(self.checkpoint)
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