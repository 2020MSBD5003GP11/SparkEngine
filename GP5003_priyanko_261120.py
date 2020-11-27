#!/usr/bin/python
# -*- coding: utf-8 -*-

# In[1]:

import pyspark

# sc = pyspark.SparkContext(appName = "MyAPP")

from pyspark.sql.functions import *
from pyspark.sql.session import SparkSession

# spark = SparkSession(sc)

import sys
from pyspark.sql import SQLContext, SparkSession
from pyspark import SparkContext, SparkConf

# from pyspark.sql.functions import udf,col

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pyspark.sql import SQLContext
from pyspark.mllib.stat import Statistics
import pandas as pd
from pyspark.sql.functions import udf
from pyspark.ml.feature import StringIndexer, VectorAssembler, \
    StandardScaler
from pyspark.ml import Pipeline
from sklearn.metrics import confusion_matrix
from pyspark.sql.functions import col, explode, array, lit

# In[2]:

# sparkConf = SparkConf().setMaster("local").setAppName("MongoSparkConnectorTour").set("spark.app.id", "MongoSparkConnectorTour")
# sqlContext = SQLContext(sc)
## create and load dataframe from MongoDB URI
# df = sqlContext.read.format("com.mongodb.spark.sql.DefaultSource")\
#                     .option("spark.mongodb.input.uri", "mongodb+srv://admin:12345678Pc@cluster0.k5xvg.mongodb.net/2020MSBD5003GP11.BehaviorData?retryWrites=true&w=majority")\
#                     .load()

df = spark.read.csv('../data/2019-Oct.csv', header=True,
                    inferSchema=True)  # .limit(1000000)

# In[3]:

original_columns = df.columns

# original_columns.remove('_id')#needed for DataBricks

# In[4]:

usable_ids = df.select('user_id'
                       ).where("event_type = 'cart' or event_type = 'purchase'"
                               ).distinct().toPandas()
usable_ids_list = usable_ids['user_id'].tolist()
df = df.where(df.user_id.isin(usable_ids_list))
df = df.withColumn('category_id', df['category_id'].cast('string'))  # Should be commented for Databricks

# In[5]:

df.cache()

# In[6]:

df_targets = df.select('*'
                       ).where("event_type = 'cart' or event_type = 'purchase'"
                               ).dropDuplicates(subset=['event_type',
        'product_id', 'price', 'user_id', 'user_session'])

# In[7]:

# add new column is_purchased if event_type = purchase then 1 else 0

df_targets = df_targets.withColumn('is_purchased', when(col('event_type'
                                   ) == 'purchase', 1).otherwise(0))

# In[8]:

df_targets.createOrReplaceTempView('df_pur')
df_pur_max = \
    spark.sql('SELECT user_session, product_id, MAX(is_purchased) is_purchased_max FROM df_pur GROUP BY user_session, product_id'
              )

# In[9]:

import pyspark.sql.functions as f

# In[10]:

df_targets = df_targets.alias('a').join(df_pur_max.alias('b'),
        ['user_session', 'product_id']).select(
    'a.brand',
    'a.category_code',
    'a.category_id',
    'a.event_time',
    'a.event_type',
    'a.price',
    'a.product_id',
    'a.user_id',
    'a.user_session',
    'b.is_purchased_max',
    ).withColumnRenamed('is_purchased_max', 'is_purchased')

# In[11]:

df_targets = df_targets.select('*').where("event_type = 'cart'"
        ).dropDuplicates(subset=['user_session', 'product_id',
                         'is_purchased'])

# In[12]:

df_targets = df_targets.select(
    '*',
    dayofweek(col('event_time')).alias('week_day'),
    hour(col('event_time')).alias('dt_hour'),
    dayofmonth(col('event_time')).alias('dt_day'),
    split('category_code', '.')[0].alias('category_code_level1'),
    split('category_code', '.')[1].alias('category_code_level2'),
    split('category_code', '.')[2].alias('category_code_level4'),
    )
