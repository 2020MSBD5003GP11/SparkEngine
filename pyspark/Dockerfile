FROM jupyter/pyspark-notebook

USER root
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y \
    && apt-get install -y wget python3-dev openjdk-8-jre-headless python3-pip nano\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pymongo

ENV SPARK_VERSION 3.0.1
ENV HADOOP_VERSION 3.2
ENV MONGO_SPARK_VERSION 3.0.0
ENV SCALA_VERSION 2.12

WORKDIR ${HOME}

ENV SPARK_HOME ${HOME}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}

ENV PATH $PATH:${SPARK_HOME}/bin

COPY files/times.json files/readme.txt files/examples.py files/initDocuments.py files/population_by_country_1980_2010.csv /home/ubuntu/

RUN cp -R /usr/local/spark-3.0.1-bin-hadoop3.2/  /home/jovyan/spark-3.0.1-bin-hadoop3.2/

USER jovyan
