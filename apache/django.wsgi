import sys
import os
import os.path
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'faxcelerate.settings'
os.environ['LC_ALL'] = 'en_US.utf-8'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
