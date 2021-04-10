import datetime
import sqlite3 as sql

from flask import Blueprint, render_template, request, redirect, url_for
from flask_user import login_required, roles_required

from models import User, datetime, user_manager, db, Role

blueprint = Blueprint('blueprint', __name__)


# The Home page is accessible to anyone
@blueprint.route('/')
def home_page():
    return render_template('home.html')


@roles_required('Manager')  # Use of @roles_required decorator
@blueprint.route('/register')
def register_page():
    form = user_manager.RegisterFormClass()
    return render_template('register.html', form=form)


@blueprint.route('/sign-in')
def login_page():
    form = user_manager.LoginFormClass()
    return render_template('login.html', form=form)


# The Members page is only  k accessible to authenticated users
@blueprint.route('/members')
@login_required  # Use of @login_required decorator
def member_page():
    return render_template('member.html')


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin')
@roles_required('Manager')  # Use of @roles_required decorator
def admin_page():
    return render_template('admin.html')


@blueprint.route('/data', methods=['POST'])
def data():
    if request.method == 'POST':
        print(request.form['data'])
        print(request.form['data'] == '"Manager"')
        last_role = "Manager" if request.form['data'] == '"Manager"' else "Cashier"
        file = open('role.txt', 'w')
        file.write(last_role)
        file.close()
        return render_template("home.html")

    else:
        return render_template("home.html")


@blueprint.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        reg_username = request.form['email']
        reg_password = request.form['password']
        reg_role = request.form['role']

        user = User(
            email=reg_username,
            email_confirmed_at=datetime.utcnow(),
            password=user_manager.hash_password(reg_password),
        )
        role_name = "Manager" if reg_role == 'manager' else "Cashier"
        role = Role.query.filter_by(name=role_name).one()
        user.roles.append(role)
        user_manager.db.session.commit()
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('blueprint.home_page'))


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin/view')
@roles_required('Manager')  # Use of @roles_required decorator
def admin_view():
    con = sql.connect('dbs/zlagoda.db')
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select * from cheque")

    rows = cur.fetchall()
    return render_template("list.html", rows=rows)
