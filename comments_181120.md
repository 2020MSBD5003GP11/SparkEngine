1. A new file GP5003_priyanko.ipynb - added
  a.It has Logistic Regression implemented on the problem
  b.This is in top of Desmonds EDA2.ipynb
  c.I have changed the String Indexing part a little bit - so that it can be included in the pipeline.
2. I cant run the file in Databricks , it is too slow. (Probably because I have chosen the HongKong server , and I am in India now)
3. I have used 50K records from Oct-2019
4. The Accuracy is only 0.64 , even after Cross Validation

Paddy - Can you pls try to upload this notebook in Databricks and see if it can be run ?

Desmond - Can you pls review your data transformation part 
  - a) If the splitting of product_category can be done through LabelEncoder, in that case it can be included in pipeline easily
  - b) Skipping the sampling is Ok at this point , but can you please review with the original notebook it may have missed other transformation as well.
  
 Roy - If possible can you please check what other models can be added + accuracy measures  
  
  I think before 1st dec we need to 
  - More data exploration graphs - like what are the distribution of the purchase events , 
    correlation between no of events in a session and purchase , correlation between brand , product , category etc with purchase event,
    percentage of purchase event when key information like brand , product , category etc missing
  - Can we ask the TA how we can increase the data fetch from Mongo DB ? Or any other features of the Mongo DB integration can be helpful ?
    and how we can efficiently fetch that huge data
  - Revision of data transformation - and clear answer (or some graphical exploration) on why those particular transformations
  - Some graphical measures of Accuracy - like area under ROC , Confusion matrix (I have seen these two for LogisticRegression and will add)
