# Delta Lake Deployment for Production
This delta lake deployment is for users who want to install spark locally without using Docker. This has the same functionalities as data-storer-dev without the use of Docker.

## Prerequisites
- Python >3.10
- Java 1.8
- Ubuntu System
- An account with admin or sudo privileges

## How to run the application:
Clone this repository.

### Installing Spark

Install spark in the current directory following this article: [Spark Installation](https://phoenixnap.com/kb/install-spark-on-ubuntu)

It is enough to run spark as a local instance in this case but if you want to start master and worker nodes, there are configuration options you can use to best fit your demands. You can find such options in the Spark documentation: [Documentation](https://spark.apache.org/docs/latest/spark-standalone.html#starting-a-cluster-manually)

### Running Delta Lake
Once you have made sure spark is running and installed, go to data-storer-production folder and create a virtual environment. A virtual environment allows you to install multiple python libraries specific to your project while keeping them isolated from the rest of your projects.
```
python -m venv venv
```
Activate the virtual environment using the command below and the command line would now have a (venv)
```
source venv/bin/activate
```
You can now run the delta lake application by simply running the following.
```
python savetolake.py
```

## Features
This directory has three scripts that handle data ingestion:
1. savetolake.py

    `savetolake` is the main script that handles ingesting CSV data into Delta Tables and creating materialized views that can later be used for data analysis.

2. mview_functions.py

    `mview_functions` has functions that create materialized views of the CSV data that are ingested. It uses `spark_materialized_views.json` to determine materialized views to make.

3. EXP_PGM.py

    `EXP_PGM` creates a lookup table for the ECHO data.
    