import sys
from pyspark.sql import SQLContext, SparkSession
from pyspark import SparkContext, SparkConf

sparkConf = SparkConf().setMaster("local").setAppName("MongoSparkConnectorTour").set("spark.app.id", "MongoSparkConnectorTour")


spark = SparkSession.builder.appName("local").\
                                master("spark://spark-master:7077").\
                                config("spark.executor.memory", "1g").\
                                config("spark.mongodb.input.uri","mongodb://mongo1:27017/spark.times").\
                                config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.0").\
                                getOrCreate()

df = spark.read.format("mongo").load()
print(4321)
df.printSchema()
print(1234)