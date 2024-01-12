import os
from producer_interruptions  import Producer_Interruptions
from producer_weather import Producer_Weather
from setup_db import Setup_DB
from consumer import Consumer

def main():
    mode = os.getenv('MODE')

    if mode == 'producer_interruptions':
        consumer = Producer_Interruptions()
        consumer.run()
    elif mode == 'producer_weather':
        producer = Producer_Weather()
        producer.run()
    elif mode == 'consumer':
        producer = Consumer()
        producer.run()
    elif mode == 'setup_db':
        setup_db = Setup_DB()
        setup_db.run()
    else:
        print("Invalid MODE. Please set MODE (environment variable) to 'producer_delays', 'producer_weather' or 'consumer'.")

if __name__ == "__main__":
    main()
