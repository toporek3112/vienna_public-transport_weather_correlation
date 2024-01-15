import os
from clients.producer_delays import ProducerDelays
from clients.producer_weather import ProducerWeather
from clients.consumer import Consumer
from clients.setup_db import SetupDB
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    mode = os.getenv('MODE')

    if mode == 'producer_delays':
        consumer = ProducerDelays()
        consumer.run()
    elif mode == 'producer_weather':
        producer = ProducerWeather()
        producer.run()
    elif mode == 'consumer':
        producer = Consumer()
        producer.run()
    elif mode == 'setup_db':
        setup_db = SetupDB()
        setup_db.run()
    else:
        logger.error("Invalid MODE. Please set MODE (environment variable) to 'producer_delays', 'producer_weather' or 'consumer'.")

if __name__ == "__main__":
    main()
