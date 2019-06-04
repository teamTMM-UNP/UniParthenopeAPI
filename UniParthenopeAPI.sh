#! /bin/bash

# Activate the virtual environment
. venv/bin/activate

# Set the flask application
export FLASK_APP=app.py

# Run flask
flask run --host=0.0.0.0 --port=8080
