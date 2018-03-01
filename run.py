# -*-coding:utf-8 -*-
from storage import create_app
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# db参数
db_info = 'root:qq123456@localhost:3306'
app = create_app(db_info)

if __name__ == '__main__':
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5500)
    IOLoop.instance().start()
