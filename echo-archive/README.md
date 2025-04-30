# Echo Archive Documentation

# Overview
This folder contains a Python-based script for mirroring and archiving ECHO Downloads. It scans the website for downloadable file links, downloads them, and stores them in a local folder structure that mirrors the website's organization. The goal is to create a local archive for backup, offline access, or data ingestion.

## Folder Structure

```
logs/                   # Directory for log files (download history, errors, etc.)
datasets_info.json      # JSON file that tracks downloaded files and metadata
Dockerfile              # Dockerfile to containerize the application
echo_dataset_downloader.py  # Main script for crawling and downloading files
file_utilities.py       # Utility functions for file operations
README.md               # Project documentation
requirements.txt        # Python dependencies
```

## How to Use
### Running with Docker
1. Build the docker image using provided `Dockerfile`.
    ```bash
    docker build . -t {image_name}
    ```
2. Run the container and mount volumes to persist downloaded data:
    ```bash
    docker run -v {path_in_local_machine}:{path_in_container} {image_name}
    ```
Example:
    ```bash
    docker run -v /home/user/echodata:/app/echodata echo-archiver
    ```
### Setting up a Cron Job
You can schedule automatic updates by setting up a cron job:

1. Open your crontab for editing.
    ```bash
    crontab -e
    ```

2. Add a line to schedule the job. For example, to check for updates every Monday at 8am, add the following line.
    ```bash
    0 8 * * 1 docker docker run -v {path_in_local_machine}:{path_in_container} {image_name}
    ```

This ensures your datasets stay updated on a weekly basis without manual intervention.

## Notes

- Incremental Downloads:
    - `datasets_info.json` is automatically managed by the script.
    - If it exists, the script checks the last_modified date of each file entry and only downloads new or updated files.
    - To force a full re-download of all datasets, simply delete `datasets_info.json`.


## License
