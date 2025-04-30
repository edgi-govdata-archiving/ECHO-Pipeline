# Delta Lake Deployment for Production
This directory contains scripts for ingesting the scraped data (e.g CSV and JSON) from into an on-premise Delta Lake system using PySpark for the production environment. 

## Prerequisites
- Python >3.10
- Java 1.8
- Ubuntu System
- An account with admin or sudo privileges

## How to Use:
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
spark-submit --packages io.delta:delta-spark_2.12:3.3.0 --conf spark.driver.extraJavaOptions="-Divy.cache.dir=/tmp -Divy.home=/tmp" --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" savetolake.py

```

If you are using a different Spark version, refer to this [site](https://docs.delta.io/latest/releases.html) to determine the compatible Delta Lake version.

## License & Copyright
Copyright (C) Environmental Data and Governance Initiative (EDGI) This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the [LICENSE](../LICENSE) file for details.