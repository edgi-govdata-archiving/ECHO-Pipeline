import json
import queue
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import urllib3
import os
import logging
from file_utilities import *
from datetime import datetime

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(log_dir, f'{timestamp}.log')
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)

# Error about site certificate not being valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def is_file(url):
    try:
        # Send a HEAD request to get headers without downloading the content
        response = requests.head(url, allow_redirects=True, verify=False)
        # Check the content type in the headers
        if 'Content-Type' in response.headers:
            # If the content type is not a directory, assume it's a file
            content_type = response.headers['Content-Type']
            if 'text/html' in content_type:
                # For directories, the content type might be HTML or redirected (could point to a listing page)
                return False
            return True

        # If no content type, it could be a directory (like when it returns a listing page)
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking URL: {e}")
        return -1


def fetch_links(url):
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: {response.status_code}")

    soup = BeautifulSoup(response.content, "html.parser")
    table_rows = soup.find('table').find_all('tr')
    return table_rows


def convert_to_mb(size_str):
    if size_str == '-':
        return size_str
    # Extract the number and unit from the string
    size, unit = float(size_str[:-1]), size_str[-1].upper()
    if unit.isdigit():
        return size_str
    # Convert the size to bytes based on the unit
    if unit == 'K':
        size_in_bytes = size * 1024  # 1 KB = 1024 bytes
    elif unit == 'M':
        size_in_bytes = size * 1024 ** 2  # 1 MB = 1024^2 bytes
    elif unit == 'G':
        size_in_bytes = size * 1024 ** 3  # 1 GB = 1024^3 bytes
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    # Convert bytes to megabytes
    size_in_mb = size_in_bytes / 1024 ** 2
    return f'{size_in_mb:.2f}'


def convert_string_to_timestamp(timestamp_str):
    format_str = "%Y-%m-%d %H:%M"  # Format matches your timestamp
    return datetime.strptime(timestamp_str, format_str)


def convert_timestamp_to_string(timestamp):
    format_str = "%Y-%m-%d %H:%M"  # Format matches your timestamp
    return datetime.strftime(timestamp, format_str)


def log_error_files(contents):
    error_file = 'errors'
    if not os.path.exists(error_file):
        with open(error_file, "w", encoding="utf-8") as file:
            file.write(contents)
    else:
        with open(error_file, "a", encoding="utf-8") as file:
            file.write(contents)


# Load existing metadata
def load_metadata(file_path='datasets_info.json'):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # First run, no metadata yet


# Save metadata after updates
def save_metadata(data, file_path='datasets_info.json'):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def crawl_page(base_url, metadata_file):
    # Initialize a queue to manage URLs to be processed
    q = queue.Queue()
    q.put(base_url)
    files = load_metadata()
    updated_files = []

    # Process URLs in the queue until it's empty
    while not q.empty():
        url = q.get()
        logging.info(url)
        try:
            rows = fetch_links(url)
        except Exception as e:
            logging.error(f"Error fetching links from {url}: {e}")
            continue

        # Iterate over each row in the fetched table
        for row in rows:
            # Find the anchor tag with a href attribute
            a_tag = row.find('a', href=True)
            if not a_tag:
                continue
            if a_tag.text.strip() == 'Parent Directory' or a_tag.text.strip() == 'Name':
                continue

            # Extract the href link and construct the full URL
            href = a_tag['href']
            full_url = urljoin(url, href)
            # print(full_url)

            # Check if the link points to a file or directory
            file_check = is_file(full_url)
            if file_check is None:
                logging.warning(f'Unable to determine if {full_url} is a file or directory')
                continue
            # If it's a directory, add its URL to the queue for processing
            elif not file_check:
                logging.info(f'{full_url} is a directory')
                q.put(full_url)
                continue

            logging.info(f'{full_url} is a file')

            cells = row.find_all('td', align='right')
            timestamp = cells[0].text.strip() if len(cells) > 0 else None  # Extract timestamp if available
            size = convert_to_mb(cells[1].text.strip()) if len(cells) > 1 else None  # Extract size if available

            file_info = {
                'link': full_url,  # Full URL to the file
                'last_modified': timestamp,  # Timestamp of the file if available
                'size(mb)': size  # Size of the file if available
            }
            # If it's a file, append its information to the files list
            stored_last_modified = files.get(href, {}).get('last_modified')
            if not stored_last_modified or convert_string_to_timestamp(timestamp) > convert_string_to_timestamp(
                    stored_last_modified):
                logging.info(f'{full_url} is a new file, adding to updated files list')
                files[href] = file_info
                updated_files.append((href, full_url, convert_string_to_timestamp(timestamp).timestamp()))
            else:
                logging.info(f'{full_url} has not been updated since last time, skipping')

    # Return the collected list of file information
    save_metadata(files)
    return updated_files


def edit_json(file_name, entry):
    files_info = load_metadata()
    (key, value) = entry
    files_info[file_name][key] = value
    save_metadata(files_info)


def main():
    # Base URL of the website
    BASE_URL = "https://echo.epa.gov/files/echodownloads/"
    METADATA_FILE = "datasets_info.json"
    BASE_LOCAL_PATH = "data"

    try:
        updated_files_to_download = crawl_page(BASE_URL, METADATA_FILE)
        logging.info(f'Done scraping {BASE_URL}')
        logging.info(f'Beginning file download')

        for file_name, download_link, last_modified_timestamp in updated_files_to_download:
            try:
                parsed_url = urlparse(download_link)
                file_path = parsed_url.path.lstrip('/')  # Remove leading '/' to avoid issues
                download_file(download_link, os.path.join(BASE_LOCAL_PATH, os.path.dirname(file_path)),
                              last_modified_timestamp, need_extracting=False)

                # Add file's location on local directory
                edit_json(file_name, ("file_location", os.path.join(BASE_LOCAL_PATH, file_path)))

            except Exception as download_error:
                logging.error(f"Error downloading {download_link}: {download_error}")
                log_error_files(f"{download_link}: {download_error}")
                continue
    except Exception as e:
        logging.critical(f"Error: {e}")


if __name__ == "__main__":
    main()