df_targets = df_targets.select('*', f.coalesce('category_code_level2',
                               'category_code_level4'
                               ).alias('category_code_level3'))
df_targets = df_targets.withColumn('category_id_id1',
                                   substring('category_id', 1,
                                   6)).withColumn('category_id_id2',
        substring('category_id', 7, 6)).withColumn('category_id_id3',
        substring('category_id', 13, 7))
df_targets = df_targets.select('*', f.coalesce('category_id_id1',
                               'category_code_level1'
                               ).alias('category_code_level1_f'))
df_targets = df_targets.select('*', f.coalesce('category_id_id1',
                               'category_code_level2'
                               ).alias('category_code_level2_f'))
df_targets = df_targets.select('*', f.coalesce('category_id_id1',
                               'category_code_level3'
                               ).alias('category_code_level3_f'))
df_targets = df_targets.select('*', f.coalesce('category_id_id1',
                               'brand').alias('brand_f'))

# In[13]:

df.createOrReplaceTempView('df_temp1')
df.createOrReplaceTempView('df_temp2')
df_purchase_users_activity = \
    spark.sql('select * from df_temp2 where user_id in (select distinct user_id from df_temp1 where event_type = "cart" or event_type = "purchase")'
              )
df_activity_in_session = \
    df_purchase_users_activity.groupBy('user_session'
        ).count().withColumnRenamed('count', 'activity_count')

# In[14]:

# join the activity_count

df_targets = df_targets.alias('a').join(df_activity_in_session.alias('b'
        ), 'user_session', how='left').select('a.*', 'b.activity_count')
df_targets = df_targets.fillna(0, subset=['activity_count'])

# In[15]:

df_targets.printSchema()

# In[16]:

usable_features = [
    'category_id_id1',
    'category_id_id2',
    'category_id_id3',
    'category_code_level1_f',
    'category_code_level2_f',
    'category_code_level3_f',
    'brand_f',
    'price',
    'dt_hour',
    'dt_day',
    'week_day',
    'activity_count',
    'is_purchased',
    ]

# In[17]:

cols_to_drop = [col for col in df_targets.columns if col
                not in usable_features]
df = df_targets.drop(
    'user_session',
    'brand',
    'category_code',
    'category_id',
    'event_time',
    'event_type',
    'product_id',
    'user_id',
    'category_code_level1',
    'category_code_level2',
    'category_code_level4',
    'category_code_level3',
    )
df.printSchema()

# In[18]:

# df_targets = \[
#     df_targets.wher]e('category_code is not null and brand is not null'
#                      )

df = df.na.drop()

# In[19]:

# Oversampling through explode - commenetd
# major_df = df_targets.where('is_purchased = 0')
# minor_df = df_targets.where('is_purchased = 1')

# In[20]:

# ratio = int(major_df.count()/minor_df.count())
# print("ratio: "+str(ratio))

# In[21]:

# a = range(ratio)
## duplicate the minority rows
# oversampled_df = minor_df.withColumn("dummy", explode(array([lit(x) for x in a]))).drop('dummy')
## combine both oversampled minority rows and previous majority rows
# combined_df = major_df.unionAll(oversampled_df)

# In[22]:

# combined_df = df_targets

# In[23]:

# Index category features - Cat features

indexer = StringIndexer(inputCols=['category_id_id1', 'brand_f',
                        'category_code_level1_f',
                        'category_code_level2_f'],
                        outputCols=['category_id_id1_index',
                        'brand_index', 'category_code_level1_index',
                        'category_code_level2_index'])  #    'category_id_id2',

                                                        #    'category_id_id3',
                                                        #    'category_code_level3_f'
                                                        #    'category_id_id2_index',
                                                        #    'category_id_id3_index',

# ,#    'category_code_level3_index'

# In[24]:

# Scale - Continuous numerical features

