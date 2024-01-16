#################################################
#################### Docker #####################
#################################################
docker exec -it dsi_postgres /bin/bash

# troubleshooting container
docker build -t debug-tools .
docker run -it --rm --network docker_dsi_custom_bridge debug-tools

# db setup container
docker run --rm \
  --network docker_dsi_custom_bridge \
  -e MODE='setup_db' \
  -e DB_HOST='dsi_postgres' \
  -e DB_PORT='5432' \
  -e DB_NAME='dsi_project' \
  -e DB_USER='postgres' \
  -e DB_PASSWORD='postgres' \
  -e DB_TABLE='stops' \
  docker_psotgres_setup_table

#################################################
################### Postgres ####################
#################################################

psql -h dsi_postgres -p 5432 -U postgres -d postgres

# Export database
docker exec dsi_postgres pg_dump -U postgres dsi_project > database_dump_16.01.24.sql

INSERT INTO producer_delays_checkpoint (page, behoben, delay_id, last_scrape_time)
 VALUES (2632, TRUE, '26740', TO_TIMESTAMP(1705354511.2298088));

#################################################
#################### Kafka ######################
#################################################

# consume from topic
bin/kafka-console-consumer.sh --bootstrap-server kafka_00:9094 --topic topic_delays --from-beginning
# delete a topic
bin/kafka-topics.sh --bootstrap-server kafka_00:9094 --delete --topic stocks_topic
# list topics
bin/kafka-topics.sh --bootstrap-server kafka_00:9094 --list
# create topic
bin/kafka-topics.sh --bootstrap-server kafka_00:9094 --create --if-not-exists --replication-factor 1 --partitions 1 --config cleanup.policy=compact --topic stocks_topic
# produce json event
echo '{"id": "137232", "title": "U-Bahnbau\nZüge halten bei Josefstädter Str. 5", "behoben": true, "lines": ["2"], "stations": ["Rathaus"], "start": "11.01.2021 03:30", "end": "10.01.2024 23:45"}' | bin/kafka-console-producer.sh --broker-list kafka_00:9094 --topic topic_delays


# deploy connector
curl -X POST -H "Content-Type: application/json" --data @kafka_connect/connector_stocks_topic_to_postgres.yaml http://localhost:8083/connectors

### Kafka Connect
# check running connectors
curl http://localhost:8083/connectors/

##################################################
##################### Debug ######################
##################################################

# dsi_project
alias set_producer_delays='export MODE="producer_delays" ;
export KAFKA_HOST="localhost:9092" ;
export KAFKA_TOPIC="topic_delays" ;
export SOURCE_URL="https://öffi.at/?archive=1&text=&types=2%2C3&page=" ;
export TIMEOUT_SECONDS="10"'
alias set_producer_weather='export MODE="producer_weather" ;
export KAFKA_HOST="localhost:9092" ;
export KAFKA_TOPIC="topic_weather" ;
export KAFKA_INTERRUPTION_TOPIC="topic_delays" ;
export SOURCE_URL="https://archive-api.open-meteo.com/v1/archive"'

alias set_consumer='
export MODE="consumer" ;
export KAFKA_HOST="localhost:9092" ; 
export DB_HOST="localhost" ;
export DB_PORT="5432" ;
export DB_NAME="dsi_project" ; 
export DB_USER="postgres" ; 
export DB_PASSWORD="postgres"
'

alias set_setup_db='export MODE="setup_db" ;
export DB_HOST="localhost" ;
export DB_PORT="5432" ;
export DB_NAME="dsi_project" ;
export DB_USER="postgres" ;
export DB_PASSWORD="postgres" ;
export DB_TABLE="stops" ;
export KAFKA_HOST="localhost:9092"
'

##################################################
###################### SQL #######################
##################################################

# query disruption count per station
SELECT
  stops.name as "Station",
  COUNT(*) as "Delays",
  stops.longitude,
  stops.latitude
FROM
  delays
CROSS JOIN
  jsonb_array_elements_text(delays.stations) as station_name
JOIN
  stops ON station_name = stops.name
WHERE 
  $__timeFilter(delays.time_start)
GROUP BY
  stops.name, stops.longitude, stops.latitude;


# query total disruption count for a station
SELECT
   stops.name,
   COUNT(*) as disruption_count
 FROM
   delays
 CROSS JOIN
   jsonb_array_elements_text(delays.stations) as station_name
 JOIN
   stops ON station_name = stops.name
WHERE stops.name = ('${Station:raw}') AND $__timeFilter(delays.time_start)
GROUP BY
   stops.name

# query list of disruptions for selected station
SELECT
  time_start_original as "Time Start",
  title as "Title",
  behoben as "Behoben",
  lines as "Lines",
  stations as "Stations"
FROM
  delays
WHERE
  $__timeFilter(time_start)
  AND ('${Station:raw}') = ANY (SELECT jsonb_array_elements_text(stations));


 SELECT
   time_start,
   count(title)
 FROM
   delays
 WHERE
   'Johnstraße' = ANY (SELECT jsonb_array_elements_text(stations))
 GROUP BY time_start
 ORDER by time_start desc
