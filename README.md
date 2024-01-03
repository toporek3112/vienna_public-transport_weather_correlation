# dsi_project

# Prerequisities

+ docker
+ docker-compose

# Setup

As a start create a custom bridge network for this project:

```{bash}
docker network create --driver bridge --subnet 172.20.0.0/16 dsi_custom_bridge
```
After the network is created lets make sure the node_exporter container will be able to mount the root directory so it can serve metrics:

```{bash}
sudo mount --make-shared /
sudo systemctl restart docker
```

With all that setup you can now spin up the containers with docker-compose

```{bash}
# cd docker
docker-compose up -d
```