numericAssembler = VectorAssembler().setInputCols(['price',
        'activity_count']).setOutputCol('vectorNumeric')

# In[25]:

numericScaler = StandardScaler().setInputCol('vectorNumeric'
        ).setOutputCol('scaledNumeric')

# In[26]:

from distutils.version import LooseVersion

# In[27]:

# Encode Categorical Features - ?? To be revisited

if LooseVersion(pyspark.__version__) < LooseVersion('3.0'):
    from pyspark.ml.feature import OneHotEncoderEstimator
    encoder = OneHotEncoderEstimator(inputCols=['week_day', 'dt_day',
            'dt_hour'], outputCols=['week_day_coded', 'dt_day_coded',
            'dt_hour_coded'])
else:
    from pyspark.ml.feature import OneHotEncoder
    encoder = OneHotEncoder(inputCols=['week_day', 'dt_day', 'dt_hour'
                            ], outputCols=['week_day_coded',
                            'dt_day_coded', 'dt_hour_coded'])

# In[28]:

# Standardize numerical features
# Vector Assembler - all numeric features

assembler = VectorAssembler().setInputCols([  #     'price_scaled',
                                              #     'activity_count_scaled',
    'week_day_coded',
    'dt_day_coded',
    'dt_hour_coded',
    'scaledNumeric',
    'category_id_id1_index',
    'brand_index',
    'category_code_level1_index',
    'category_code_level2_index',
    ]).setOutputCol('features')

# In[29]:

# LabelIndex - the label is_purchased

label_indexer = StringIndexer().setInputCol('is_purchased'
        ).setOutputCol('label')

# In[31]:

# Run Pipeline of transformers

pipeline_stages = Pipeline().setStages([
    indexer,
    numericAssembler,
    numericScaler,
    encoder,
    assembler,
    label_indexer,
    ])

# .##.#setStages([indexer,assembler,label_indexer])

pipeline_model = pipeline_stages.fit(df)  # pipeline_stages.fit(df_targets)
pipeline_df = pipeline_model.transform(df)  # pipeline_model.transform(df_targets)

# In[32]:

# Select Data for Modeling

selectedCols = ['features', 'label']  # original_columns + ['features', 'label']
pipeline_df = pipeline_df.select(selectedCols)
pipeline_df.printSchema()

# In[33]:

print pipeline_df.features

# In[34]:

# pipeline_df = pipeline_df.sample(frac = 1)

(train, test) = pipeline_df.randomSplit([0.8, 0.2], seed=7)
print 'Training Dataset Count: ' + str(train.count())
print 'Test Dataset Count: ' + str(test.count())

# In[35]:

from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# In[36]:

from pyspark.ml.classification import LogisticRegression

# In[ ]:

## Final run for Databricks - only GBT and RF should be used

# In[37]:

##Fit Logistic Regression Model and see the data
# lr = LogisticRegression(featuresCol = 'features', labelCol = 'label', maxIter=5 , family="binomial")
# lrModel = lr.fit(train)
# predictions = lrModel.transform(test)

# In[38]:

# trainingSummary = lrModel.summary
# roc = trainingSummary.roc.toPandas()
# plt.plot(roc['FPR'],roc['TPR'])
# plt.ylabel('False Positive Rate')
# plt.xlabel('True Positive Rate')
# plt.title('ROC Curve')
# plt.show()
# print('Training set areaUnderROC: ' + str(trainingSummary.areaUnderROC))

# In[39]:

# predictions.select('label', 'features',  'rawPrediction', 'prediction', 'probability').toPandas().head(5)

# In[40]:

##Accuracy of the Raw Model
# accuracy = predictions.filter(predictions.label == predictions.prediction).count() / float(predictions.count())
# print("Initial Test Accuracy LR : ",accuracy)
# lr_accuracy = accuracy

# In[41]:

# evaluator = BinaryClassificationEvaluator()
# print("Test Area Under ROC, Initial LR: " + str(evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})))
# lr_area_roc = evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})

