import os
from producer_interruptions  import Producer_Interruptions
from producer_weather import Producer_Weather
from consumer import Consumer

def main():
    mode = os.getenv('MODE')

    if mode == 'producer_delays':
        consumer = Producer_Interruptions('https://öffi.at/?archive=1&text=&types=2%2C3&page=')
        consumer.run()
    elif mode == 'producer_weather':
        producer = Producer_Weather()
        producer.run()
    elif mode == 'consumer':
        producer = Producer_Weather()
        producer.run()
    else:
        print("Invalid MODE. Please set MODE (environment variable) to 'producer_delays', 'producer_weather' or 'consumer'.")

if __name__ == "__main__":
    main()
