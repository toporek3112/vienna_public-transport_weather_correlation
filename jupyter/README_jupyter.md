# Jupyter Notebooks
These jupyter Notebooks do the same things as some of the docker containers, but as executable scripts.
The scripts still need a working kafka instance and Postgres database to function (and visualization still requires grafana), but are otheriwse self-contained.

## webscraper:
Like container *dsi_kafka_producer_delays*, scrapes Öffi.at and writes delays to a kafka producer

## api:
Like container *dsi_kafka_producer_weather*, requests weather data from openmeteo for the relevant timeframe. One difference here is that api.ipynb simply requests all data for our relevant timeframe, whereas the actual containerized solution uses the timestamps from the disruptions

## consumer:
Like container *dsi_kafka_consumer*, consumes the data from both topics and writes them to the database

## stations:
Imports the station data from the csv file into the database. This is included in the container *dsi_kafka_consumer*.


