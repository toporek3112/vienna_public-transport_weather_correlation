from kafka import KafkaProducer
import json
import os
import time

source_url = os.getenv('SOURCE_URL')
kafka_host = os.getenv('KAFKA_HOST')
kafka_topic = os.getenv('KAFKA_TOPIC')
checkpoint_file_name = 'checkpoint_weather.json'

class Producer_Weather():
  def __init__(self):
    print("Initializing Weather Producer")

    self.source_url = source_url
    self.producer = KafkaProducer(
      bootstrap_servers=kafka_host,
      value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
  
  def __scrape_weather():
    print(f'*** Scraping Page {checkpoint["page"]} ***')


  def run(self):
    print('\n***** Starting Weather Producer *****\n')

    try:
      while True:
        # Scrape interruptions
        checkpoint, wather = self.__scrape_weather()

        # Send each JSON object as a separate message
        for w in wather:
            self.producer.send(kafka_topic, value=w)

        # Ensure all messages are sent
        self.producer.flush()

        # Save checkpoint to file
        self.__save_checkpoint(checkpoint)

        time.sleep(300)
    except Exception as e:
      print(f"An error occurred: {e}")
    finally:
      # Close the producer, ensuring it's done regardless of how the while loop exits
      print("\n***** Closing Kafka producer *****")
      self.producer.close()
      print("***** EXITING *****\n")