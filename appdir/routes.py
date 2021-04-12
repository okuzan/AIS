import datetime
import random
import sqlite3 as sql

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash
from flask import session
from flask_user import login_required, roles_required

from forms import CategoryForm, ProducerForm
from forms import CheckForm
from forms import EmployeeForm, ProductForm, CustomerForm, StoreProductForm, \
    ReturnContractForm, ConsignmentForm
from models import db, Role

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
@roles_required('Manager')  # Use of @roles_required decorator
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
            session.pop('_flashes', None)
            flash('Category was successfully added', 'success')
            return redirect(url_for('blueprint.category'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash('Name of category must be unique', 'danger')
            return render_template('form.html', form=form, title='Add category')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add category')


# @blueprint.route('/delete')
# def foo():
#     pin = requests.args.get('id')
#     print(pin)

@roles_required('Manager')
@blueprint.route('/<table>/<key>/<int:rowid>/delete', methods=['POST'])
def delete(table, key, rowid):
    print("DELETING")
    print(rowid)
    table1 = table if ' ' not in table else table.replace(' ', '_')
    print(table1)
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("DELETE FROM " + table1 +
                " WHERE " + key + " = "
                + "(" + "SELECT " + key + " FROM "
                + table1 + " LIMIT 1 OFFSET " + (
                    str(rowid)) + ")"),
    con.commit()
    cur.close()
    return redirect('/admin_allData')


@blueprint.route('/delete', methods=['get'])
@roles_required('Manager')
def delete_page():
    con = sql.connect('dbs/zlagoda.db')
    con.row_factory = sql.Row
    cur = con.cursor()

    # Data for Producer
    cur.execute("select * from producer")
    namesProducer = [description[0] for description in cur.description]
    rowsProducer = cur.fetchall()

    return redirect('/admin_allData')


@roles_required('Manager')
@blueprint.route('/<int:rowid>/update', methods=['GET', 'POST'])
def update_employee(rowid):
    print(request.form)
    print(rowid)
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM EMPLOYEE LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    cur.execute("SELECT rowid FROM EMPLOYEE LIMIT 1 OFFSET " + (str(rowid - 1))),
    row2 = cur.fetchall()[0]
    print(row2)
    print("rowid!!")
    print(row)
    form = EmployeeForm(hide_a=True)
    form.surname.data = row[1]
    form.name.data = row[2]
    form.patronymic.data = row[3]
    form.role = row[4]  # careful : select fields don't need 'data'
    form.salary.data = str(row[5])
    form.date_of_birth.data = datetime.strptime(str(row[6]), '%Y-%m-%d')
    form.date_of_start.data = datetime.strptime(str(row[7]), '%Y-%m-%d')
    form.phone_number.data = str(row[8])
    form.city.data = row[9]
    form.street.data = row[10]
    form.zip_code.data = str(row[11])
    form.password.data = '.'  # just to pass validation, that won't be assigned
    if form.is_submitted():
        try:
            birth = request.form['date_of_birth']
            start = request.form['date_of_start']
            if datetime.strptime(birth, '%Y-%m-%d').date() > (
                    datetime.strptime(start, '%Y-%m-%d').date() - relativedelta(years=18)):
                session.pop('_flashes', None)
                flash('Age can`t be less than 18', 'danger')
                return render_template('form.html', form=form, title='Update employee')

            values = (request.form['surname'], request.form['name'], request.form['patronymic'], request.form['role'],
                      request.form['salary'], birth, start,
                      request.form['phone_number'], request.form['city'], request.form['street'],
                      request.form['zip_code'], (str(rowid - 1)))
            print(request)
            cur.execute("""UPDATE EMPLOYEE
                        SET EMPL_SURNAME = ?, EMPL_NAME = ?, EMPL_PATRONYMIC = ?, ROLE = ?,
                        SALARY = ?,DATE_OF_BIRTH = ?, DATE_OF_START = ?,
                        PHONE_NUMBER = ?, CITY = ?, STREET = ?, ZIP_CODE = ?
                        WHERE ID_EMPLOYEE = (SELECT ID_EMPLOYEE FROM EMPLOYEE LIMIT 1 OFFSET ?)""", values)

            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Employee was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Employee')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Employee')


@blueprint.route('/admin_allData', methods=['get'])
@roles_required('Manager')
def admin_data():
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()

        # Data for Producer
        cur.execute("select * from producer")
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
                           tablenameReturn_Contract='Return Contract', namesReturn_Contract=namesReturn_Contract,
                           rowsReturn_Contract=rowsReturn_Contract,
                           tablenameEmployee='Employee', namesEmployee=namesEmployee, rowsEmployee=rowsEmployee,
                           tablenameConsignment='Consignment', namesConsignment=namesConsignment,
                           rowsConsignment=rowsConsignment,
                           tablenameSale='Sale', namesSale=namesSale, rowsSale=rowsSale,
                           tablenameCheque='Cheque', namesCheque=namesCheque, rowsCheque=rowsCheque,
                           tablenameProduct='Product', namesProduct=namesProduct, rowsProduct=rowsProduct,
                           tablenameCategory='Category', namesCategory=namesCategory, rowsCategory=rowsCategory,
                           tablenameStore_Product='Store Product', namesStore_Product=namesStore_Product,
                           rowsStore_Product=rowsStore_Product,
                           tablenameCustomer_Card='Customer Card', namesCustomer_Card=namesCustomer_Card,
                           rowsCustomer_Card=rowsCustomer_Card)


