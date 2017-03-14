#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/FlaskApps/poeupdaterApp/")

# home refers to home.py here
from home import app as application
application.secret_key = 'SECRET_KEY_PLACEHOLDER'