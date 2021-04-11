from flask import Flask, render_template_string, Blueprint, render_template, request, redirect, url_for, flash
from flask_user import login_required, roles_required
from flask_script import Manager, Command, Shell
from forms import CategoryForm, ProducerForm, EmployeeForm
import random
from dateutil.relativedelta import relativedelta

import datetime
import sqlite3 as sql

from flask import Blueprint, render_template, request, redirect, url_for
from flask_user import login_required, roles_required

from models import User, datetime, user_manager, db, Role

blueprint = Blueprint('blueprint', __name__)

from models import User, datetime, user_manager


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
    try:
      con = sql.connect('dbs/zlagoda.db')
      con.row_factory = sql.Row
      cur = con.cursor()
      cur.execute("select * from cheque")
      names = [description[0] for description in cur.description]
      rows = cur.fetchall()
      cur.close()
    except sql.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
       if (con):
        con.close()
    return render_template("list.html", rows=rows, tablename="Check info", titles=names)


@blueprint.route('/category/', methods=['get', 'post'])
@roles_required('Admin')  # Use of @roles_required decorator
def category():
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT MAX(CATEGORY_NUMBER) FROM CATEGORY")
            result = cur.fetchone()
            max_id = int(result[0]) + 1
            cur.execute('''INSERT INTO CATEGORY
                                   VALUES (?, ?);''', (max_id, name))
            con.commit()
            cur.close()
            flash('Category was successfully added', 'success')
            return redirect(url_for('blueprint.category'))
        except sql.Error as error:
            flash('Name of category must be unique', 'danger')
            return render_template('form.html', form=form, title='Add category')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add category')


@blueprint.route('/admin_allData/', methods=['get', 'post'])
@roles_required('Admin')
def admin_allData():
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()

        # Data for Producer
        cur.execute("select * from cheque")
        namesProducer = [description[0] for description in cur.description]
        rowsProducer = cur.fetchall()

        # Data for Return_Contract
        cur.execute("select * from return_contract")
        namesReturn_Contract = [description[0] for description in cur.description]
        rowsReturn_Contract = cur.fetchall()

        # Data for Employee
        cur.execute("select * from employee")
        namesEmployee = [description[0] for description in cur.description]
        rowsEmployee = cur.fetchall()

        # Data for Consignment
        cur.execute("select * from consignment")
        namesConsignment = [description[0] for description in cur.description]
        rowsConsignment = cur.fetchall()

        # Data for Sale
        cur.execute("select * from sale")
        namesSale = [description[0] for description in cur.description]
        rowsSale = cur.fetchall()

        # Data for Cheque
        cur.execute("select * from cheque")
        namesCheque = [description[0] for description in cur.description]
        rowsCheque = cur.fetchall()

        # Data for Product
        cur.execute("select * from product")
        namesProduct = [description[0] for description in cur.description]
        rowsProduct = cur.fetchall()

        # Data for Category
        cur.execute("select * from category")
        namesCategory = [description[0] for description in cur.description]
        rowsCategory = cur.fetchall()

        # Data for Store_Product
        cur.execute("select * from store_product")
        namesStore_Product = [description[0] for description in cur.description]
        rowsStore_Product = cur.fetchall()

        # Data for Customer_Card
        cur.execute("select * from customer_card")
        namesCustomer_Card = [description[0] for description in cur.description]
        rowsCustomer_Card = cur.fetchall()

        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template('admin_allData.html', title='All Data',
                           tablenameProducer='Producer', namesProducer=namesProducer, rowsProducer=rowsProducer,
                           tablenameReturn_Contract='Return Contract', namesReturn_Contract=namesReturn_Contract, rowsReturn_Contract=rowsReturn_Contract,
                           tablenameEmployee='Employee', namesEmployee=namesEmployee, rowsEmployee=rowsEmployee,
                           tablenameConsignment='Consignment', namesConsignment=namesConsignment, rowsConsignment=rowsConsignment,
                           tablenameSale='Sale', namesSale=namesSale, rowsSale=rowsSale,
                           tablenameCheque='Cheque', namesCheque=namesCheque, rowsCheque=rowsCheque,
                           tablenameProduct='Product', namesProduct=namesProduct, rowsProduct=rowsProduct,
                           tablenameCategory='Category', namesCategory=namesCategory, rowsCategory=rowsCategory,
                           tablenameStore_Product='Store Product', namesStore_Product=namesStore_Product, rowsStore_Product=rowsStore_Product,
                           tablenameCustomer_Card='Customer Card', namesCustomer_Card=namesCustomer_Card, rowsCustomer_Card=rowsCustomer_Card)


@blueprint.route('/producer/', methods=['get', 'post'])
@roles_required('Admin')  # Use of @roles_required decorator
def producer():
    form = ProducerForm()
    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT MAX(ID_PRODUCER) FROM PRODUCER")
            result = cur.fetchone()
            max_id = int(result[0])+1
            cur.execute('''INSERT INTO PRODUCER(ID_PRODUCER, CONTRACT_NUMBER, RPOD_NAME,COUNTRY, CITY, STREET, ZIP_CODE, PHONE_NUMBER)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?);''', (max_id, form.contract_number.data, form.name.data, form.country.data, form.city.data, form.street.data, form.zip_code.data, form.phone_number.data))
            con.commit()
            cur.close()
            flash('Producer was successfully added', 'success')
            return redirect(url_for('blueprint.producer'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add producer')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add producer')


@blueprint.route('/employee/', methods=['get', 'post'])
@roles_required('Admin')  # Use of @roles_required decorator
def employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            birth = form.date_of_birth.data
            start = form.date_of_start.data
            if(birth>(start - relativedelta(years=18))):
                flash('Age can`t be less than 18', 'danger')
                return render_template('form.html', form=form, title='Add employee')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT ID_EMPLOYEE FROM EMPLOYEE")
            result = cur.fetchall()
            num = random.randint(1,10000)
            while(result.__contains__('e'+str(num))):
                num=random.randint(1,10000)
            eid = 'e'+str(num)
            cur.execute('''INSERT INTO EMPLOYEE(ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC, ROLE, SALARY, DATE_OF_BIRTH, DATE_OF_START, PHONE_NUMBER, CITY, STREET, ZIP_CODE, PASSWORD)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', (eid, form.surname.data, form.name.data, form.patronymic.data, form.role.data, form.salary.data, form.date_of_birth.data, form.date_of_start.data, form.phone_number.data,  form.city.data, form.street.data, form.zip_code.data, user_manager.hash_password(form.password.data)))
            con.commit()
            cur.close()
            flash('Employee was successfully added', 'success')
            return redirect(url_for('blueprint.employee'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Employee')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Employee')
