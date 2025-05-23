import os
from clients.producer_delays import ProducerDelays
from clients.producer_weather import ProducerWeather
from clients.consumer import Consumer
from clients.setup_db import SetupDB
from utils.database import Database
from pythonjsonlogger import jsonlogger
import sys
import logging

log_handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(message)s')
log_handler.setFormatter(formatter)

logging.getLogger("kafka").setLevel(logging.WARNING)
logging.basicConfig(
  level=logging.INFO,
  handlers=[log_handler],
  force=True
)

def main():
    logger = logging.getLogger(__name__)
    mode = os.getenv('MODE')
    db_url = os.getenv('DB_CONNECTION')

    Database(db_url)

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
        logger.error(f'Invalid MODE: {mode}. Please set MODE (environment variable) to "producer_delays", "producer_weather", "setup_db" or "consumer".')

if __name__ == '__main__':
    main()
