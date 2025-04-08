from kafka import KafkaConsumer
import os
import sys
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from clients.events.delay import Delay
from clients.events.weather_data import WeatherData
from utils.database import Database

Base = declarative_base()

class Consumer:
  def __init__(self):
    # Configure logging
    self.logger = logging.getLogger(__name__)
    self.logger.info("Initializing Consumer")

    kafka_host = os.getenv('KAFKA_HOST', 'vptwc_kafka_00:9094')

    self.session = Database.get_session()

    # Retry mechanism for Kafka connection
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
      try:
        # Initialize the Kafka consumer
        self.consumer = KafkaConsumer(
          'topic_delays',
          'topic_weather',
          bootstrap_servers=kafka_host,
          group_id='consumer_01' 
        )
        break
      except Exception as e:
        self.logger.warning(f"Attempt {retry_count + 1} failed to connect Kafka Producer: {e}")
        time.sleep(5)  # wait for 5 seconds before next attempt
        retry_count += 1

    if retry_count == max_retries:
      self.logger.error("Failed to connect to Kafka after multiple attempts.")
      sys.exit(1)
  
  def run(self):
    try:
      for message in self.consumer:
        # Parse and process the Kafka message
        event = message.value.decode('utf-8')

        if message.topic == 'topic_delays':
          # Create an instance of Delay with the event data
          delay = Delay(event)
          self.logger.info(f'Upserting delay with id_delays {delay.id_delays} into database')
  
          # Check if a record with this id_delays exists
          existing_delay = self.session.query(Delay).filter(Delay.id_delays == delay.id_delays).first()
  
          if existing_delay:
            # Update existing record
            for key, value in vars(delay).items():
              setattr(existing_delay, key, value)
          else:
            # Insert new record
            self.session.add(delay)
  
          self.session.commit()
  
        elif message.topic == 'topic_weather':
          # Create Instance of WeatherData with the json event 
          weather_data = WeatherData(event)
          self.logger.info(f'Inserting weather data for time {weather_data.time} into database')
          # Add to session and commit
          self.session.add(weather_data)
          self.session.commit()
    except Exception as e:
      self.logger.error(e)
    finally:
      # Close the producer and consumer, ensuring it's done regardless of how the while loop exits
      self.logger.info('***** Closing Kafka producer and consumer *****')
      self.consumer.close()
      self.logger.info('***** EXITING *****')
