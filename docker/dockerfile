#################################################################################################
# This docker image is used for debuging and testing feel free to install additional tools.     #
#################################################################################################
# docker build -t debug-tools .                                                                 #
# docker run -it --rm --network custom_bridge debug-tools                                       #
#################################################################################################

# Use OpenJDK 11 JDK base image
FROM openjdk:11-jdk

# Set the working directory
WORKDIR /root

# Install essential tools
RUN apt-get update && apt-get install -y \
    net-tools \
    procps \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Download jmxterm
RUN curl -L -o ./jmxterm-1.0.2-uber.jar https://github.com/jiaqi/jmxterm/releases/download/v1.0.2/jmxterm-1.0.2-uber.jar
RUN wget https://dlcdn.apache.org/kafka/3.6.1/kafka_2.13-3.6.1.tgz && tar -xzf kafka_2.13-3.6.1.tgz && rm kafka_2.13-3.6.1.tgz

# Set aliases
RUN echo 'alias l="ls -lha"' >> .bashrc
RUN echo 'alias ll="ls -lh"' >> .bashrc

# By default, just run a shell. Users can execute Java tools or other commands as needed.
CMD ["/bin/bash"]
