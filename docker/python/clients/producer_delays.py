from kafka import KafkaProducer
import json
import requests
import sys
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime
import time
import logging

class ProducerDelays:
  def __init__(self):
    logging.basicConfig(level=logging.INFO)
    self.logger = logging.getLogger(__name__)

    self.source_url = source_url = os.getenv('SOURCE_URL')
    self.kafka_host = kafka_host = os.getenv('KAFKA_HOST')
    self.checkpoint_file_name = 'checkpoint_delays.json'
    self.kafka_topic = kafka_topic = os.getenv('KAFKA_TOPIC')
    self.timeout = int(os.getenv('TIMEOUT'))

    self.producer = KafkaProducer(
      bootstrap_servers=kafka_host,
      value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    self.logger.info("Initializing Delays Producer")
    self.logger.info(f'Source Url: {source_url}')
    self.logger.info(f'Kafka Host: {kafka_host}')
    self.logger.info(f'  Weather Topic (Write): {kafka_topic}')

  def __get_number_of_pages(self):
    # Fetch html from source url
    response = requests.get(self.source_url)
    # Parse source html into Beutifule soupe
    soup = BeautifulSoup(response.content, 'html.parser')
    # Get number of pages
    number_of_pages = int(soup.find(string = re.compile(r'Aktuelle Seite: \d+/\d+')).split('/')[-1].strip()[:-1])
    return number_of_pages

  def __save_checkpoint(self, checkpoint):
    self.logger.info(f'***** Saving checkpoint to {self.checkpoint_file_name} *****')

    with open(f'./{self.checkpoint_file_name}', 'w') as file:
      json.dump(checkpoint, file)

  def __get_checkpoint(self):
    self.logger.info(f'Looking up checkpoint from {self.checkpoint_file_name}')

    # Check if checkpoint_delays.json exists if not create it
    if not os.path.exists(f'./{self.checkpoint_file_name}'):
      self.logger.info(f'{self.checkpoint_file_name} not found. Creating...')

      number_of_pages = self.__get_number_of_pages()

      with open(f'./{self.checkpoint_file_name}', 'w') as file:
        json.dump(
          {
            "page": number_of_pages,
            "behoben": None,
            "id": None,
            "last_scrape_time": time.time()
          },
          file
        )

		# Read checkpoint.json and print info about last checkpoint
    with open(f'./{self.checkpoint_file_name}', 'r') as file:
      checkpoint = json.load(file)
      self.logger.info(f'Last checkpoint: Page: {checkpoint["page"]} | ID: {checkpoint["id"]} | Behoben: {checkpoint["behoben"]} | Last Scrape Time: {datetime.fromtimestamp(checkpoint["last_scrape_time"])} ')
      return checkpoint

  def __scrape_delays(self):
    # Get checkpoint of last scrape
    checkpoint = self.__get_checkpoint()

    self.logger.info(f'*** Scraping Page {checkpoint["page"]} ***')

		# Get page source html
    response = requests.get(f'{self.source_url}{checkpoint["page"]}')

		# Parse html into beautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    interruption_list_raw = soup.find('ul', {'class': 'category-filter'})

    delays = []

		# Build json
    for delay in interruption_list_raw.findChildren('li', attrs={'class': 'disruption uk-padding-small'},recursive=False):
      lines = []
      stations = []
      
      # Assign variables
      id = delay.attrs['id']
      title = delay.find('h2',{'class':'disruption-title'}).text.split(':')[-1].strip()
      content = delay.find('div',{'class':'uk-accordion-content'})
      behoben = content.find('p') != None

      if len(content.find_all('ul')) > 0:
        for line in content.find_all('ul')[0].find_all('li'):
          lines.append(line.text)
  
        if len(content.find_all('ul')) > 1: # some delays do not have stations see page 3041 N24
          for station in content.find_all('ul')[1].find_all('li'):
            stations.append(station.text)
      
      start = content.find_all(string=re.compile(r': \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}'))[0].split(': ')[1]
      end = content.find_all(string=re.compile(r': \d{2}\.\d{2}\.\d{4} \d{2}:\d{2}'))[1].split(': ')[1]
      
			#combine into a single dict and send to kafka
      interruption = {
        'id': id,
        'title':title,
        'behoben': behoben,
        'lines': lines,
        'stations': stations,
        'start': start,
        'end': end
        }
    
      delays.append(interruption)
    # Overwrite old checkpoint
    if checkpoint['page'] != 1: checkpoint['page'] = checkpoint['page'] - 1
    checkpoint['behoben'] = delays[0]['behoben']
    checkpoint['id'] = delays[0]['id']
    checkpoint['last_scrape_time'] = time.time()
    
    return [checkpoint, delays]

  def run(self):
    self.logger.info('***** Starting Delays Producer *****')

    try:
      while True:
        # Scrape delays
        checkpoint, delays = self.__scrape_delays()
      
			  # Send each JSON object as a separate message
        for delay in delays:
            logging.debug(delay)
            self.producer.send(self.kafka_topic, value=delay)
        
        # Ensure all messages are sent
        self.producer.flush()
        
        # Save checkpoint to file
        self.__save_checkpoint(checkpoint)
        time.sleep(self.timeout)
    except Exception as e:
      self.logger.error(f"AN ERROR OCCURED: {e}")
    finally:
      # Close the producer, ensuring it's done regardless of how the while loop exits
      self.logger.info("***** Closing Kafka producer *****")
      self.producer.close()
      self.logger.info("***** EXITING *****")


