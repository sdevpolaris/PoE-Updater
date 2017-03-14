#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/FlaskApps/poeupdaterApp/")

from FlaskApp import app as application
application.secret_key = 'SECRET_KEY_PLACEHOLDER'