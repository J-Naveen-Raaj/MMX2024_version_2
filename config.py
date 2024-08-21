import os

DEBUG = True

#ENV_TYPE can take one of the values: "WINDOWS"  OR "LINUX"
ENV_TYPE = "LINUX"

SECRET_KEY=os.urandom(16)
SESSION_TYPE = 'filesystem'
BASE_DIR = os.path.dirname(__file__)
SESSION_FILE_DIR = os.path.join(BASE_DIR,"session")
SESSION_PERMANENT = True

INPUT_FILES_DIR = os.path.join(BASE_DIR,"app_server","inputs")
OUTPUT_FILES_DIR = os.path.join(BASE_DIR,"app_server","outputs")

# Store locations for optimization input data files, optim output files, optim logs files
OP_INPUT_FILES_DIR = os.path.join(BASE_DIR,"app_server","optim_input")
OP_OUTPUT_FILES_DIR = os.path.join(BASE_DIR,"app_server","optim_output")
OP_LOG_FILES_DIR = os.path.join(BASE_DIR,"app_server","optim_logs")

# Locations of logs for app and db queries
APP_LOG_FILES_DIR = os.path.join(BASE_DIR, "logs")
JSON_SORT_KEYS = False