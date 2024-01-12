from kafka import KafkaProducer
import json
import requests
import sys
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime
import time

source_url = os.getenv('SOURCE_URL')
kafka_host = os.getenv('KAFKA_HOST')
kafka_topic = os.getenv('KAFKA_TOPIC')
checkpoint_file_name = 'checkpoint_interruptions.json'

class Producer_Interruptions:
    def __init__(self):
        print("Initializing Delays Producer")
        print(f'Source Url: {source_url}')
        print(f'Kafka Host: {kafka_host}')
        print(f'  Weather Topic (Write): {kafka_topic}')

        self.source_url = source_url
        self.producer = KafkaProducer(
          bootstrap_servers=kafka_host,
          value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def __get_number_of_pages(self):
        # Fetch html from source url
        response = requests.get(self.source_url)
        # Parse source html into Beutifule soupe
        soup = BeautifulSoup(response.content, 'html.parser')
        # Get number of pages
        number_of_pages = int(soup.find(string = re.compile(r'Aktuelle Seite: \d+/\d+')).split('/')[-1].strip()[:-1])
        return number_of_pages

    def __save_checkpoint(self, checkpoint):
        print(f'***** Saving checkpoint to {checkpoint_file_name} *****\n')

        with open(f'./{checkpoint_file_name}', 'w') as file:
            json.dump(checkpoint, file)

    def __get_checkpoint(self):
        print(f'Looking up checkpoint from {checkpoint_file_name}')

        # Check if checkpoint_interruptions.json exists if not create it
        if not os.path.exists(f'./{checkpoint_file_name}'):
            print(f'{checkpoint_file_name} not found. Creating...')

            number_of_pages = self.__get_number_of_pages()

            with open(f'./{checkpoint_file_name}', 'w') as file:
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
        with open(f'./{checkpoint_file_name}', 'r') as file:
            checkpoint = json.load(file)
            print(f'Last checkpoint: Page: {checkpoint["page"]} | ID: {checkpoint["id"]} | Behoben: {checkpoint["behoben"]} | Last Scrape Time: {datetime.fromtimestamp(checkpoint["last_scrape_time"])} \n')
            return checkpoint

    def __scrape_interruptions(self):
        # Get checkpoint of last scrape
        checkpoint = self.__get_checkpoint()

        print(f'*** Scraping Page {checkpoint["page"]} ***')

        # Get page source html
        response = requests.get(f'{self.source_url}{checkpoint["page"]}')

        # Parse html into beautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        interruption_list_raw = soup.find('ul', {'class': 'category-filter'})

        interruptions = []

        # Build json
        for delay in interruption_list_raw.findChildren('li', attrs={'class': 'disruption uk-padding-small'},recursive=False):
            lines = []
            stations = []
    
            # Assign variables
            id = delay.attrs['id']
            title = delay.find('h2',{'class':'disruption-title'}).text.split(':')[-1].strip()
            content = delay.find('div',{'class':'uk-accordion-content'})
            behoben = content.find('p') != None
    
            for line in content.find_all('ul')[0].find_all('li'):
                lines.append(line.text)
    
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
    
            print(interruption)
            interruptions.append(interruption)

        # Overwrite old checkpoint
        if checkpoint['page'] != 1: checkpoint['page'] = checkpoint['page'] - 1
        checkpoint['behoben'] = interruptions[0]['behoben']
        checkpoint['id'] = interruptions[0]['id']
        checkpoint['last_scrape_time'] = time.time()

        return [checkpoint, interruptions]

    def run(self):
        print('\n***** Starting Delays Producer *****\n')
    
        try:
            while True:
                # Scrape interruptions
                checkpoint, interruptions = self.__scrape_interruptions()
    
                # Send each JSON object as a separate message
                for interruption in interruptions:
                    self.producer.send(kafka_topic, value=interruption)
    
                # Ensure all messages are sent
                self.producer.flush()
    
                # Save checkpoint to file
                self.__save_checkpoint(checkpoint)
    
                time.sleep(30)
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Close the producer, ensuring it's done regardless of how the while loop exits
            print("\n***** Closing Kafka producer *****")
            self.producer.close()
            print("***** EXITING *****\n")


