# Data Storer Development

This directory contains scripts for storing the scraped data (e.g CSV and JSON) from ECHO into delta lake using pyspark. 


## How to Run:
### Running in Docker
1. After verifying the containers are running, access the storer container's shell using the following command:
    ```bash
    docker compose -f dev-compose.yaml storer exec bash
    ```

2. Run the savetolake.py script:
    ```bash
    python3 savetolake.py
    ```

### Setting up a Cron Job
You can automate running this container at a scheduled time using a cron job.

1. Open your crontab for editing.
    ```bash
    crontab -e
    ```

2. Add a line to schedule the job. For example, to run the container every Monday at 8am, add the following line.
    ```bash
    0 8 * * 1 docker compose restart storer
    ```


####  Logs
Script progress and errors are logged in the logs/ folder, with each run creating a new log file with timestamp of script start as the name.

#### Want to add more files?
You can add csv files to delta lake by doing the following:
1. Add the csv file of choice in the **updated-datasets**. This folder is found under the **STORAGE_MOUNT_PATH**
2. Add a schema file in **{JSON_DIR_MOUNT_PATH}/schemas** corresponding to the header of the csv file of choice. You can follow a template of a schema file under *json/schemas* of this repository.
3. Add the csv and schema pairing in the *spark_csv_mapping.json*. This may be found in the **JSON_DIR_MOUNT_PATH**.
4. Run the script. 