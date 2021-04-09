import sqlite3

from flask import render_template_string, Blueprint, render_template
from flask_user import login_required, roles_required
import sqlite3 as sql

blueprint = Blueprint('blueprint', __name__)


# The Home page is accessible to anyone
@blueprint.route('/')
def home_page():
    return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>{%trans%}Home page{%endtrans%}</h2>
                <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                <p><a href={{ url_for('blueprint.home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                <p><a href={{ url_for('blueprint.member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                <p><a href={{ url_for('blueprint.admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
            {% endblock %}
            """)


# The Members page is only accessible to authenticated users
@blueprint.route('/members')
@login_required  # Use of @login_required decorator
def member_page():
    return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>{%trans%}Members page{%endtrans%}</h2>
                <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                <p><a href={{ url_for('blueprint.home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                <p><a href={{ url_for('blueprint.member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                <p><a href={{ url_for('blueprint.admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
            {% endblock %}
            """)


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin')
@roles_required('Admin')  # Use of @roles_required decorator
def admin_page():
    return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
                <h2>{%trans%}Admin Page{%endtrans%}</h2>
                <p><a href={{ url_for('user.register') }}>{%trans%}Register{%endtrans%}</a></p>
                <p><a href={{ url_for('user.login') }}>{%trans%}Sign in{%endtrans%}</a></p>
                <p><a href={{ url_for('blueprint.home_page') }}>{%trans%}Home Page{%endtrans%}</a> (accessible to anyone)</p>
                <p><a href={{ url_for('blueprint.member_page') }}>{%trans%}Member Page{%endtrans%}</a> (login_required: member@example.com / Password1)</p>
                <p><a href={{ url_for('blueprint.admin_page') }}>{%trans%}Admin Page{%endtrans%}</a> (role_required: admin@example.com / Password1')</p>
                <p><a href={{ url_for('user.logout') }}>{%trans%}Sign out{%endtrans%}</a></p>
            {% endblock %}
            """)


# The Admin page requires an 'Admin' role.
@blueprint.route('/admin/view')
@roles_required('Admin')  # Use of @roles_required decorator
def admin_view_page():
    con = sql.connect('appdir/zlagoda.db')
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute("select * from cheque")

    rows = cur.fetchall()
    return render_template("list.html", rows=rows)
