from sqlalchemy import create_engine
import pandas as pd
import os

db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_table = os.getenv('DB_TABLE')
file_name = 'data/wienerlinien-ogd-haltepunkte.csv'

class Setup_DB():
  def __init__(self):
    print('Initializing Setup DB')
    print(f'db host: {db_host}')
    print(f'db port: {db_port}')
    print(f'db user: {db_user}')
    print(f'db name: {db_name}')
    print(f'db table: {db_table}\n')

    self.engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    try:
        self.engine.connect()
        print("success")
    except Exception as e:
        print("error", e.__cause__)

  def run(self):
    print('***** Setting up stops table in dsi_projekt database *****')
    haltestellen = pd.read_csv(file_name, sep=';', usecols=[0,2,5,6], names=['id','name','longitude','latitude'], header=0)
    haltestellen.to_sql(db_table, self.engine, if_exists='replace', index=False)
    print('Data Inserted into Table')
    
    # Query to select the first 10 rows from the table
    query = "SELECT * FROM stops LIMIT 10"
    result = pd.read_sql(query, self.engine)
    print(f"First 10 rows from the '{db_table}' table:")
    print(result)
