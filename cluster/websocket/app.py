import tornado.websocket
import tornado.ioloop
import tornado.web
import logging
import signal
import uuid
import time
import json
import random
import requests

from tornado.log import enable_pretty_logging
from tornado.ioloop import PeriodicCallback
from tornado.websocket import WebSocketClosedError

# PORT = random.randint(5000, 8000)
PORT = 8000
CONTROL = 'control'
ENDPOINT = '/api/v1/server'


enable_pretty_logging()
logger = tornado.log.gen_log
http_client = tornado.httpclient.AsyncHTTPClient()

class LimitHadler(tornado.web.RequestHandler):
    def __init__(self, application, request, monitor, **kwargs):
        super(LimitHadler, self).__init__(application, request, **kwargs)
        self.__monitor = monitor
    
    def post(self,):
        data = json.loads(self.request.body)
        try:
            new_limit = int(data['limit'])
            self.__monitor.set_new_limit(new_limit)
        except Exception as e:
            logger.error('Wrong data set to endpoint "/api/v1/setlimit/", data: {}, error: {}'.format(data, e))

    def get(self, ):
        dict_ ={'limit': self.__monitor.get_limit()}
        self.write(json.dumps(dict_))

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
 
class WSHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request, monitor, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.__client_id = str(uuid.uuid4())
        self.__monitor = monitor
        self.callback = PeriodicCallback(self.do_ping, 5000)
    
    def do_ping(self,):
        try:
            self.ping('ping')
        except:
            logger.info('{} do not answer to ping, dropping...'.format(self.__client_id))
            self.__monitor.remove_client({self.__client_id: self})

    def open(self, ):
        self.__monitor.add_client(self.__client_id, self)
        logger.info('New connection with id: {}'.format(self.__client_id))
 
    async def on_message(self, message):
        logger.info('Message received:  %s' % (message,))
        try:
            await self.process_message(message)
            clients = self.__monitor.get_clients()
            for client in clients:
                for uuid,client_obj in client.items():
                    logger.info('Sending message to {}'.format(uuid))
                    client_obj.write_message("The server says: " + str(message))
                # self.write_message("The server says: " + str(message) + " back at you")
        except WebSocketClosedError:
            logger.error('Was trying to send message to closed socket.')
 
    def on_close(self):
        self.__monitor.remove_client({self.__client_id: self})
        logger.info('Connection closed for {}'.format(self.__client_id))
 
    def check_origin(self, origin):
        return True
    
    async def process_message(self, message):
        logger.info('Working on some heavy task.')
        self.__monitor.add_task()
        await tornado.gen.sleep(10)
        self.__monitor.remove_task()
        return '"{}" was processed by server.'.format(message)


def sig_handler(sig, frame):
    logging.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)

def shutdown():
    logging.info('Stopping http server')
    logging.info('Will shutdown...')
    http_server.stop()
    io_loop = tornado.ioloop.IOLoop.instance()
    io_loop.stop()

class Monitor:

    def __init__(self,):
        self.clients = []
        self.limit = 10
        self.tasks = 0
    
    def set_new_limit(self, new_limit):
        self.limit = new_limit
        logger.info('New limit set to {}'.format(self.limit))
    
    def get_limit(self,):
        return self.limit

    def add_task(self, ):
        self.tasks += 1
        logger.debug('Task added.')

    def remove_task(self,):
        self.tasks -= 1
        logger.debug('Task removed.')

    def add_client(self, client_id, obj):
        dict_ = {client_id: obj}
        self.clients.append(dict_)
        logger.debug('Added client: "{}", list: {}'.format(client_id, self.clients))

    def get_clients(self,):
        return self.clients
    
    def remove_client(self, client_id):
        self.clients.remove(client_id)
        logger.debug('Removed clients: "{}", list: {}'.format(client_id, self.clients))

    def get_stats(self,):
        return {'users': len(self.clients), 'limit': self.limit, 'stamp': int(time.time()), 'port': PORT, 'active_tasks': self.tasks}

    def send_stats(self,):
        stats = self.get_stats()
        http_client.fetch("http://" + CONTROL + ENDPOINT, callback=self.handle_response, method='POST', headers=None, body=json.dumps(stats))

    def handle_response(self, response):
        if response.error:
            logger.error("Error: {}".format(response.error))
        else:
            logger.info("Control server updated.")
            logger.debug('Number of connected clients: {}, tasks: {}'.format(len(self.clients), self.tasks))


if __name__ == "__main__":
    M = Monitor()
    application = tornado.web.Application([
    (r'/', WSHandler, {'monitor': M}),
    (r'/api/v1/limit/?', LimitHadler, {'monitor': M}),
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(PORT)
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    callback = PeriodicCallback(M.send_stats, 6000)
    callback.start()
    print('*** Websocket Server Started on port {}***'.format(PORT))
    tornado.ioloop.IOLoop.instance().start()
