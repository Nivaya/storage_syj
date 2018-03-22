# -*-coding:utf-8 -*-
from flask_script import Manager, Shell
from livereload import Server
from storage import create_app, db
from storage.model import User
from flask_migrate import Migrate, MigrateCommand
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from config import db_info

app = create_app(db_info)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def run():
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5500)
    IOLoop.instance().start()


@manager.command
def dev():
    server = Server(app.wsgi_app)
    server.watch('**/*.*')
    server.serve()


def make_shell_context():
    return dict(app=app, db=db, User=User)


manager.add_command('shell', Shell(make_context=make_shell_context))

if __name__ == '__main__':
    manager.run()
