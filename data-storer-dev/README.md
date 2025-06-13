# Data Storer Development

This directory contains scripts for ingesting the scraped data (e.g CSV and JSON) from the data-scraper tool into the Delta Lake docker container based on the Delta Lake Quickstart Docker using PySpark.


## How to Run:
### Running in Docker

**NOTE**: If you use Docker Desktop, increase the limits of several resource allocations. We tested the containers with 8 CPU, 12 GB Memory limit, and 4 GB Swap size. This will prevent the Out of Memory errors. 

1. After verifying the containers are running, access the storer container's shell using the following command:
    ```bash
    docker compose -f dev-compose.yaml exec storer bash
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

## Adding a New File
To ingest new CSV files into Delta Lake:
1. Copy your desired CSV file into the ***updated-datasets** folder. This directory is located under the `STORAGE_HOST_PATH`configured in your Docker Compose file.
2. Add or update the schema.
    - If the CSV has a new schema or format, ensure that a corresponding JSON schema file exists.
    - Follow the instructions in the [json/README.md](../json/README.md) to define the schema and link it correctly to the CSV file.
3. Ingest the data.

## License & Copyright
Copyright (C) Environmental Data and Governance Initiative (EDGI) This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the [LICENSE](../LICENSE) file for details.