# In[42]:

# print(lr.explainParams())

# In[43]:

# We use a ParamGridBuilder to construct a grid of parameters to search over.
# With 2 values for lr.regParam, 3 values of maxIter
# this grid will have 3 x 2  = 6 parameter settings for CrossValidator to choose from.

# paramGrid = ParamGridBuilder() \
#     .addGrid(lr.regParam, [0.1, 0.01]) \
#     .addGrid(lr.maxIter, [1, 5, 10]) \
#     .build()

# crossval = CrossValidator(estimator=lr,
#                           estimatorParamMaps=paramGrid,
#                           evaluator=BinaryClassificationEvaluator(),
#                           numFolds=5)

## Run cross-validation, and choose the best set of parameters.
# cvModel = crossval.fit(train)

# predictions_cv = cvModel.transform(test)

# accuracy_cv = predictions_cv.filter(predictions_cv.label == predictions_cv.prediction).count() / float(predictions_cv.count())
# print("After CV Test Accuracy LR : ",accuracy_cv)

# In[44]:

from pyspark.ml.classification import GBTClassifier

# In[45]:

gbt = GBTClassifier(labelCol='label', featuresCol='features',
                    maxIter=10)
gbtModel = gbt.fit(train)
predictions = gbtModel.transform(test)

# In[46]:

# Accuracy of the Raw Model

accuracy = predictions.filter(predictions.label
                              == predictions.prediction).count() \
    / float(predictions.count())
print ('Initial Test Accuracy GBT : ', accuracy)
gbt_accuracy = accuracy

# In[47]:

# print(gbt.explainParams())

# In[48]:

evaluator = BinaryClassificationEvaluator()
print 'Test Area Under ROC, Initial GBT: ' \
    + str(evaluator.evaluate(predictions,
          {evaluator.metricName: 'areaUnderROC'}))
gbt_area_roc = evaluator.evaluate(predictions,
                                  {evaluator.metricName: 'areaUnderROC'
                                  })

# In[2]:

paramGrid = ParamGridBuilder().addGrid(gbt.stepSize, [0.01, 0.1,
        1.0]).addGrid(gbt.maxIter, [1, 5, 10]).addGrid(gbt.maxDepth,
        [3, 7]).build()

crossval = CrossValidator(estimator=gbt, estimatorParamMaps=paramGrid,
                          evaluator=BinaryClassificationEvaluator(),
                          numFolds=5)

# Run cross-validation, and choose the best set of parameters.

cvModel = crossval.fit(train)

predictions_cv = cvModel.transform(test)

accuracy_cv = predictions_cv.filter(predictions_cv.label
                                    == predictions_cv.prediction).count() \
    / float(predictions_cv.count())
print ('After Cross Validation Accuracy GBT : ', accuracy_cv)
evaluator = BinaryClassificationEvaluator()
print 'Test Area Under ROC, Cross Validation GBT: ' \
    + str(evaluator.evaluate(predictions_cv,
          {evaluator.metricName: 'areaUnderROC'}))

# In[50]:

# from pyspark.ml.classification import DecisionTreeClassifier

# In[51]:

# dt = DecisionTreeClassifier(labelCol="label", featuresCol="features")
# dtModel = dt.fit(train)
# predictions = dtModel.transform(test)

# In[52]:

##Accuracy of the Raw Model
# accuracy = predictions.filter(predictions.label == predictions.prediction).count() / float(predictions.count())
# print("Initial Test Accuracy DT : ",accuracy)

# In[53]:

# evaluator = BinaryClassificationEvaluator()
# print("Test Area Under ROC, Initial DT: " + str(evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})))

# In[ ]:

# dt_accuracy = accuracy
# dt_area_roc = evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})

# In[54]:

from pyspark.ml.classification import RandomForestClassifier

# In[55]:

