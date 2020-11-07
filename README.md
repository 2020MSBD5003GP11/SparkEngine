# SparkEngine

```bash
docker pull jupyter/pyspark-notebook
docker run -it --rm -p 50024:8888 -v $PWD:/home/jovyan/work jupyter/pyspark-notebook jupyter notebook --ip='*' --NotebookApp.token='' --NotebookApp.password=''
```
[Open](http://localhost:50024/)
