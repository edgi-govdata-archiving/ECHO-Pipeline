# Data Scraper Documentation
This directory contains scripts to download CSV files and scrape the matching schemas from (the EPA site)[https://echo.epa.gov/tools/data-downloads].

## Directory Structure
    Dockerfile    # Docker image definition
    echo_dataset_downloader.py # Script to download the CSV datasets
    echo_schema_getter.py # Script to scrape the schema definition 
    file_utilities.py # Utility functions to deal with file operations
    schema_utilities.py # Utility functions to deal with schema creation and handling
    main.py        # Main script
    README.md     # Project documentation

## How to Use
### Building and Running with Docker
1. Create a .env file at the root of the echo-pipeline directory (next to the docker-compose.yaml file). Docker Compose will use this file to inject environment variables into the container at runtime.

    | Variable Name | Description | Example Path                         |
    |-----------------------------|----------------------------------------|----------|
    | `LOCAL_ECHODOWNLOADS_HOST_PATH` | Path on the host where raw ECHO downloads are stored               | `/home/user/echo-downloads`          |
    | `STORAGE_HOST_PATH`             | Path on the host where processed files and outputs will be stored   | `/home/user/epa-data`                |
    | `JSON_DIR_HOST_PATH`           | Path on the host containing schema definition JSON files            | `/home/user/json-schemas`            |

    These host paths are mounted into the container at the following internal paths:

    - /app/echo-downloads ← LOCAL_ECHODOWNLOADS_HOST_PATH

    - /app/epa-data ← STORAGE_HOST_PATH

    - /app/json ← JSON_DIR_HOST_PATH
    
2. Run the docker compose file.
    ```bash
        docker compose build 
    ```

3. Start the container in the docker compose file.
    ```bash
        docker compose up -d scraper
    ```

4. After verifying the containers are running, access the container's shell using the following command:
    ```bash
        docker compose -f dev-compose.yaml exec scraper bash
    ```

### Setting up a Cron Job
You can automate running this container at a scheduled time using a cron job.

1. Open your crontab for editing.
    ```bash
    crontab -e
    ```

2. Add a line to schedule the job. For example, to run the container every Monday at 8am, add the following line.
    ```bash
    0 8 * * 1 docker compose restart scraper
    ```

## License & Copyright
Copyright (C) Environmental Data and Governance Initiative (EDGI) This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the [LICENSE](../LICENSE) file for details.
