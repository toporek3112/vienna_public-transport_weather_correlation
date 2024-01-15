from kafka import KafkaConsumer
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from clients.events.delays import Delay
from clients.events.weather_data import WeatherData
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Consumer:
  def __init__(self):
# Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    self.logger = logging.getLogger(__name__)
    
    self.logger.info("Initializing Consumer")
    
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    kafka_host = os.getenv('KAFKA_HOST')

    # Initialize the database engine
    self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    Base.metadata.create_all(self.engine)

    # Create a session
    Session = sessionmaker(bind=self.engine)
    self.session = Session()

    # Initialize the Kafka consumer
    self.consumer = KafkaConsumer(
      'topic_delays',
      'topic_weather',
      bootstrap_servers=kafka_host,
      group_id='consumer_01' 
    )
  
  def run(self):
    try:
      for message in self.consumer:
        # Parse and process the Kafka message
        event = message.value.decode('utf-8')

        if message.topic == 'topic_delays':
          # Create an instance of Interruption
          delay = Delay(event)
          self.logger.info(f'Inserting delay with id {delay.id} into database')
          # Add to session and commit
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
