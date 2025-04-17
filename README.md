# Project Description
This project is the final project for COMP646 in Rice U.


## Init project
1. run `poetry install` to install dependency of this project
2. run `docker-compose up -d` or `docker compose up -d` to run the docker of mysql dataset
3. edit `.env` file to edit the setting of this project
4. run `poetry run python main.py` to run the backend of this project

## Password
agent_backend

## Access Swagger Document
Visit 127.0.0.1:8888/api/docs to access the swagger document

## User Authorization
In swagger document, execute Post /api/monitor/seed-user to register a test user in the database (just once)

Click the "Authorize button", enter "test-token-abc123" then click "Authorize" to do the authorization.



# Start a Run with Image

**Add boto3 into poetry first:**

``poetry add boto3``



1. 上传图片至 AWS S3 buckets，获得公网URL



2. 
