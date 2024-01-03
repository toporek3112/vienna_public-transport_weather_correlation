#################################################
#################### Docker #####################
#################################################
docker exec -it dsi_postgres /bin/bash

# troubleshooting container
docker build -t debug-tools .
docker run -it --rm --network dsi_custom_bridge debug-tools

#################################################
################### Postgres ####################
#################################################

psql -h dsi_postgres -p 5432 -U postgres -d postgres