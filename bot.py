import os, sys
import mwclient

username, pwd = open(os.path.expanduser('~/.config/cpdl')).read().split()

cpdl = mwclient.Site(('http', 'cpdl.org'), path='/wiki/')
cpdl.login(username, pwd)
