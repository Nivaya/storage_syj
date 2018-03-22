# -*-coding:utf-8 -*-
from flask import render_template, redirect, url_for, flash, request, jsonify, g
from form import LoginForm, RegisterForm
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from model import User, Storage, Catalog, History, Role
from api import Api
from . import db
import json
import datetime
import decimal


def init_views(app):
    class DataEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return datetime.strftime(obj, '%Y-%m-%d %H:%M').replace(' 00:00', '')
            elif isinstance(obj, datetime.date):
                return datetime.strftime(obj, '%Y-%m-%d')
            elif isinstance(obj, decimal.Decimal):
                return str(obj)
            elif isinstance(obj, float):
                return round(obj, 8)
            return json.JSONEncoder.default(self, obj)

    # @app.template_filter('eip_format')
    def eip_format(data):
        return json.dumps(data, json.dumps, cls=DataEncoder, ensure_ascii=False, indent=2)

    @app.before_request
    def before_request():
        g.user = current_user
        g.para = {'iflogin': request.args.get('login_required') or 'default'}
        g.islogin = login()
        g.catalog = db.session.execute('SELECT ca.id, ca.catalog FROM stdb.catalog ca')

    @app.teardown_request
    def teardown_request(exception):
        db.session.close()

    # 登录
    @app.route('/', methods=['GET', 'POST'])
    @app.route('/index', methods=['GET', 'POST'])
    def index():
        if g.islogin == 'ok':
            return redirect(url_for('index'))
        elif g.islogin == 'mistake':
            return redirect('/index?login_required=1')
        g.para.update({'page': 'index'})
        return render_template('index.html',
                               login_form=LoginForm(),
                               para=g.para,
                               page={})

    # 是否登陆成功
    def login():
        login_form = LoginForm()
        if login_form.lg_submit.data and login_form.validate_on_submit():
            user = User.query.filter_by(username=login_form.username.data).first()
            # 验证密码
            if user is not None and user.verify_password(login_form.password.data):
                login_user(user, login_form.remember.data)
                return 'ok'
            flash(u'用户名或者密码错误！', 'error')
            return 'mistake'
        # 注册成功时显示flash
        if g.para['iflogin'] == '2':
            flash(u'注册成功！现在您可以登录了', 'success')
        return 0

    # 注册
    # @app.route('/register', methods=['GET', 'POST'])
    def register():
        register_form = RegisterForm()
        if g.islogin == 'ok':
            return redirect(url_for('index'))
        elif g.islogin == 'mistake':
            return redirect('/register?login_required=1')
        if register_form.re_submit.data and register_form.validate_on_submit():
            user = User(username=register_form.username.data,
                        password_hash=register_form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect('/index?login_required=2')
        return render_template('register.html',
                               login_form=LoginForm(),
                               register_form=register_form,
                               para=g.para,
                               page={})

    # 登出
    @app.route('/logout', methods=['GET', 'POST'])
    @login_required
    def logout():
        logout_user()
        return redirect('#')

    # 库存查询
    @app.route('/storage', methods=['GET', 'POST'])
    @login_required
    def storage():
        para = {'page_index': request.args.get('page', 1, type=int),
                'catalog_id': request.args.get('catalog_id', ''),
                'query': request.args.get('query', ''),
                'part': request.args.get('part', ''),
                'id': request.args.get('id', ''),
                'sn': request.args.get('sn', ''),
                'username': request.args.get('username', ''),
                'location': request.args.get('location', ''),
                'state': request.args.get('state', ''),
                'ifedit': 'N' if g.user.password_hash == '123456' else 'Y'}

        storages = db.session.query(Storage, Catalog).join(Catalog).filter('''
                (storage.catalog_id=:catalog_id or :catalog_id ='')
                and (storage.part like concat('%',:part,'%') or :part ='')
                and (storage.location like concat('%',:location,'%') or :location ='')
                and (storage.username like concat('%',:username,'%') or :username ='')
                and (storage.sn like concat('%',:sn,'%') or :sn ='')
                and (storage.id like concat('%',:id,'%') or :id ='')
                and (storage.state=:state or :state ='')
            ''').params(catalog_id=para['catalog_id'],
                        query=para['query'],
                        part=para['part'],
                        location=para['location'],
                        username=para['username'],
                        sn=para['sn'],
                        id=para['id'],
                        state=para['state']).order_by(Storage.id)
        pagination = storages.paginate(para['page_index'], per_page=15, error_out=False)
        storages = pagination.items

        g.para.update({'page': 'storage'})
        return render_template('storage.html',
                               login_form=LoginForm(),
                               para=g.para,
                               catalog=g.catalog,
                               page=eip_format(para),
                               storages=storages if para['query'] else [],
                               pagination=pagination if para['query'] else [])

    # 详情
    @app.route('/storage.detail', methods=['POST'])
    @login_required
    def detail():
        if g.user.role_id == 3:
            return 'Powerless'
        para = {'id': request.form.get('id')}
        part = db.session.execute(u'''
          select st.*,ca.catalog,
                CASE st.location WHEN '仓库' THEN '1' ELSE '0' END AS 'exit',
                CASE st.location WHEN '仓库' THEN '' ELSE 'disabled' END AS 'disabled'
          from stdb.storage st
          left join stdb.catalog ca on ca.id=st.catalog_id
          where st.id=:id
       ''', {'id': para['id']})
        part = [dict(r) for r in part]
        for k, v in part[0].items():
            if k == 'purchase_date' and v:
                part[0][k] = v.strftime("%Y-%m-%d")
        return jsonify(part)

    # 保存
    @app.route('/storage.save', methods=['POST'])
    @login_required
    def save():
        if g.user.role_id == 3:
            return 'Powerless'
        sql = ''
        para = Api.reqs('catalog_id,part,id,sn,username,location,state,description,'
                        'remark,type,exit,attr1,attr2')
        para.update({
            # 不填默认今天
            'purchase_date': request.form.get('purchase_date') or datetime.datetime.today().strftime('%Y-%m-%d'),
            # 不填默认0元
            'price': request.form.get('price') or 0,
            # 不填默认今天
            'register_date': request.form.get('register_date') or datetime.datetime.today().strftime('%Y-%m-%d'),
            'engname': g.user.username})
        # 批量返还
        ids = request.form.getlist('ids')
        if len(ids):
            for i in ids:
                para['id'] = i
                sql = u"call history_p(:id, '仓库', '仓库', '0', :register_date, :engname);"
                db.session.execute(sql, para)
                db.session.commit()
            return u'批量返还ok'
        if para['type'] == 'update':
            sql = '''
                UPDATE stdb.storage st
                    SET st.state=:state,
                        st.sn=:sn,
                        st.price=:price,
                        st.description=:description,
                        st.catalog_id=:catalog_id,
                        st.remark=:remark,
                        st.part=:part,
                        st.purchase_date=:purchase_date,
                        {0}
                        st.modify_date=now(),
                        st.modify_user=:engname
                    WHERE st.id=:id
            '''.format('st.username=:username,st.location=:location,' if g.user.role_id == 1 else '')
        elif para['type'] == 'insert':
            checkid = Storage.query.filter_by(id=para['id']).all()
            if len(checkid):
                return 'exist'
            # 笔记本&主机类型
            if para['attr1'] or para['attr2']:
                power = Catalog.query.filter_by(catalog=u'电源适配器').first().id
                mouse = Catalog.query.filter_by(catalog=u'鼠标').first().id
                keyboard = Catalog.query.filter_by(catalog=u'键盘').first().id
                special_ct = Catalog.query.filter_by(id=para['catalog_id']).first().catalog
                if special_ct in [u'笔记本电脑', u'主机']:
                    obj = [
                        Storage(id=para['id'], username=u'仓库', state=para['state'], sn=para['sn'],
                                price=para['price'], part=para['part'],
                                description=para['description'], catalog_id=para['catalog_id'], remark=para['remark'],
                                purchase_date=para['purchase_date'], location=u'仓库',
                                create_user=para['engname']),
                        Storage(id=para['id'] + '-01', username=u'仓库', state=para['state'], sn=para['sn'],
                                part=para['part'] + (u'-电源适配器' if special_ct == u'笔记本电脑' else u'-鼠标'),
                                catalog_id=power if special_ct == u'笔记本电脑' else mouse,
                                remark=para['remark'], price=0, description=para['description'],
                                purchase_date=para['purchase_date'], location=u'仓库',
                                create_user=para['engname']) if para['attr1'] else None,
                        Storage(id=para['id'] + '-02', username=u'仓库', state=para['state'], sn=para['sn'],
                                part=para['part'] + (u'-鼠标' if special_ct == u'笔记本电脑' else u'-键盘'),
                                catalog_id=mouse if special_ct == u'笔记本电脑' else keyboard,
                                remark=para['remark'], description=para['description'], price=0,
                                purchase_date=para['purchase_date'], location=u'仓库',
                                create_user=para['engname'] if para['attr2'] else None)
                    ]
                    db.session.add_all([i for i in obj if i])
                    db.session.commit()
                    return 'ok'
            else:
                sql = u'''
                INSERT INTO stdb.storage (id,username,state,sn,price,description,catalog_id,remark,part,purchase_date,location,create_user,create_date)
                VALUE (:id,'仓库',:state,:sn,:price,:description,:catalog_id,:remark,:part,:purchase_date,'仓库',:engname,now())
                '''
        elif para['type'] == 'history':
            if para['location'] == u'仓库' and para['exit'] == '1':
                return 'inactive'
            sql = u'call history_p(:id, :username, :location, :exit, :register_date,:engname);'
        db.session.execute(sql, para)
        db.session.commit()
        return 'ok'

    @app.route('/storage.delete', methods=['POST'])
    @login_required
    def delete():
        if g.user.role_id == 3:
            return 'Powerless'
        para = request.form.get('id')
        flag = Storage.query.filter(u"id=:id and location='仓库'").params(id=para).first()
        if not flag:
            return 'fail'
        db.session.execute(u"delete from stdb.st_history where part_id='%s'" % para)
        db.session.execute(u"delete from stdb.storage where id='%s' and location='仓库'" % para)
        db.session.commit()
        return 'ok'

    # 历史查询
    @app.route('/history', methods=['GET', 'POST'])
    @login_required
    def history():
        para = {'page_index': request.args.get('page', 1, type=int),
                'catalog_id': request.args.get('catalog_id', ''),
                'query': request.args.get('query', ''),
                'part': request.args.get('part', ''),
                'id': request.args.get('id', ''),
                'username': request.args.get('username', ''),
                'location': request.args.get('location', ''),
                'state': request.args.get('state', ''),
                'ifedit': 'N' if g.user.password_hash == '123456' else 'Y'}

        historys = db.session.query(History, Storage.part, Catalog.catalog) \
            .outerjoin(Storage, Storage.id == History.part_id) \
            .outerjoin(Catalog, Catalog.id == Storage.catalog_id).filter('''
                (storage.catalog_id=:catalog_id or :catalog_id ='')
                and (storage.part like concat('%',:part,'%') or :part ='')
                and (st_history.location like concat('%',:location,'%') or :location ='')
                and (st_history.username like concat('%',:username,'%') or :username ='')
                and (st_history.part_id like concat('%',:id,'%') or :id ='')
                and (st_history.state=:state or :state ='')
            ''').params(catalog_id=para['catalog_id'],
                        query=para['query'],
                        part=para['part'],
                        location=para['location'],
                        username=para['username'],
                        id=para['id'],
                        state=para['state']).order_by(History.id.desc())
        pagination = historys.paginate(para['page_index'], per_page=15, error_out=False)
        historys = pagination.items

        g.para.update({'page': 'history'})
        return render_template('history.html',
                               login_form=LoginForm(),
                               para=g.para,
                               catalog=g.catalog,
                               page=eip_format(para),
                               historys=historys if para['query'] else [],
                               pagination=pagination if para['query'] else [])

    # 人员维护
    @app.route('/hr', methods=['GET', 'POST'])
    @login_required
    def hr():
        para = {'page_index': request.args.get('page', 1, type=int),
                'role_id': request.args.get('role_id', ''),
                'query': request.args.get('query', ''),
                'username': request.args.get('username', ''),
                'ifedit': 'N' if g.user.password_hash == '123456' else 'Y'}
        if g.user.role_id != 1:
            return 'Powerless'
        users = db.session.query(User, Role.name).outerjoin(Role, User.role_id == Role.id).filter('''
                (users.role_id=:role_id or :role_id ='')
                and (users.username like concat('%',:username,'%') or :username ='')
            ''').params(role_id=para['role_id'],
                        query=para['query'],
                        username=para['username']).order_by(User.username)

        power = db.session.execute('SELECT rl.id, rl.name FROM stdb.roles rl')

        g.para.update({'page': 'hr'})
        return render_template('hr.html',
                               login_form=LoginForm(),
                               para=g.para,
                               power=power,
                               page=eip_format(para),
                               users=users if para['query'] else [])

    # 详情
    @app.route('/hr.detail', methods=['POST'])
    @login_required
    def hr_detail():
        if g.user.role_id != 1:
            return 'Powerless'
        para = {'id': request.form.get('id')}
        part = db.session.execute(u'''
          select u.id,u.username,u.role_id
          from stdb.users u
          where u.id=:id
       ''', {'id': para['id']})
        part = [dict(r) for r in part]
        return jsonify(part)

    # 保存
    @app.route('/hr.save', methods=['POST'])
    @login_required
    def hr_save():
        para = {'role_id': request.form.get('role_id', ''),
                'username': request.form.get('username', ''),
                'id': request.form.get('id', ''),
                'stype': request.form.get('type', ''),
                'chpwd': request.form.get('chpwd', '')}
        # 维护操作需要root权限
        if g.user.role_id != 1 and para['stype'] == 'update':
            return 'Powerless'
        if not para['role_id']:
            return u'不可分配空角色'
        if para['stype'] == 'update':
            sql = '''
                UPDATE stdb.users u
                    SET u.role_id=:role_id
                    WHERE u.id=:id
            '''
        elif para['stype'] == 'new':
            check = User.query.filter_by(username=para['username']).all()
            if len(check):
                return 'exist'
            sql = '''
                    INSERT INTO stdb.users (username,password_hash,role_id)
                    VALUE(:username,'123456',:role_id)
                '''
        else:
            sql = '''
            UPDATE stdb.users u
                SET u.password_hash= CASE :stype WHEN 'reset' THEN '123456'
                                                 ELSE :chpwd END
                WHERE u.id=:id
        '''
        db.session.execute(sql, para)
        db.session.commit()
        return 'ok' if para['stype'] in ['update', 'new'] else u'重置密码成功！'

    # 分类维护
    @app.route('/catalog', methods=['GET', 'POST'])
    @login_required
    def catalog():
        para = {'query': request.args.get('query', ''),
                'ifedit': 'N' if g.user.password_hash == '123456' else 'Y'}
        if g.user.role_id == 3:
            return 'Powerless'
        catalogs = Catalog.query
        g.para.update({'page': 'catalog'})
        return render_template('catalog.html',
                               login_form=LoginForm(),
                               para=g.para,
                               catalogs=catalogs if para['query'] else [],
                               page=eip_format(para))

    # 分类详情
    @app.route('/catalog.detail', methods=['POST'])
    @login_required
    def catalog_detail():
        if g.user.role_id == 3:
            return 'Powerless'
        para = {'id': request.form.get('id')}
        part = db.session.execute(u'''
                  select *
                  from stdb.catalog c
                  where c.id=:id
               ''', {'id': para['id']})
        part = [dict(r) for r in part]
        return jsonify(part)

    # 保存
    @app.route('/catalog.save', methods=['POST'])
    @login_required
    def catalog_save():
        para = {'id': request.form.get('id', ''),
                'catalog': request.form.get('catalog', ''),
                'stype': request.form.get('type', '')}
        # 维护操作需要权限
        if g.user.role_id == 3:
            return 'Powerless'
        if not para['catalog']:
            return u'不可更新为空'
        if para['stype'] == 'update':
            sql = '''
                    UPDATE stdb.catalog c
                        SET c.catalog=:catalog
                        WHERE c.id=:id
                '''
        else:
            sql = '''
                    INSERT INTO stdb.catalog (catalog)
                        VALUE (:catalog)
                '''
        db.session.execute(sql, para)
        db.session.commit()
        return 'ok'