@blueprint.route('/producer/', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def producer():
    form = ProducerForm()
    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT MAX(ID_PRODUCER) FROM PRODUCER")
            result = cur.fetchone()
            max_id = int(result[0]) + 1
            cur.execute('''INSERT INTO PRODUCER(ID_PRODUCER, CONTRACT_NUMBER, RPOD_NAME,COUNTRY, CITY, STREET, ZIP_CODE, PHONE_NUMBER)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?);''', (
                max_id, form.contract_number.data, form.name.data, form.country.data, form.city.data, form.street.data,
                form.zip_code.data, form.phone_number.data))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Producer was successfully added', 'success')
            return redirect(url_for('blueprint.producer'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add producer')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add producer')


@blueprint.route('/employee', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def employee():
    form = EmployeeForm(hide_a=False)
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    if form.validate_on_submit():
        try:
            birth = form.date_of_birth.data
            start = form.date_of_start.data
            if birth > (start - relativedelta(years=18)):
                session.pop('_flashes', None)
                flash('Age can`t be less than 18', 'danger')
                return render_template('form.html', form=form, title='Add employee')
            cur.execute("SELECT ID_EMPLOYEE FROM EMPLOYEE")
            result = cur.fetchall()
            num = random.randint(1, 10000)
            temp = []
            for row in result:
                temp.append(row[0])
            while temp.__contains__('e' + str(num)):
                num = random.randint(1, 10000)
            eid = 'e' + str(num)
            cur.execute('''INSERT INTO EMPLOYEE(ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC, ROLE, SALARY, DATE_OF_BIRTH, DATE_OF_START, PHONE_NUMBER, CITY, STREET, ZIP_CODE)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''', (
                eid, form.surname.data, form.name.data, form.patronymic.data, form.role.data, form.salary.data,
                form.date_of_birth.data, form.date_of_start.data, form.phone_number.data, form.city.data,
                form.street.data,
                form.zip_code.data))
            con.commit()
            cur.close()
            user = User(
                email=eid + "." + form.name.data + "." + form.surname.data + ".@db.com",
                email_confirmed_at=datetime.utcnow(),
                password=user_manager.hash_password(form.password.data),
            )
            role_name = "Manager" if form.role.data == 'M' else "Cashier"
            role = Role.query.filter_by(name=role_name).one()
            user.roles.append(role)
            user_manager.db.session.commit()
            db.session.add(user)
            db.session.commit()
            session.pop('_flashes', None)
            flash('Employee was successfully added', 'success')
            return redirect(url_for('blueprint.employee'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Employee')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Employee')


@blueprint.route('/<int:rowid>/update-producer', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_producer(rowid):
    con = sql.connect('dbs/zlagoda.db')
    # con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM PRODUCER LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    print(row)
    form = ProducerForm()
    form.contract_number.data = row[1]
    form.name.data = row[2]
    form.country.data = row[3]
    form.city.data = row[4]
    form.street.data = row[5]
    form.zip_code.data = row[6]
    form.phone_number.data = row[7]

    if form.is_submitted():
        try:
            cur.execute('''UPDATE PRODUCER
             SET CONTRACT_NUMBER = ?, RPOD_NAME = ?,
             COUNTRY = ?,  CITY = ?, STREET = ?, 
             ZIP_CODE = ?, PHONE_NUMBER = ?
             WHERE ID_PRODUCER = (SELECT ID_PRODUCER FROM PRODUCER LIMIT 1 OFFSET ?)''', (
                request.form['contract_number'], request.form['name'],
                request.form['country'], request.form['city'],
                request.form['street'], request.form['zip_code'],
                request.form['phone_number'], str(rowid - 1)))

            con.commit()
            cur.close()
            flash('Producer was successfully updated', 'success')
            return redirect(url_for('blueprint.admin_data'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update producer')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update producer')


@blueprint.route('/product', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def product():
    form = ProductForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT CATEGORY_NUMBER, CATEGORY_NAME FROM CATEGORY")
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.category_number.choices = groups_list
    if form.validate_on_submit():
        try:
            s = value = dict(form.category_number.choices).get(form.category_number.data)
            print(value + " @")  # here is the answer you need to parse further
            chosen_fk = s[s.find("(") + 1:s.find(")")]
            print(chosen_fk)  # here is ID (something between '(' ')' )
            cur.execute("SELECT MAX(ID_PRODUCT) FROM PRODUCT")
            result = cur.fetchone()
            max_id = int(result[0]) + 1
            cur.execute('''INSERT INTO PRODUCT(ID_PRODUCT, CATEGORY_NUMBER, PRODUCT_NAME, CHARACTERISTICS)
                                   VALUES (?, ?, ?, ?);''', (
                max_id, chosen_fk, form.product_name.data, form.characteristics.data))
            con.commit()
            session.pop('_flashes', None)
            flash('Product was successfully added', 'success')
            return redirect(url_for('blueprint.product'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Product')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Product')


@blueprint.route('/customer/', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def customer():
    form = CustomerForm()
    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT CARD_NUMBER FROM CUSTOMER_CARD")
            result = cur.fetchall()
            num = random.randint(1, 10000)
            temp = []
            for row in result:
                temp.append(row[0])
            while temp.__contains__('c' + str(num)):
                num = random.randint(1, 10000)
            eid = 'c' + str(num)
            cur.execute('''INSERT INTO CUSTOMER_CARD(CARD_NUMBER, CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC, PHONE_NUMBER, CITY, STREET, ZIP_CODE, PERCENT)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);''', (
                eid, form.surname.data, form.name.data, form.patronymic.data, form.phone_number.data, form.city.data,
                form.street.data, form.zip_code.data, form.percent.data))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Customer Card was successfully added', 'success')
            return redirect(url_for('blueprint.customer'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Customer Card')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Customer Card')


@blueprint.route('/<int:rowid>/update-contract', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_contract(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM RETURN_CONTRACT LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    print(rowid)
    print(row)
    form = ReturnContractForm()
    # form.upc = row[1]
    # form.producer = row[2]
    # form.employee = row[3]
    form.quantity.data = str(row[5])
    form.signature_date.data = datetime.strptime(str(row[4]), '%Y-%m-%d')

    cur.execute('''SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.producer.choices = groups_list

    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="manager"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list

    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc.choices = groups_list

    if form.validate_on_submit():
        try:
            cur.execute('''UPDATE RETURN_CONTRACT
             SET ID_PRODUCER = ?, ID_EMPLOYEE = ?, UPC = ?, SIGNATURE_DATE = ?, PRODUCT_NUMBER = ?, SUM_TOTAL = ?
             WHERE CONTRACT_NUMBER = (SELECT CONTRACT_NUMBER FROM RETURN_CONTRACT LIMIT 1 OFFSET ?)''', (
                request.form['producer'],
                request.form['employee'],
                request.form['upc'],
                request.form['signature_date'],
                request.form['quantity'],
                request.form['sum'],
                str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Return contract was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Return Contract')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Return Contract')


@blueprint.route('/<int:rowid>/update-consignment', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_consignment(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM CONSIGNMENT LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    print(rowid)
    print(row)
    form = ConsignmentForm()
    # form.upc = row[1]
    # form.producer = row[2]
    # form.employee = row[3]
    form.signature_date.data = datetime.strptime(str(row[4]), '%Y-%m-%d')
    form.quantity.data = str(row[5])
    form.price.data = str(row[6])

    cur.execute('''SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.producer.choices = groups_list

    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="manager"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list

    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc.choices = groups_list

    if form.validate_on_submit():
        try:
            cur.execute('''UPDATE CONSIGNMENT
             SET ID_PRODUCER = ?, ID_EMPLOYEE = ?, UPC = ?, SIGNATURE_DATE = ?, PRODUCTS_NUMBER = ?, PURCHASE_PRICE = ?
             WHERE CONS_NUMBER = (SELECT CONS_NUMBER FROM CONSIGNMENT LIMIT 1 OFFSET ?)''', (
                request.form['producer'],
                request.form['employee'],
                request.form['upc'],
                request.form['signature_date'],
                request.form['quantity'],
                request.form['price'],
                str(rowid - 1)))
            new_price = round(1.56 * float(form.price.data), 2)
            cur.execute('''UPDATE STORE_PRODUCT
                                       SET SELLING_PRICE = ?
                                       WHERE UPC=?''', (new_price, form.upc.data))
            con.commit()
            cur.close()
            flash('Consignment was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Consignment')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Consignment')


@blueprint.route('/<int:rowid>/update-category', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_category(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM CATEGORY LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    form = CategoryForm()
    form.name.data = row[1]
    if form.validate_on_submit():
        try:
            cur.execute('''UPDATE CATEGORY
             SET CATEGORY_NAME = ?
             WHERE CATEGORY_NUMBER = (SELECT CATEGORY_NUMBER FROM CATEGORY LIMIT 1 OFFSET ?)''', (
                request.form['name'], str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Customer Card was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Category')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Category')


@blueprint.route('/<int:rowid>/update-cheque', methods=['get', 'post'])
@roles_required('Cashier')  # Use of @roles_required decorator
def update_cheque(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM CATEGORY LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    form = CheckForm()
    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="manager"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list
    cur.execute('''SELECT CARD_NUMBER, CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC
                          FROM CUSTOMER_CARD''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.card.choices = [("", "---")] + groups_list
    form.signature_date.data = row[3]  # todo
    form.sum.data = str(row[4])
    form.vat.data = str(row[5])
    form.name.data = row[1]
    if form.validate_on_submit():
        try:
            cur.execute('''UPDATE CHEQUE
             SET ID_EMPLOYEE = ?, CARD_NUMBER = ?, 
             PRINT_DATE = ?, SUM_TOTAL = ?, VAT = ?
             WHERE CHECK_NUMBER = (SELECT CHECK_NUMBER FROM CHEQUE LIMIT 1 OFFSET ?)''', (
                request.form['employee'],
                request.form['card'],
                request.form['data'],
                request.form['sum'],
                request.form['vat'],
                str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Customer Card was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Category')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Category')


@blueprint.route('/<int:rowid>/update-product', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_product(rowid):
    form = ProductForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM PRODUCT LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    cur.execute("SELECT CATEGORY_NUMBER, CATEGORY_NAME FROM CATEGORY")
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.category_number.choices = groups_list
    # form.category_number = row[1]
    form.product_name.data = row[2]
    form.characteristics.data = row[2]

    if form.validate_on_submit():
        try:
            cur.execute('''UPDATE PRODUCT
             SET CATEGORY_NUMBER = ?, PRODUCT_NAME = ?, CHARACTERISTICS = ?
             WHERE ID_PRODUCT = (SELECT ID_PRODUCT FROM PRODUCT LIMIT 1 OFFSET ?)''', (
                request.form['category_number'],
                request.form['product_name'],
                request.form['characteristics'],
                str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Product was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Product')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Product')


@blueprint.route('/<int:rowid>/update-store-product', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_store_product(rowid):
    form = StoreProductForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM STORE_PRODUCT LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    cur.execute('''SELECT ID_PRODUCT, PRODUCT_NAME FROM PRODUCT
    WHERE 2>(SELECT COUNT(ID_PRODUCT)
            FROM STORE_PRODUCT
            WHERE PRODUCT.ID_PRODUCT=ID_PRODUCT
    )
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.product_number.choices = groups_list
    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT S
                   WHERE PROMOTIONAL_PRODUCT=1 AND UPC NOT IN (
                   SELECT UPC_PROM
                   FROM STORE_PRODUCT
                   WHERE UPC_PROM IS NOT NULL
                   )      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + i[0] + ") ") for i in result]
    form.upc_prom.choices = [('-1','---')]+groups_list

    # form.category_number = row[1]
    form.upc_code.data = row[0]
    form.price.data = str(row[3])
    form.quantity.data = str(row[4])
    form.promotional.data = str(row[5])

    if form.is_submitted():
        try:
            if form.upc_prom.data.__len__() < 12:
                cur.execute('''UPDATE STORE_PRODUCT
                                            SET UPC = ?, UPC_PROM = NULL, ID_PRODUCT = ?, SELLING_PRICE = ?,
                                             PRODUCTS_NUMBER = ?, PROMOTIONAL_PRODUCT = ? 
                                            WHERE UPC = (SELECT UPC FROM STORE_PRODUCT LIMIT 1 OFFSET ?)''', (
                    request.form['upc_code'],
                    request.form['product_number'],
                    request.form['price'],
                    request.form['quantity'],
                    request.form['promotional'],
                    str(rowid - 1)))
            else:
                cur.execute('''UPDATE STORE_PRODUCT
                             SET UPC = ?, UPC_PROM = ?, ID_PRODUCT = ?, SELLING_PRICE = ?,
                              PRODUCTS_NUMBER = ?, PROMOTIONAL_PRODUCT = ? 
                             WHERE UPC = (SELECT UPC FROM STORE_PRODUCT LIMIT 1 OFFSET ?)''', (
                    request.form['upc_code'],
                    request.form['upc_prom'],
                    request.form['product_number'],
                    request.form['price'],
                    request.form['quantity'],
                    request.form['promotional'],
                    str(rowid - 1)))


            con.commit()
            cur.close()
            flash('Store-Product was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Store-Product')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Store-Product')


@blueprint.route('/<int:rowid>/update-customer', methods=['get', 'post'])
@roles_required('Cashier')  # Use of @roles_required decorator
def update_customer(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM CUSTOMER_CARD LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    form = CustomerForm()
    form.surname.data = row[1]
    form.name.data = row[2]
    form.patronymic.data = row[3]
    form.phone_number.data = str(row[4])
    form.city.data = row[5]
    form.street.data = row[6]
    form.zip_code.data = str(row[7])
    form.percent.data = str(row[8])
    if form.validate_on_submit():
        try:
            # con.row_factory = sql.Row
            cur.execute('''UPDATE CUSTOMER_CARD
             SET CUST_SURNAME = ?, CUST_NAME = ?,
             CUST_PATRONYMIC = ?, PHONE_NUMBER = ?, CITY = ?, 
             STREET = ?, ZIP_CODE = ?, PERCENT = ?
             WHERE CARD_NUMBER = (SELECT CARD_NUMBER FROM CUSTOMER_CARD LIMIT 1 OFFSET ?)''', (
                request.form['surname'], request.form['name'], request.form['patronymic'],
                request.form['phone_number'], request.form['city'],
                request.form['street'], request.form['zip_code'], request.form['percent'], str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Customer Card was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Update Customer Card')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Update Customer Card')


@blueprint.route('/check', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def check_form():
    form = CheckForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                      FROM EMPLOYEE
                      WHERE ROLE="cashier"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list

    cur.execute('''SELECT CARD_NUMBER, CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC
                          FROM CUSTOMER_CARD''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.card.choices = [("", "---")]+groups_list
    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT CHECK_NUMBER FROM CHEQUE")
            result = cur.fetchall()
            num = random.randint(1, 10000)
            temp = []
            for row in result:
                temp.append(row[0])
            while temp.__contains__('c' + str(num)):
                num = random.randint(1, 10000)
            max_id = 'c'+str(num)
            sale_prices = []
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sum_total = 0
            percent = 0
            if form.card.data.__len__()>0:
                cur.execute('''SELECT PERCENT 
                             FROM CUSTOMER_CARD
                             WHERE CARD_NUMBER=?''', (form.card.data,))
                result = cur.fetchall()
                percent=result[0][0]
            for s in form.sales.data:
                cur.execute('''SELECT SELLING_PRICE
                               FROM STORE_PRODUCT
                               WHERE UPC=?''', (s['upc_code'],))
                result = cur.fetchall()
                if result.__len__()!=1:
                    flash('Incorrect UPC', 'danger')
                    return render_template('checkForm.html', form=form, title='Add check')
                sale_prices=sale_prices+[(result[0][0], s['quantity'], s['upc_code'])]
            for sale in sale_prices:
                sum_total+=int(sale[1])*int(sale[0])
            if percent != 0:
                sum_total=0.01*(100-percent)*sum_total
            sum_total=round(sum_total, 2)
            vat = round(0.2 * sum_total / 1.2,2)
            if form.card.data.__len__()>0:
                cur.execute('''INSERT INTO CHEQUE(CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT)
                                                              VALUES (?, ?, ?, ?, ?, ?);''', (max_id, form.employee.data,
                                                                                              form.card.data, date, sum_total, vat))
            else:
                cur.execute('''INSERT INTO CHEQUE(CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT)
                                                                              VALUES (?, ?, NULL, ?, ?, ?);''',
                            (max_id, form.employee.data,
                             date, sum_total, vat))
            con.commit()
            for sale in sale_prices:
                cur.execute('''INSERT INTO SALE(UPC, CHECK_NUMBER, PRODUCT_NUMBER, SELLING_PRICE)
                                                                                              VALUES (?, ?, ?, ?);''',
                            (sale[2], max_id,
                            sale[1], sale[0]))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Check was successfully added', 'success')
            return redirect(url_for('blueprint.check_form'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('checkForm.html', form=form, title='Add check')
        finally:
            if (con):
                con.close()
    return render_template('checkForm.html', form=form, title='Create check')


@blueprint.route('/cashier_queries/', methods=['get'])
@roles_required('Cashier')
def cashier_queries():
    tablename = 'Cashier Queries'
    _1Query = 'Скласти список чеків,  видрукуваних даним касиром за певний період часу'
    _2Query = 'За номером чеку вивести усю інформацію про даний чек'
    _3Query = 'Вивести усю інформацію про покупця з певним прізвищем, що має карту клієнта'
    _4Query = 'Список усіх постійних клієнтів, що мають карту клієнта з певним відсотком'
    _5Query = 'Скласти список товарів, що належать певній категорії, відсортованих за назвою'
    _6Query = 'Скласти список усіх товарів, відсортований за назвою'
    _7Query = 'Скласти список усіх акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    _8Query = 'Скласти список усіх не акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    _9Query = 'За номером чека скласти список усіх товарів, інформація про продаж яких є у цьому чеку'
    _10Query = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару'
    _11Query = 'За ID_працівника знайти всю інформацію про себе'
    return render_template('cashier_queries.html', tablename=tablename, _1Query=_1Query,
                           _2Query=_2Query,
                           _3Query=_3Query,
                           _4Query=_4Query,
                           _5Query=_5Query,
                           _6Query=_6Query,
                           _7Query=_7Query,
                           _8Query=_8Query,
                           _9Query=_9Query,
                           _10Query=_10Query,
                           _11Query=_11Query)


@blueprint.route('/1QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_1Query():
    cashier_id = request.form['1QueryCName1']
    date_from = request.form['1QueryCName2']
    date_to = request.form['1QueryCName3']
    tablename = 'Скласти список чеків,  видрукуваних даним касиром за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM CHEQUE WHERE PRINT_DATE BETWEEN {} AND {} AND ID_EMPLOYEE={}".format(date_from, date_to,
                                                                                                cashier_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/2QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_2Query():
    check_number = request.form['2QueryCName']
    tablename = 'За номером чеку вивести усю інформацію про даний чек'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, 
                            SALE.UPC,   PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME
                      FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER
                      INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC
                      INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT
                      WHERE CHEQUE.CHECK_NUMBER={}'''.format(check_number))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/3QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_3Query():
    surname = request.form['3QueryCName']
    tablename = 'Вивести усю інформацію про покупця з певним прізвищем, що має карту клієнта'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM CUSTOMER_CARD
                      WHERE CUST_SURNAME=?'''.format(surname))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/4QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_4Query():
    percent = request.form['4QueryCName']
    tablename = 'Список усіх постійних клієнтів, що мають карту клієнта з певним відсотком'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CUSTOMER_CARD WHERE PERCENT={}".format(percent))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/5QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_5Query():
    category_name = request.form['5QueryCName']
    tablename = 'Скласти список товарів, що належать певній категорії, відсортованих за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        toExec = "SELECT * FROM PRODUCT WHERE CATEGORY_NUMBER IN(SELECT CATEGORY_NUMBER FROM CATEGORY WHERE CATEGORY_NAME='" + category_name + "') ORDER BY PRODUCT_NAME "
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/6QueryC', methods=['get'])
@roles_required('Cashier')
def cashier_6Query():
    tablename = 'Скласти список усіх товарів, відсортований за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT PRODUCT.ID_PRODUCT, PRODUCT_NAME, CHARACTERISTICS, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT
                              FROM PRODUCT INNER JOIN STORE_PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT
                              ORDER BY PRODUCT_NAME''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/7QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_7Query():
    order_by = request.form['7QueryCName1']  # quan or name
    sortType = request.form['7QueryCName2']  # ASC or DESC
    tablename = 'Скласти список усіх акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM STORE_PRODUCT WHERE PROMOTIONAL_PRODUCT=1 ORDER BY {} {}".format(order_by, sortType))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/8QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_8Query():
    order_by = request.form['8QueryCName1']  # quan or name
    sortType = request.form['8QueryCName2']  # ASC or DESC
    tablename = 'Скласти список усіх не акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM STORE_PRODUCT WHERE PROMOTIONAL_PRODUCT=0 ORDER BY {} {}".format(order_by, sortType))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/9QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_9Query():
    check_num = request.form['9QueryCName']
    tablename = 'За номером чека скласти список усіх товарів, інформація про продаж яких є у цьому чеку'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT PRODUCT_NAME, CHARACTERISTICS, CATEGORY_NAME, SALE.UPC, PRODUCT_NUMBER, SELLING_PRICE
                      FROM SALE INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC
                      INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT
                      INNER JOIN CATEGORY ON PRODUCT.CATEGORY_NUMBER=CATEGORY.CATEGORY_NUMBER
                      WHERE SALE.CHECK_NUMBER={}'''.format(check_num))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/10QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_10Query():
    upc = request.form['10QueryCName']
    tablename = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару, назву та характеристики товару'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT STORE_PRODUCT.UPC, STORE_PRODUCT.ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PRODUCT_NAME, CHARACTERISTICS FROM STORE_PRODUCT INNER JOIN PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT WHERE UPC={}".format(
                upc))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/11QueryC', methods=['get', 'post'])
@roles_required('Cashier')
def cashier_11Query():
    id = request.form['11QueryCName']
    tablename = 'За ID_працівника знайти всю інформацію про себе'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM EMPLOYEE 
                      WHERE ID_EMPLOYEE={}
                   '''.format(id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/store_product/', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def store_product():
    form = StoreProductForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute('''SELECT ID_PRODUCT, PRODUCT_NAME FROM PRODUCT
    WHERE (SELECT COUNT(ID_PRODUCT)
            FROM STORE_PRODUCT
            WHERE PRODUCT.ID_PRODUCT=ID_PRODUCT
    )
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.product_number.choices =groups_list

    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT S
                   WHERE PROMOTIONAL_PRODUCT=1 AND UPC NOT IN (
                   SELECT UPC_PROM
                   FROM STORE_PRODUCT
                   WHERE UPC_PROM IS NOT NULL
                   )      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc_prom.choices = [('', '---')]+ groups_list

    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            if form.upc_prom.data.__len__() < 12:
                cur.execute('''INSERT INTO STORE_PRODUCT(UPC, ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT)
                                                  VALUES (?, ?, ?, ?, ?);''', (
                    form.upc_code.data, form.product_number.data, form.price.data,
                    form.quantity.data, form.promotional.data))
            else:
                cur.execute('''INSERT INTO STORE_PRODUCT(UPC, UPC_PROM, ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT)
                                   VALUES (?, ?, ?, ?, ?, ?);''', (
                    form.upc_code.data, form.upc_prom.data, form.product_number.data, form.price.data,
                    form.quantity.data,
                    form.promotional.data))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Store product was successfully added', 'success')
            return redirect(url_for('blueprint.store_product'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Store Product')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Store Product')


@blueprint.route('/consignment/', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def consignment():
    form = ConsignmentForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute('''SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.producer.choices = groups_list

    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="manager"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list

    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc.choices = groups_list

    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT CONS_NUMBER FROM CONSIGNMENT")
            result = cur.fetchall()
            num = random.randint(1, 10000)
            temp = []
            for row in result:
                temp.append(row[0])
            while temp.__contains__('c' + str(num)):
                num = random.randint(1, 10000)
            eid = 'c' + str(num)
            cur.execute('''INSERT INTO CONSIGNMENT(CONS_NUMBER, ID_PRODUCER, ID_EMPLOYEE, UPC, SIGNATURE_DATE, PRODUCTS_NUMBER, PURCHASE_PRICE)
                                               VALUES (?, ?, ?, ?, ?, ?, ?);''', (
                eid, form.producer.data, form.employee.data, form.upc.data, form.signature_date.data,
                form.quantity.data,
                form.price.data))
            #закуп. ціна + закуп. ціна * 0,3 + 0,2 * (закуп. ціна + закуп. ціна * 0,3).
            new_price = round(1.56*float(form.price.data),2)
            cur.execute("SELECT PRODUCTS_NUMBER FROM STORE_PRODUCT WHERE UPC=?",(form.upc.data,))
            number = cur.fetchall()[0][0]
            cur.execute('''UPDATE STORE_PRODUCT
                           SET SELLING_PRICE = ?, PRODUCTS_NUMBER = ?
                           WHERE UPC=?''', (new_price, number+form.quantity.data, form.upc.data))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Consignment was successfully added', 'success')
            return redirect(url_for('blueprint.consignment'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Consignment')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Consignment')


@blueprint.route('/return_contract/', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def return_contract():
    form = ReturnContractForm()
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute('''SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1]) for i in result]
    form.producer.choices = groups_list

    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="manager"''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]
    form.employee.choices = groups_list

    cur.execute('''SELECT UPC
                   FROM STORE_PRODUCT      
    ''')
    result = cur.fetchall()
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc.choices = groups_list

    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            cur.execute("SELECT PRODUCTS_NUMBER FROM STORE_PRODUCT WHERE UPC=?", (form.upc.data,))
            number = cur.fetchall()[0][0]- form.quantity.data
            if number < 0:
                flash('Result quantity of product after returning must be more than 0', 'danger')
                return render_template('form.html', form=form, title='Add Return Contract')
            cur.execute('''SELECT PURCHASE_PRICE FROM CONSIGNMENT
            WHERE UPC=? AND SIGNATURE_DATE IN (SELECT MAX(SIGNATURE_DATE)
            FROM CONSIGNMENT WHERE UPC=?
            )''', (form.upc.data, form.upc.data))
            price = cur.fetchall()[0][0]

            cur.execute("SELECT CONTRACT_NUMBER FROM RETURN_CONTRACT")
            result = cur.fetchall()
            num = random.randint(1, 10000)
            temp = []
            for row in result:
                temp.append(row[0])
            while temp.__contains__('c' + str(num)):
                num = random.randint(1, 10000)
            eid = 'c' + str(num)
            cur.execute('''INSERT INTO RETURN_CONTRACT(CONTRACT_NUMBER, ID_PRODUCER, ID_EMPLOYEE, UPC, SIGNATURE_DATE, PRODUCT_NUMBER, SUM_TOTAL)
                                               VALUES (?, ?, ?, ?, ?, ?, ?);''', (
                eid, form.producer.data, form.employee.data, form.upc.data, form.signature_date.data,
                form.quantity.data,
                price*form.quantity.data))
            cur.execute('''UPDATE STORE_PRODUCT
                                                   SET PRODUCTS_NUMBER = ?
                                                   WHERE UPC=?''', (number, form.upc.data))
            con.commit()
            cur.close()
            session.pop('_flashes', None)
            flash('Return contract was successfully added', 'success')
            return redirect(url_for('blueprint.return_contract'))
        except sql.Error as error:
            session.pop('_flashes', None)
            flash(error, 'danger')
            return render_template('form.html', form=form, title='Add Return Contract')
        finally:
            if (con):
                con.close()
    return render_template('form.html', form=form, title='Add Return Contract')


@blueprint.route('/admin_queries/', methods=['get', 'post'])
@roles_required('Manager')
def admin_queries():
    tablename = 'Admin Queries'
    _1Query = 'Скласти список працівників, що займають посаду касира, відсортованих за прізвищем'
    _2Query = 'Скласти список товарів, що належать певній категорії, відсортованих за назвою'
    _3Query = 'За прізвищем працівника знайти його телефон та адресу'
    _4Query = 'Скласти список усіх виробників, що постачають товари до магазину'
    _5Query = 'За назвою виробника вивести його контактний телефон та адресу'
    _6Query = 'Скласти список усіх товарів, відсортованих за назвою'
    _7Query = 'Скласти список усіх категорій, відсортованих за назвою'
    _8Query = 'Скласти список всіх товарів, що належать певній категорії'
    _9Query = 'Скласти список товарів у магазині, що належать певному товару'
    _10Query = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару'
    _11Query = 'Скласти список усіх акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    _12Query = 'Скласти список усіх не акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    _13Query = 'Скласти список усіх накладних на певний товар, підписаних виробником за певний період часу'
    _14Query = 'Скласти список усіх накладних, підписаних певним виробником за певний період часу'
    _15Query = 'Скласти список усіх накладних, підписаних будь-яким виробником за певний період часу'
    _16Query = 'Визначити загальну кількість закуплених одиниць певного товару за певний період часу'
    _17Query = 'Скласти список усіх договорів повернення на певний товар, підписаних виробником за певний період часу'
    _18Query = 'Скласти список усіх договорів повернення, підписаних певним виробникам за певний період часу'
    _19Query = 'Скласти список усіх договорів повернення, підписаних будь-яким виробникам за певний період часу'
    _20Query = 'Визначити загальну кількість повернених одиниць певного товару за певний період часу'
    _21Query = 'Скласти список чеків, видрукуваних певним касиром за певний період часу (з можливістю перегляду куплених товарів, їх к-сті та ціни)'
    _22Query = 'Скласти список чеків, видрукуваних усіма касирами за певний період часу (з можливістю перегляду куплених товарів, їх к-сті та ціни)'
    _23Query = 'Визначити загальну кількість одиниць певного товару, проданого за певний період часу'
    _24Query = 'Скласти список усіх постійних клієнтів, що мають карту клієнта, по полях ПІБ, телефон, адреса (якщо вказана)'
    _25Query = 'Скласти список усіх постійних клієнтів, що мають карту клієнта із певним відсотком'
    _26Query = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару, назву та характеристики товару'
    return render_template('admin_queries.html', tablename=tablename, _1Query=_1Query,
                           _2Query=_2Query,
                           _3Query=_3Query,
                           _4Query=_4Query,
                           _5Query=_5Query,
                           _6Query=_6Query,
                           _7Query=_7Query,
                           _8Query=_8Query,
                           _9Query=_9Query,
                           _10Query=_10Query,
                           _11Query=_11Query,
                           _12Query=_12Query,
                           _13Query=_13Query,
                           _14Query=_14Query,
                           _15Query=_15Query,
                           _16Query=_16Query,
                           _17Query=_17Query,
                           _18Query=_18Query,
                           _19Query=_19Query,
                           _20Query=_20Query,
                           _21Query=_21Query,
                           _22Query=_22Query,
                           _23Query=_23Query,
                           _24Query=_24Query,
                           _25Query=_25Query,
                           _26Query=_26Query)


@blueprint.route('/1Query', methods=['get'])
@roles_required('Manager')
def admin_1Query():
    tablename = 'Скласти список працівників, що займають посаду касира, відсортованих за прізвищем'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT * 
                              FROM EMPLOYEE 
                              WHERE ROLE='cashier'
                              ORDER BY EMPL_SURNAME 
                    ''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/2Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_2Query():
    category_name = request.form['2QueryName']
    tablename = 'Скласти список товарів, що належать певній категорії, відсортованих за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        toExec = "SELECT * FROM PRODUCT WHERE CATEGORY_NUMBER IN(SELECT CATEGORY_NUMBER FROM CATEGORY WHERE CATEGORY_NAME='" + category_name + "') ORDER BY PRODUCT_NAME "
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/3Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_3Query():
    surname = request.form['3QueryName']
    tablename = 'За прізвищем працівника знайти його телефон та адресу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        toExec = "SELECT EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC, PHONE_NUMBER, CITY, STREET, ZIP_CODE FROM EMPLOYEE WHERE EMPL_SURNAME='" + surname + "'"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/4Query', methods=['get'])
@roles_required('Manager')
def admin_4Query():
    tablename = 'Скласти список усіх виробників, що постачають товари до магазину'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM PRODUCER
                      WHERE ID_PRODUCER IN (
                            SELECT ID_PRODUCER
                            FROM CONSIGNMENT)
                    ''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/5Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_5Query():
    name = request.form['5QueryName']
    tablename = 'За назвою виробника вивести його контактний телефон та адресу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT ID_PRODUCER, RPOD_NAME, PHONE_NUMBER, CITY, STREET, ZIP_CODE FROM PRODUCER WHERE RPOD_NAME='" + name + "'")
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/6Query', methods=['get'])
@roles_required('Manager')
def admin_6Query():
    tablename = 'Скласти список усіх товарів, відсортованих за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT PRODUCT.ID_PRODUCT, PRODUCT_NAME, CHARACTERISTICS, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT
                      FROM PRODUCT INNER JOIN STORE_PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT
                      ORDER BY PRODUCT_NAME''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/7Query', methods=['get'])
@roles_required('Manager')
def admin_7Query():
    tablename = 'Скласти список усіх категорій, відсортованих за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM CATEGORY
                      ORDER BY CATEGORY_NAME''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/8Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_8Query():
    category_name = request.form['8QueryName']
    tablename = 'Скласти список всіх товарів, що належать певній категорії'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM PRODUCT WHERE CATEGORY_NUMBER IN(SELECT CATEGORY_NUMBER FROM CATEGORY WHERE CATEGORY_NAME='" + category_name + "')")
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/9Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_9Query():
    product_id = request.form['9QueryName']
    tablename = 'Скласти список товарів у магазині, що належать певному товару'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM STORE_PRODUCT WHERE ID_PRODUCT='" + product_id + "'")
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/10Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_10Query():
    upc = request.form['10QueryName']
    tablename = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT SELLING_PRICE, PRODUCTS_NUMBER FROM STORE_PRODUCT WHERE UPC='" + upc + "'")
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/11Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_11Query():
    order_by = request.form['11QueryName1']  # quan or name
    sortType = request.form['11QueryName2']  # ASC or DESC
    tablename = 'Скласти список усіх акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM STORE_PRODUCT WHERE PROMOTIONAL_PRODUCT=1 ORDER BY {} {}".format(order_by, sortType))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/12Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_12Query():
    order_by = request.form['12QueryName1']  # quan or name
    sortType = request.form['12QueryName2']  # ASC or DESC
    tablename = 'Скласти список усіх не акційних товарів, відсортованих за кількістю одиниць товару/ за назвою'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM STORE_PRODUCT WHERE PROMOTIONAL_PRODUCT=0 ORDER BY {} {}".format(order_by, sortType))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/13Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_13Query():
    product_id = request.form['13QueryName1']
    date_from = request.form['13QueryName2']
    date_to = request.form['13QueryName3']
    tablename = 'Скласти список усіх накладних на певний товар, підписаних виробником за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM CONSIGNMENT WHERE UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT={}) AND SIGNATURE_DATE BETWEEN {} AND {}".format(
                product_id, date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/14Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_14Query():
    producer_id = request.form['14QueryName1']
    date_from = request.form['14QueryName2']
    date_to = request.form['14QueryName3']
    tablename = 'Скласти список усіх накладних, підписаних певним виробником за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM CONSIGNMENT WHERE ID_PRODUCER={} AND SIGNATURE_DATE BETWEEN {} AND {}} ".format(producer_id,
                                                                                                           date_from,
                                                                                                           date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/15Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_15Query():
    date_from = request.form['15QueryName1']
    date_to = request.form['15QueryName2']
    tablename = 'Скласти список усіх накладних, підписаних будь-яким виробником за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CONSIGNMENT WHERE SIGNATURE_DATE BETWEEN {} AND {}".format(date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/16Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_16Query():
    product_id = request.form['16QueryName1']
    date_from = request.form['16QueryName2']
    date_to = request.form['16QueryName3']
    tablename = 'Визначити загальну кількість закуплених одиниць певного товару за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCTS_NUMBER) AS QUANTITY FROM CONSIGNMENT WHERE SIGNATURE_DATE BETWEEN {} AND {}  AND UPC IN(SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT={}) ".format(
                date_from, date_to, product_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/17Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_17Query():
    product_id = request.form['17QueryName1']
    date_from = request.form['17QueryName2']
    date_to = request.form['17QueryName3']
    tablename = 'Скласти список усіх договорів повернення на певний товар, підписаних виробником за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN {} AND {} AND UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT={})".format(
                date_from, date_to, product_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/18Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_18Query():
    producer_id = request.form['18QueryName1']
    date_from = request.form['18QueryName2']
    date_to = request.form['18QueryName3']
    tablename = 'Скласти список усіх договорів повернення, підписаних певним виробникам за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN {} AND {} AND ID_PRODUCER={}".format(date_from,
                                                                                                             date_to,
                                                                                                             producer_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/19Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_19Query():
    date_from = request.form['19QueryName1']
    date_to = request.form['19QueryName2']
    tablename = 'Скласти список усіх договорів повернення, підписаних будь-яким виробникам за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN {} AND {}".format(date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/20Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_20Query():
    product_id = request.form['20QueryName1']
    date_from = request.form['20QueryName2']
    date_to = request.form['20QueryName3']
    tablename = 'Визначити загальну кількість повернених одиниць певного товару за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCT_NUMBER) FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN {} AND {} AND UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT={})".format(
                date_from, date_to, product_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/21Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_21Query():
    cashier_id = request.form['21QueryName1']
    date_from = request.form['21QueryName2']
    date_to = request.form['21QueryName3']
    tablename = 'Скласти список чеків, видрукуваних певним касиром за певний період часу (з можливістю перегляду куплених товарів, їх к-сті та ціни)'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, SALE.UPC, PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN {} AND {}  AND ID_EMPLOYEE={}".format(
                date_from, date_to, cashier_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/22Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_22Query():
    date_from = request.form['22QueryName1']
    date_to = request.form['22QueryName2']
    tablename = 'Скласти список чеків, видрукуваних усіма касирами за певний період часу (з можливістю перегляду куплених товарів, їх к-сті та ціни)'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, SALE.UPC, PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN {} AND {}".format(
                date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/23Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_23Query():
    product_id = request.form['23QueryName1']
    date_from = request.form['23QueryName2']
    date_to = request.form['23QueryName3']
    tablename = 'Визначити загальну кількість одиниць певного товару, проданого за певний період часу'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCT_NUMBER) AS QUANTITY FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN {} AND {} AND PRODUCT.ID_PRODUCT={}".format(
                date_from, date_to, product_id))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/24Query', methods=['get'])
@roles_required('Manager')
def admin_24Query():
    tablename = 'Скласти список усіх постійних клієнтів, що мають карту клієнта, по полях ПІБ, телефон, адреса (якщо вказана)'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC, PHONE_NUMBER, CITY, STREET, ZIP_CODE
                      FROM CUSTOMER_CARD''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/25Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_25Query():
    percent = request.form['25QueryName']
    tablename = 'Скласти список усіх постійних клієнтів, що мають карту клієнта із певним відсотком'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CUSTOMER_CARD WHERE PERCENT={}".format(percent))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/26Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_26Query():
    upc = request.form['26QueryName']
    tablename = 'За UPC-товару знайти ціну продажу товару, кількість наявних одиниць товару, назву та характеристики товару'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT STORE_PRODUCT.UPC, STORE_PRODUCT.ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PRODUCT_NAME, CHARACTERISTICS FROM STORE_PRODUCT INNER JOIN PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT WHERE UPC={}".format(
                upc))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)
