import os

IP = "127.0.0.1"
PORT = 8880
RETRY = 5
CODE = 'chenjunmin'
MAXSIZE = 1000000000
ACCOUNTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'accounts.json')
LOGFILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logger', 'logs.log')
USERDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'User')
CFILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core', 'services.so')

