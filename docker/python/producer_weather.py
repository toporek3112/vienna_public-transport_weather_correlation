from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime, timedelta
import json
import os
import time
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

source_url = os.getenv('SOURCE_URL')
kafka_host = os.getenv('KAFKA_HOST')
kafka_topic = os.getenv('KAFKA_TOPIC')
kafka_interruption_topic = os.getenv('KAFKA_INTERRUPTION_TOPIC')

class Producer_Weather():
    def __init__(self):
      print('Initializing Weather Producer')
      print(f'Source Url: {source_url}')
      print(f'Kafka Host: {kafka_host}')
      print(f'  Weather Topic (Write): {kafka_topic}')
      print(f'  Interruptions Topic (Read): {kafka_interruption_topic}')
      
      self.source_url = source_url
      self.cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
      self.retry_session = retry(self.cache_session, retries = 5, backoff_factor = 0.2)
      self.openmeteo = openmeteo_requests.Client(session = self.retry_session)

      self.producer = KafkaProducer(
          bootstrap_servers=kafka_host,
          value_serializer=lambda v: json.dumps(v).encode('utf-8')
      )
      self.consumer = KafkaConsumer(
          kafka_interruption_topic,
          bootstrap_servers=kafka_host,
          value_deserializer=lambda m: json.loads(m.decode('utf-8'))
      )

    def __listen_for_interruptions(self):
      print("*** Listening for interruption events from Kafka ***")
    
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
          print(f'Recived batch of {len(batch)} events')
          yield batch
          batch = []  # Reset batch
          start_time = time.time()  # Reset start time for the new batch

      # After exiting the loop, if there are any remaining messages in the batch, yield them
      if batch:
        yield batch

    def __extract_date_time(self, events_batch):
      print("Extracting date of the interruption event")
    
      # Get unique dates from events batch and convert them to the desired format
      unique_dates = set()
      for event in events_batch:
          # Extract the date part
          original_date_str = event['start'].split(' ')[0]
  
          # Create a datetime object from the string
          date_obj = datetime.strptime(original_date_str, '%d.%m.%Y')
  
          # Format the datetime object to the desired format
          formatted_date = date_obj.strftime('%Y-%m-%d')
  
          # Add the formatted date to the set
          unique_dates.add(formatted_date)
  
      # Convert the set to a list to get an array of unique, formatted dates
      unique_dates_list = sorted(list(unique_dates))

      # Add an additional date which is +24 hours to the last date in the list
      if unique_dates_list:
          last_date = datetime.strptime(unique_dates_list[-1], '%Y-%m-%d')
          next_day = last_date + timedelta(days=1)
          unique_dates_list.append(next_day.strftime('%Y-%m-%d'))

      print(f'Dates extracted: {unique_dates_list}')
      return unique_dates_list

    def __check_weather_date_frames(self, date_time_frame):
      file_path = 'already_requested_weather_date_frames.json'
      already_requested = False
  
      # Check if the file exists
      if os.path.exists(file_path):
          # Read the existing data
          with open(file_path, 'r') as file:
              try:
                  requested_frames = json.load(file)
              except json.JSONDecodeError:
                  requested_frames = []
  
          # Check if the current date_time_frame is in the file
          if date_time_frame in requested_frames:
              already_requested = True
          else:
              # Add the new date_time_frame and save
              requested_frames.append(date_time_frame)
              with open(file_path, 'w') as file:
                  json.dump(requested_frames, file)
      else:
          # Create the file and write the current date_time_frame
          with open(file_path, 'w') as file:
              json.dump([date_time_frame], file)
  
      return already_requested

    def __fetch_weather(self, date_time):
      date_frame = [date_time[0], date_time[-1]]
      already_requested = self.__check_weather_date_frames([date_frame])

      if not already_requested:
        print(f'Fetching weather data for dates from {date_frame[0]} to  {date_frame[1]}')
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
        return [already_requested, hourly_dataframe]
      else:
        return [already_requested, None]

    def __write_weather_to_kafka(self, df_weather):
      print('Writing weather data into kafka\n')
      for index, row in df_weather.iterrows():
        # Convert the row to JSON format
        row_as_json_string = row.to_json()
        row_json = json.loads(row_as_json_string)
        # Send the row as a message to Kafka
        self.producer.send(kafka_topic, value=row_json)

    def run(self):
      print('\n***** Starting Weather Producer *****\n')
      try:
        # while True:
          # Listen for interruption events
          for event_batch in self.__listen_for_interruptions():
            dates_start = self.__extract_date_time(event_batch)

            if dates_start:
              # Fetch weather data for the given date_time
              already_requested, df_weather = self.__fetch_weather(dates_start)
              
              if not already_requested:
                self.__write_weather_to_kafka(df_weather)
              else:
                 print('Date frame for weather data already requested\nSkipping...\n')

              # Ensure all messages are sent
              self.producer.flush()
            else:
              print("No events or unable to extract date_time")
      except Exception as e:
        print(f"An error occurred: {e}")
      finally:
        # Close the producer and consumer, ensuring it's done regardless of how the while loop exits
        print("\n***** Closing Kafka producer and consumer *****")
        self.producer.close()
        self.consumer.close()
        print("***** EXITING *****\n")
