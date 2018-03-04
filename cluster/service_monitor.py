import requests
import subprocess
import time

from datetime import datetime
from threading import Thread

URL = 'http://localhost/api/v1/server'

if __name__ == "__main__":
    while True:
        USERS = 0
        LIMIT = 0
        DO_WE_NEED_NEW_SERVER = False
        NUM_OF_SERVERS = 0
        r = requests.get(URL)
        data = r.json()
        NUM_OF_SERVERS = len(data)
        for server in data:
            USERS += int(server['users'])
            LIMIT += int(server['limit'])
        PERCENT = int(USERS / LIMIT * 100)
        print('***Check done at: {}***'.format(datetime.now()))
        print('***Current load: {}%, slots used: {} of {}.'.format(PERCENT, USERS, LIMIT))
        if PERCENT > 75:
            print('***Creating new instance of websocket server...')
            subprocess.run(["docker-compose", "scale", "websocket=%d" % (NUM_OF_SERVERS + 1, )])
        elif PERCENT < 25:
            subprocess.run(["docker-compose", "scale", "websocket=%d" % (NUM_OF_SERVERS - 1, )])
        else:
            time.sleep(5)