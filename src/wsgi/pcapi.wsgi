import os, sys

pwd = os.path.dirname(os.path.realpath(__file__))

paths = os.path.dirname(__file__).split("/")

# TODO: SOMEONE HAS TO FIX THOSE ASSUMPTIONS
root_path = os.sep.join((os.environ['HOME'], 'local', 'pcapi'))

# append the root directory in your python system path
sys.path.append(root_path)

#print sys.path

## Change working directory so relative paths work
pwd = os.path.dirname(os.path.realpath(__file__))
os.chdir(pwd)

## Also add library to the python path
sys.path.append(os.path.join(pwd,'../lib'))
sys.path.append(pwd)

# activate the virtual environment
activate_this = os.path.join(root_path, "bin", "activate_this.py")
execfile(activate_this, dict(__file__=activate_this))

os.environ['ROOT_PATH'] = root_path

import bottle

import pcapi_routes
application = bottle.default_app()
