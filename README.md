# dsi_project

# Prerequisities

+ docker
+ docker-compose

#### Optional
Lets make sure the node_exporter container will be able to mount the root directory so it can serve metrics:

```{bash}
sudo mount --make-shared /
sudo systemctl restart docker
```

With all that setup you can now spin up the containers with docker-compose

# Start up

```{bash}
# cd docker
docker-compose up -d
```