rf = RandomForestClassifier(labelCol='label', featuresCol='features',
                            numTrees=10)
rfModel = rf.fit(train)
predictions = rfModel.transform(test)

# In[56]:

# Accuracy of the Raw Model

accuracy = predictions.filter(predictions.label
                              == predictions.prediction).count() \
    / float(predictions.count())
print ('Initial Test Accuracy RF : ', accuracy)

# In[57]:

evaluator = BinaryClassificationEvaluator()
print 'Test Area Under ROC, Initial RF: ' \
    + str(evaluator.evaluate(predictions,
          {evaluator.metricName: 'areaUnderROC'}))

# In[ ]:

rf_accuracy = accuracy
rf_area_roc = evaluator.evaluate(predictions,
                                 {evaluator.metricName: 'areaUnderROC'})

# In[ ]:

paramGrid = ParamGridBuilder().addGrid(gbt.stepSize, [0.01, 0.1,
        1.0]).addGrid(gbt.maxIter, [1, 5, 10]).addGrid(gbt.maxDepth,
        [3, 7]).build()

crossval = CrossValidator(estimator=rf, estimatorParamMaps=paramGrid,
                          evaluator=BinaryClassificationEvaluator(),
                          numFolds=5)

# Run cross-validation, and choose the best set of parameters.

rfModel = crossval.fit(train)

predictions_cv = rfModel.transform(test)

accuracy_cv = predictions_cv.filter(predictions_cv.label
                                    == predictions_cv.prediction).count() \
    / float(predictions_cv.count())
print ('After Cross Validation Accuracy RF : ', accuracy_cv)
evaluator = BinaryClassificationEvaluator()
print 'Test Area Under ROC, Cross Validation RF: ' \
    + str(evaluator.evaluate(predictions_cv,
          {evaluator.metricName: 'areaUnderROC'}))

# In[58]:

# from pyspark.ml.classification import LinearSVC

# In[59]:

# lsvc = LinearSVC(maxIter=10, regParam=0.1, labelCol="label", featuresCol="features")
# lsvcModel = lsvc.fit(train)
# predictions = lsvcModel.transform(test)

# In[60]:

##Accuracy of the Raw Model
# accuracy = predictions.filter(predictions.label == predictions.prediction).count() / float(predictions.count())
# print("Initial Test Accuracy SVC : ",accuracy)

# In[61]:

# evaluator = BinaryClassificationEvaluator()
# print("Test Area Under ROC, Initial SVC: " + str(evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})))

# In[ ]:

# lsvc_accuracy = accuracy
# lsvc_area_roc = evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})

# In[62]:

# from pyspark.ml.classification import NaiveBayes

# In[63]:

# nb = NaiveBayes(labelCol="label", featuresCol="features")
# nbModel = nb.fit(train)
# predictions = nbModel.transform(test)

# In[64]:

##Accuracy of the Raw Model
# accuracy = predictions.filter(predictions.label == predictions.prediction).count() / float(predictions.count())
# print("Initial Test Accuracy NB : ",accuracy)

# In[65]:

# evaluator = BinaryClassificationEvaluator()
# print("Test Area Under ROC, Initial NB: " + str(evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})))

# In[ ]:

# nb_accuracy = accuracy
# nb_area_roc = evaluator.evaluate(predictions, {evaluator.metricName: "areaUnderROC"})

# In[ ]:

modelData = [(gbt_accuracy, gbt_area_roc, 'GBT'), (rf_accuracy,
             rf_area_roc, 'RF')]  #   (nb_accuracy, nb_area_roc , "NB"),
                                  #   (lr_accuracy, lr_area_roc , "LR"),
                                  #   (lsvc_accuracy, lsvc_area_roc , "LSVC"),
                                  #   (dt_accuracy, dt_area_roc , "DT"),

# create DataFrame using data

modelDF = pd.DataFrame(modelData, columns=['accuracy', 'area_roc',
                       'model'])
