from tornado import httpserver, httpclient
from tornado import gen
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.log import enable_pretty_logging

import tornado.web
import json
import time

WAIT_FOR_NEW_UPDATE = 15 # Expect updates from servers every 15 seconds.

enable_pretty_logging()
logger = tornado.log.gen_log

global servers
servers = []
http_client = httpclient.AsyncHTTPClient()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Go to /api/v1/server/.')

class UpdateHandler(tornado.web.RequestHandler):

    def update(self, data):
        logger.info('Current servers: {}'.format(servers))
        for server in servers:
            if data['ip'] == server['ip']:
                if data['port'] == server['port']:
                    servers.remove(server)
                    servers.append(data)
                    logger.debug('Stats for {}:{} updated...'.format(data['ip'], data['port']))
                    return
        logger.info('Adding new server {}:{}'.format(data['ip'], data['port']))
        servers.append(data)

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self):
        json_ = json.dumps(servers)
        self.write(json_)

    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body)
        data['ip'] = self.request.remote_ip
        self.update(data)
        logger.debug('Recived valid json: "{}" from {}'.format(data, data['ip']))

class GetFree(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    @tornado.gen.coroutine
    def get(self,):
        item_to_serve = {'service_info': {'servers': servers}}
        if servers:
            for server in servers:
                if server['users'] < server['limit']:
                    item_to_serve['free'] = server
                else:
                    item_to_serve['free'] = 'No avaliable servers'

        else:
            json_ = item_to_serve['free'] = 'No avaliable servers'

        json_ = json.dumps(item_to_serve)        
        self.write(json_)

class SetLimit(tornado.web.RequestHandler):
    
    def get(self,):
        template = t.generate(servers=servers)
        self.write(template)
    
    def post(self,):
        new_limit = {'limit': self.get_argument('limit')}
        ip = self.get_argument('ip')
        port = self.get_argument('port')
        logger.info('Trying to set new limit for {}:{}'.format(ip, port))
        http_client.fetch("http://{}:{}/api/v1/limit/".format(ip, port), method='POST', headers=None, body=json.dumps(new_limit))
        

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/?", MainHandler),
            (r"/api/v1/server/?", UpdateHandler),
            (r"/api/v1/free/?", GetFree),
            (r"/api/v1/limits/?", SetLimit),
        ]
        tornado.web.Application.__init__(self, handlers)

def check_dead():
    seconds = int(time.time()) - WAIT_FOR_NEW_UPDATE
    logger.info('Checking for dead servers...')
    logger.debug('Current clients: {}'.format(servers))
    for server in servers:
        if server['stamp'] < seconds:
            logger.info('Server {}:{} removed from active list.'.format(server['ip'], server['port']))
            servers.remove(server)

def main():
    app = Application()
    app.listen(80)
    callback = PeriodicCallback(check_dead, 10000)
    callback.start()
    print('*** REST Server Started***')
    IOLoop.instance().start()

t = tornado.template.Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Set limits</title>
</head>
<body>
    {% for server in servers %}
    <form action="/api/v1/limits/" method="POST">
        For {{server['ip']}}:{{server['port']}} limit set to {{server['limit']}}:<br>
        Set your new limit: 
        <input type="text" name="limit"><br>
        <input type="hidden" name="ip" value="{{server['ip']}}">
        <input type="hidden" name="port" value="{{server['port']}}">
    </form> 
    {% end %}
</body>
</html>""")

if __name__ == '__main__':
    main()