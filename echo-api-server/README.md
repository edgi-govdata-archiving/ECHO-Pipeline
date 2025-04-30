# ECHO API Server

The **ECHO API Server** is a backend service designed to serve Delta Lake tables over a RESTful API. It allows users to interact with the stored data efficiently, offering capabilities to read and query the data in a structured manner. The API is built using FastAPI and serves as an interface for interacting with large-scale datasets stored in Delta Lake format, which is commonly used for handling big data.

Currently, this server is designed for users who want to access ECHO data via an API without the need to set up their own Delta Lake infrastructure locally.

## Features
- **REST API** for accessing Delta Lake tables
- Supports reading and querying large datasets through HTTP endpoints
- **SQLite caching layer** to reduce redundant data operations


## Endpoints Overview
| Method | Endpoint         | Description                     |
|--------|------------------|---------------------------------|
| GET | `/auth` | Get a token to access api server
| GET    | `/echo/{table}` | Run a SQL query on a table      |

### `/auth`
Redirects the user to GitHub for authentication. After successful login and permission approval, the user is redirected back with an access token.

### `/echo/{table}`
Query data from a specified table.

- Path Parameters:

    - table_name (string): Name of the Delta table to query

- Query Parameters:
    
    - sql (string): SQL-style statement to get data from the specified table (mandatory)

    - idx_field (string)

    - base_table (string)

    - echo_type (string)

Example
```
GET /echo/ECHO_EXPORTER?sql=SELECT REGISTRY_ID FROM ECHO_EXPORTER LIMIT 1
```

Response

Returns a JSON data.

#### Prerequisities
1. Python >=3.10
2. A GitHub account

Note: If you are running Python version lower than 3.10, you may want to consider Docker.

#### How to Run:

1. Create a python virtual environment
    ```bash
    python3 -m venv venv
    ```

2. Activate the virtual environment

    - On Windows
    ```bash
    venv/Scripts/activate
    ```
    - On MacOS/Linux
    ```bash
    source venv/bin/activate
    ```

3. Install the required dependencies
    ```bash
    pip install -r requirements.txt
    ```

4. Run the api server
    Replace {port} with the desired port number.

    ```bash
    uvicorn main:app --host 0.0.0.0 --port {port}
    ```

####  Environment Variables
Add the following variables to a .env file for this application to run.

Variable | Description | Example
-----|:--------------------------------|:---------
DELTA_LAKE_PATH | Folder with Delta Tables | /home/user/epa-data
GITHUB_CLIENT_ID | Client ID given by GitHub | clientid
GITHUB_CLIENT_SECRET | Client secret giveb by GitHub| supersecretkey


Tip: You can use python-dotenv to automatically load variables from a .env file.

####