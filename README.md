# ECHO Pipeline Project Documentation

This project developed a data pipeline system to enhance the archiving system and the data science tools that the Environmental Data & Governance Initiative (EDGI)’s [Environmental Enforcement Watch](https://www.environmentalenforcementwatch.org/) program has developed. This project developed both an on-premise and dockerized delta lake platform harnessing the latest and stable open source technologies. All up-to-date datasets on the EPA Enforcement and Compliance History Online (ECHO) website can be automatically archived and curated in the delta lake system for data processing and query services. To harness this newly streamlined open delta lake technologies, the previously developed [EDGI’s ECHO_modules](https://github.com/edgi-govdata-archiving/ECHO_modules) was updated and added to the current repo as a branch. The project also developed a fast and tiny RESTful API server that can receive a query request from a client who uses the updated API supporting EDGI’s ([ECHO_modules_delta](https://github.com/edgi-govdata-archiving/ECHO_modules/tree/echo-modules-delta)) and return the query result from the on-premise delta lake system to the client. Any data analytics tools using the EDGI’s ECHO_modules_delta can easily access the ingested EPA ECHO datasets via the RESTful API service. 

This project consist of the following components:

### 1. echo-archive ([Documentation](echo-archive/README.md))
This directory contains scripts for mirroring and archiving the [ECHO Downloads](https://echo.epa.gov/files/echodownloads/) site. It scans the website for downloadable file links, downloads them, and stores them in a local folder structure that mirrors the website's organization. The goal is to create a local archive for backup, offline access, or data ingestion by the next data-scraper tool.

### 2. data-scraper ([Documentation](data-scraper/README.md))
This directory contains scripts to download CSV files and scrape the matching schemas from (the EPA site)[https://echo.epa.gov/tools/data-downloads]. The system is containerized using Docker for portability and reproducibility.

### 3. data-storer-dev ([Documentation](data-storer-dev/README.md))
This directory contains scripts for ingesting the scraped data (e.g CSV and JSON) from the data-scraper tool into the Delta Lake docker container based on the Delta Lake Quickstart Docker using PySpark. While this tool was created for the development environment, it can be deployed as a local Delta Lake system so analysts using the ECHO_modules_delta can directly access the ingested ECHO tables in the local Delta Lake system.

### 4. data-storer-production ([Documentation](data-storer-production/README.md))
This directory contains scripts for ingesting the scraped data (e.g CSV and JSON) from into an on-premise Delta Lake system using PySpark for the production environment. The on-premise Delta Lake deployment is used for the ECHO API service.

### 5. echo-api-server ([Documentation](echo-api-server/README.md))
This directory contains scripts for deploying the api server that can receive a query request from a client who uses the ECHO_modules_delta and return the query result from the on-premise Delta Lake system to the client. The server is built using fastapi. Refer to the directory's README.md for instructions on running the application.

### 6. json ([Documentation](json/README.md))
This directory contains the schema files and additional configuration files used by ECHO_Pipeline.


## How to use
1. Set up your `.env` file based on the provided `.env.example` file.
    
    Variable | Description | Example
    ---------|-------------|--------
    | STORAGE_HOST_PATH | Path on the host machine where updated datasets and delta tables will be stored | /home/user/epa-data
    LOCAL_ECHODOWNLOADS_HOST_PATH | Path on the host machine where raw ECHO downloads are stored | /home/user/echo-downloads
    JSON_DIR_HOST_PATH | Path on the host machine containing schema definition JSON files, and other JSON files used in the pipeline | home/user/json

    These host paths are mounted into the containers at the following internal paths:

    - /app/echo-downloads ← LOCAL_ECHODOWNLOADS_HOST_PATH

    - /app/epa-data ← STORAGE_HOST_PATH

    - /app/json ← JSON_DIR_HOST_PATH

2. Build the docker containers by using `docker compose` command:
    ```bash
    docker compose -f dev-compose.yaml build
    ```
    **NOTE**: If you use Docker Desktop, increase the limits of several resource allocations. We tested the containers with 8 CPU, 12 GB Memory limit, and 4 GB Swap size. This will prevent the Out of Memory errors. 
    
4. Start the containers:
    ```bash
    docker compose -f dev-compose.yaml up
    ```
This will start the containers defined in **dev-compose.yaml** which are scraper and storer services. The scraper's main script will run upon container starting but you will have to start storer on your own. 

Notes
- Ensure that the paths defined in your .env file is accessible and correctly mounted within the containers.
- For detailed usage and individual directory instructions, refer to the individual `README.md` files in each directory.

## Code of Conduct
This repository falls under EDGI’s Code of Conduct <https://github.com/edgi-govdata-archiving/overview/blob/main/CONDUCT.md>. Please take a moment to review it before commenting on or creating issues and pull requests.

## Contributors
- Sung-Gheel Jang <https://github.com/@sunggheel> (Organizer, Project Management, Code, Tests, Documentation, Reviews)
- Yemoe Aung <https://github.com/@yemoeaung1> (Code, Tests, Documentation, Reviews)

## License & Copyright
Copyright (C) Environmental Data and Governance Initiative (EDGI) This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the [LICENSE](LICENSE) file for details.
