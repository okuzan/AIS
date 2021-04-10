from flask import render_template_string, Blueprint, render_template
from flask_user import login_required, roles_required
import sqlite3 as sql

blueprint = Blueprint('blueprint', __name__)


# The Home page is accessible to anyone
@blueprint.route('/')
def home_page():
    return render_template('home.html')


# The Members page is only accessible to authenticated users
@blueprint.route('/members')
@login_required  # Use of @login_required decorator
def member_page():
    return render_template('member.html')


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin')
@roles_required('Admin')  # Use of @roles_required decorator
def admin_page():
    return render_template('admin.html')


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin/view')
@roles_required('Admin')  # Use of @roles_required decorator
def admin_view():
    con = sql.connect('dbs/zlagoda.db')
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select * from cheque")

    rows = cur.fetchall()
    return render_template("list.html", rows=rows)
