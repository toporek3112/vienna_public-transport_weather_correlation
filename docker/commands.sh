#################################################
#################### Docker #####################
#################################################
docker exec -it dsi_postgres /bin/bash

# troubleshooting container
docker build -t debug-tools .
docker run -it --rm --network docker_dsi_custom_bridge debug-tools

#################################################
################### Postgres ####################
#################################################

psql -h dsi_postgres -p 5432 -U postgres -d postgres

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

#################################################
################## Postgres #####################
#################################################

# Export database
docker exec pg_dump pg_dump -U postgres dsi_project > database_dump_14.01.24.sql

##################################################
##################### Debug ######################
##################################################

# dsi_project
alias set_producer_delays='export MODE="producer_delays" ;
export KAFKA_HOST="localhost:9092" ;
export KAFKA_TOPIC="topic_delays" ;
export SOURCE_URL="https://öffi.at/?archive=1&text=&types=2%2C3&page=" ;
export TIMEOUT="10"'
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
