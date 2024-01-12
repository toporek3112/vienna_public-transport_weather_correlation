from kafka import KafkaConsumer
from datetime import datetime
import os
import json
import psycopg2

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_table = os.getenv('DB_TABLE')
kafka_host = os.getenv('KAFKA_HOST')

class Consumer:
  def __init__(self):
    print("Initializing Consumer")

    self.consumer = KafkaConsumer(
      'topic_interruptions',
      'topic_weather',
      bootstrap_servers=kafka_host,
      group_id='consumer_01' 
    )

    # Initialize the database connection
    self.conn = psycopg2.connect(
        dbname = db_name,
        user = db_user,
        password = db_password,
        host = db_host,
        port = db_port
    )
    
    # Create a cursor
    self.cur = self.conn.cursor()
  
  def insert_into_interruptions_table(self, event):
    event_json = json.loads(event)
    print(f'Inserting interruption with id {event_json["id"]} into database')
    
    # Extract data from the event_json
    id_interruptions = event_json.get("id", None)
    title = event_json.get("title", None)
    behoben = event_json.get("behoben", None)
    lines = json.dumps(event_json.get("lines", []))
    stations = json.dumps(event_json.get("stations", []))
    start_str = event_json["start"]
    end_str = event_json["end"]
    
    # Parse the timestamp strings to datetime objects
    start = datetime.strptime(start_str, '%d.%m.%Y %H:%M')
    end = datetime.strptime(end_str, '%d.%m.%Y %H:%M')
    
    # Implement the SQL INSERT statement
    sql = """
        INSERT INTO interruptions (id_interruptions, title, behoben, lines, stations, time_start, "time_end")
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    # Execute the INSERT statement with the data
    self.cur.execute(sql, (id_interruptions, title, behoben, lines, stations, start, end))
    
    # Commit the changes to the database
    self.conn.commit()

  def insert_into_weather_table(self, event):
    event_json = json.loads(event)
    print(f'Inserting weather data for time {event_json["time"]} into database')

    # Extract data from the event_json
    time_str = event_json["time"]
    temperature_2m = event_json["temperature_2m"]
    relative_humidity_2m = event_json["relative_humidity_2m"]
    wind_speed_10m = event_json["wind_speed_10m"]

    # Parse the timestamp string to a datetime object
    time = datetime.strptime(time_str, '%d/%m/%y %H:%M:%S.%f')

    # Implement the SQL INSERT statement
    sql = """
        INSERT INTO weather_data (time, temperature_2m, relative_humidity_2m, wind_speed_10m)
        VALUES (%s, %s, %s, %s)
    """

    # Execute the INSERT statement with the data
    self.cur.execute(sql, (time, temperature_2m, relative_humidity_2m, wind_speed_10m))

    # Commit the changes to the database
    self.conn.commit()
  
  def run(self):
    for message in self.consumer:
      # Parse and process the Kafka message
      event = message.value.decode('utf-8')

      if message.topic == 'topic_interruptions':
          # Process interruptions event and insert into the database
          self.insert_into_interruptions_table(event)
      elif message.topic == 'topic_weather':
          # Process weather data and insert into the database
          self.insert_into_weather_table(event)
