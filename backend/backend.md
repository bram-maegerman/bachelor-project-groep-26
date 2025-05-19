# Fast-API backend
This fast-api script sets up a backend with an endpoint to call our scan-checker script.

## How to use
Make sure fastapi and uvicorn is installed.

Use the following command to start it up in dev mode:

````
fastapi dev backend.py
````

It should use the `127.0.0.01:8000` as the port for the application, unless configured otherwise. 

The script is configured to run on endpoint `/scan-checker`. The response is a streaming response, meaning it should send the output live to the user instead of sending it all when the script is finished. 