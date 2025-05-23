from clients.events.delay import Delay
from utils.producer_delays_checkpoint import ProducerDelaysCheckpoint
from kafka import KafkaProducer
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
import json
import requests
import sys
import re
import os
import time
import logging

class ProducerDelays:
  def __init__(self):
    self.logger = logging.getLogger(__name__)

    self.source_url = source_url = os.getenv('SOURCE_URL', 'https://öffi.at/?archive=1&text=&types=2%2C3&page=')
    self.kafka_host = kafka_host = os.getenv('KAFKA_HOST', 'vptwc_kafka_00:9094')
    self.kafka_topic = kafka_topic = os.getenv('KAFKA_TOPIC', 'topic_delays')
    self.scrape_interval = int(os.getenv('SCRAPE_INTERVAL_SECONDS', 10))
    self.db = ProducerDelaysCheckpoint()

    # Retry mechanism for Kafka connection
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
      try:
        self.producer = KafkaProducer(
          bootstrap_servers=self.kafka_host,
          value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        # Test the connection
        self.producer.bootstrap_connected()
        self.logger.info("Kafka Producer connected successfully.")
        break
      except Exception as e:
        self.logger.warning(f"Attempt {retry_count + 1} failed to connect Kafka Producer: {e}")
        # hourly_dataframe # wait for 5 seconds before next attempt
        retry_count += 1

    if retry_count == max_retries:
      self.logger.error("Failed to connect to Kafka after multiple attempts.")
      sys.exit(1)

    self.checkpoint = self.db.get_checkpoint()

    self.logger.info("Initializing Delays Producer")
    self.logger.info(f'Source Url: {source_url}')
    self.logger.info(f'Kafka Host: {kafka_host}')
    self.logger.info(f'Weather Topic (Write): {kafka_topic}')
    self.logger.info(f'Last scrape time: {self.checkpoint.last_scrape_time}')
    self.logger.info(f'Last scraped page: {self.checkpoint.page}')
    self.logger.info(f'Last scraped delay ID: {self.checkpoint.delay_id}')

  def __get_number_of_pages(self):
    # Fetch html from source url
    response = requests.get(self.source_url)
    # Parse source html into Beutifule soupe
    soup = BeautifulSoup(response.content, 'html.parser')
    # Get number of pages
    number_of_pages = int(soup.find(string = re.compile(r'Aktuelle Seite: \d+/\d+')).split('/')[-1].strip()[:-1])
    return number_of_pages

  def __scrape_delays(self):
    if self.checkpoint.page == 0:
      self.checkpoint.page = self.__get_number_of_pages()

    self.logger.info(f'*** Scraping Page {self.checkpoint.page} ***')

    scrape_url = f'{self.source_url}{self.checkpoint.page}'
    response = requests.get(scrape_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    interruption_list_raw = soup.find('ul', {'class': 'category-filter'})

    delays = []

    # get information from the soup
    for delay in interruption_list_raw.findChildren('li', attrs={'class': 'disruption uk-padding-small'}, recursive=False):
      lines = []
      stations = []

      id = delay.attrs['id']
      title = delay.find('h2', {'class': 'disruption-title'}).text.strip()
      content = delay.find('div', {'class': 'uk-accordion-content'})
      behoben = content.find('p') is not None

      if len(content.find_all('ul')) > 0:
        for line in content.find_all('ul')[0].find_all('li'):
          lines.append(line.text)

        if len(content.find_all('ul')) > 1:
          for station in content.find_all('ul')[1].find_all('li'):
            stations.append(station.text)

      start = content.find_all(string=re.compile(r': \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}'))[0].split(': ')[1]
      end = content.find_all(string=re.compile(r': \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}'))[1].split(': ')[1]

      interruption = {
        'id': id,
        'title': title,
        'behoben': behoben,
        'lines': lines,
        'stations': stations,
        'start': start,
        'end': end,
        'page': f'{self.checkpoint.page}'
      }

      delays.append(interruption)

    # Update checkpoint
    if self.checkpoint.page != 1:
      self.checkpoint.page -= 1

    self.checkpoint.behoben = delays[0]['behoben']
    self.checkpoint.delay_id = delays[0]['id']
    self.checkpoint.last_scrape_time = datetime.fromtimestamp(time.time())

    return delays

  def run(self):
    self.logger.info('***** Starting Delays Producer *****')

    try:
      while True:
        # Scrape delays
        delays = self.__scrape_delays()
      
			  # Send each JSON object as a separate message
        for delay in delays:
            self.logger.debug(delay)
            self.producer.send(self.kafka_topic, value=delay)
        
        # Ensure all messages are sent
        self.producer.flush()
        
        # Save checkpoint to file
        self.db.save_checkpoint(self.checkpoint)
        time.sleep(self.scrape_interval)
    except Exception as e:
      self.logger.error(f"AN ERROR OCCURED: {e}")
    finally:
      # Close the producer, ensuring it's done regardless of how the while loop exits
      self.logger.info("***** Closing Kafka producer *****")
      self.producer.close()
      self.logger.info("***** EXITING *****")


