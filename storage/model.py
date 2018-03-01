# -*-coding:utf-8 -*-

from flask_login import UserMixin
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# 权限
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), index=True)

    def __repr__(self):
        return '<Role %r>' % self.name


# 用户表
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, index=True)
    password_hash = db.Column(db.String(100))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=3)

    role = db.relationship('Role', backref='roleid')

    def __repr__(self):
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    def verify_password(self, password):
        return self.password_hash == password


# 参考http://flask-login.readthedocs.io/en/latest/
# 用User.query.get(user_id)会报‘AnonymousUserMixin’错
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


# 分类表
class Catalog(db.Model):
    __tablename__ = 'catalog'
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    catalog = db.Column(db.String(30))

    def __repr__(self):
        return '<Catalog %r>' % self.catalog


# 库存主表
class Storage(db.Model):
    __tablename__ = 'storage'
    id = db.Column(db.String(30), primary_key=True, index=True)
    part = db.Column(db.String(30), index=True)
    sn = db.Column(db.String(40), index=True)
    description = db.Column(db.String(100))
    price = db.Column(db.Float)
    purchase_date = db.Column(db.DateTime)
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalog.id'))
    remark = db.Column(db.String(100))
    username = db.Column(db.String(30))
    state = db.Column(db.String(2))
    location = db.Column(db.String(30))
    create_user = db.Column(db.String(30))
    create_date = db.Column(db.DateTime, default=datetime.now)
    modify_user = db.Column(db.String(30))
    modify_date = db.Column(db.DateTime)

    catalog = db.relationship('Catalog', backref='catalogid')

    def __repr__(self):
        return '<Storage %r>' % self.part


# 借还记录
class History(db.Model):
    __tablename__ = 'st_history'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    part_id = db.Column(db.String(30), db.ForeignKey('storage.id'))
    username = db.Column(db.String(10), index=True)
    location = db.Column(db.String(30))
    state = db.Column(db.String(2))
    register_date = db.Column(db.DateTime)
    create_date = db.Column(db.DateTime, default=datetime.now)
    create_user = db.Column(db.String(30))

    part = db.relationship('Storage', backref='partid')

    def __repr__(self):
        return '<History %r>' % self.part_id
