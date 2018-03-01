# -*-coding:utf-8 -*-
from flask_script import Manager, Shell
from livereload import Server
from storage import create_app, db
from storage.model import User
from flask_migrate import Migrate, MigrateCommand

# db参数
db_info = 'root:qq123456@localhost:3306'

app = create_app(db_info)
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


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
