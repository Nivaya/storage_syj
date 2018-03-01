# -*-coding:utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

db = SQLAlchemy()
bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = '/index?login_required=1'
login_manager.login_message = u'请登录您的账户'
login_manager.login_message_category = 'error'


def create_app(db_info):
    app = Flask(__name__)
    app.secret_key = 'secury code'
    # app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://' + db_info + '/stdb'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    # app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    from .view import init_views
    init_views(app)
    return app
