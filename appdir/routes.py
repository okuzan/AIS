import datetime
import random
import sqlite3 as sql
from collections import namedtuple

from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash
from flask import session
from flask_user import login_required, roles_required

from forms import CategoryForm, ProducerForm
from forms import CheckForm
from forms import EmployeeForm, ProductForm, CustomerForm, StoreProductForm, \
    ReturnContractForm, ConsignmentForm, SaleForm
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


@blueprint.route('/cashier/data', methods=['get'])
@roles_required(['Cashier', 'Manager'])
def cashier_data():
    con = sql.connect('dbs/zlagoda.db')
    con.row_factory = sql.Row
    cur = con.cursor()

    # Data for Cheque
    cur.execute("select * from cheque")
    namesCheque = [description[0] for description in cur.description]
    rowsCheque = cur.fetchall()

    # Data for Customer_Card
    cur.execute("select * from customer_card")
    namesCustomer_Card = [description[0] for description in cur.description]
    rowsCustomer_Card = cur.fetchall()
    cur.close()
    con.close()

    return render_template('cashier_data.html', title='All Data',
                           tablenameCheque='Cheque', namesCheque=namesCheque, rowsCheque=rowsCheque,
                           tablenameCustomer_Card='Customer Card', namesCustomer_Card=namesCustomer_Card,
                           rowsCustomer_Card=rowsCustomer_Card)


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


@blueprint.route('/queries/', methods=['get', 'post'])
def queries():
    tablename = 'Own Queries'
    # Oleh
    _1Query = '?? ?????? ?????? ?????????? ?? ???????????? ?????? ?????????? _ ???? ?????????? _ ?????????????????? ?????????????? ?????????????? ???? ?????????????????? ????????'
    _2Query = '?????????????? ????????????????, ?????? ?????????? ???????????? ???????? ?????????????????? _ ?? ???????????? ?? _ ???? _'
    _3Query = '???? ?????? ?????????????????? ???????????????????? _ ???????????????? ?????????????????? ????????????'
    _4Query = '???????? ???????? ???????????????????? ?????????????? ???? ???????????????????? ?? ???????????? ?? _ ???? _'

    # Taya
    _5Query = '???????????? ???????????????? ?????? ???????????????? ???????? ?????????????? ???????????? ?? ???????????? ?? _ ???? _'
    _6Query = '?????????????? ?????????????????? ???????????????? ?????????????? ?? ???????????? ?? _ ???? _'
    _7Query = '?????????????? ???????????????????? ???? ???????? ???? ?????? ???????? ?????????????? ?????????????? ?? _ ???? _'
    _8Query = '?????????????? ???????? ????????????????????, ?????? ???????????????????? ???????????? ???????? ??  _  ??????????????????'

    # Andrii
    _9Query = '???????????? ???????? ??????????????????????(????????????????????), ?????? ???????????????????? ???????? ?? ???????? ????????????????, ?????? ???????????????????? ???????????????? _'
    _10Query = '?????????????? ???????? ?????????????????? ?????????????????? ?????????????????? ?? ????????????????'
    _11Query = '???????????? ???????? ?????????????????? ???????????????? ????????????????????????'
    _12Query = '???????????? ???????? ??????????????????????, ?????? ?????????????????? ???????????? ???? ???????????????? ????????????????????, ?????? ???????????????? ???????????????? _'

    try:
        
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()

        # 2 Query
        toExec = "SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _2QueryRows = []
        for i in range(0, len(tmp)):
            _2QueryRows.append(tmp[i][names[1]])

        # 3 Query
        toExec = "SELECT CUST_SURNAME FROM CUSTOMER_CARD ORDER BY CUST_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _3QueryRows = []
        for i in range(0, len(tmp)):
            _3QueryRows.append(tmp[i][names[0]])

        # 8 Query
        toExec = "SELECT CATEGORY_NAME FROM CATEGORY ORDER BY CATEGORY_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _8QueryRows = []
        for i in range(0, len(tmp)):
            _8QueryRows.append(tmp[i][names[0]])

        # 9 Query
        toExec = "SELECT RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _9QueryRows = []
        for i in range(0, len(tmp)):
            _9QueryRows.append(tmp[i][names[0]])

        # 12 Query
        toExec = "SELECT RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _12QueryRows = []
        for i in range(0, len(tmp)):
            _12QueryRows.append(tmp[i][names[0]])

        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()

    return render_template('queries.html', tablename=tablename, _1Query=_1Query,
                                                                _2Query=_2Query, _2QueryRows=_2QueryRows,
                                                                _3Query=_3Query, _3QueryRows=_3QueryRows,
                                                                _4Query=_4Query,
                                                                _5Query=_5Query,
                                                                _6Query=_6Query,
                                                                _7Query=_7Query,
                                                                _8Query=_8Query, _8QueryRows=_8QueryRows,
                                                                _9Query=_9Query, _9QueryRows=_9QueryRows,
                                                                _10Query=_10Query,
                                                                _11Query=_11Query,
                                                                _12Query=_12Query, _12QueryRows=_12QueryRows)


@blueprint.route('/own_1Query', methods=['get', 'post'])
def own_1Query():
    date_from = request.form['1QueryName1']
    date_to = request.form['1QueryName2']
    tablename = '?? ?????? ?????? ?????????? ?? ???????????? ?????? ?????????? _ ???? ?????????? _ ?????????????????? ?????????????? ?????????????? ???? ?????????????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT SUM(WHOLE_TABLE.SUM_TOTAL) AS TOTAL_SPENT, strftime('%w', WHOLE_TABLE.PRINT_DATE) AS PRINT_DATE
                        FROM (CUSTOMER_CARD CC 
                        INNER JOIN CHEQUE CH ON CH.CARD_NUMBER = CC.CARD_NUMBER  
                        INNER JOIN SALE S ON S.CHECK_NUMBER = CH.CHECK_NUMBER  
                        INNER JOIN STORE_PRODUCT SP ON SP.UPC = S.UPC  
                        INNER JOIN PRODUCT P ON SP.ID_PRODUCT = P.ID_PRODUCT 
                        INNER JOIN CATEGORY CAT ON CAT.CATEGORY_NUMBER = P.CATEGORY_NUMBER) WHOLE_TABLE 
                        WHERE CH.PRINT_DATE BETWEEN ? AND ?  
                        GROUP BY strftime('%w', WHOLE_TABLE.PRINT_DATE) 
                        ORDER BY TOTAL_SPENT DESC 
                        LIMIT 1 ''', (date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_2Query', methods=['get', 'post'])
def own_2Query():
    prod_name = request.form['2QuerySelect']
    date_from = request.form['2QueryName1']
    date_to = request.form['2QueryName2']
    tablename = '?????????????? ????????????????, ?????? ?????????? ???????????? ???????? ?????????????????? _ ?? ???????????? ?? _ ???? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC  
                FROM CUSTOMER_CARD 
                WHERE CARD_NUMBER NOT IN ( 
                        SELECT CC.CARD_NUMBER 
                        FROM (CUSTOMER_CARD CC 
              INNER JOIN CHEQUE CH ON CH.CARD_NUMBER = CC.CARD_NUMBER  
              INNER JOIN SALE S ON S.CHECK_NUMBER = CH.CHECK_NUMBER) SSS   
                        WHERE (SSS.UPC IN(                             
                                SELECT UPC  
                                FROM CONSIGNMENT 
                                WHERE ID_PRODUCER NOT IN ( 
                                        SELECT ID_PRODUCER  
                                        FROM PRODUCER 
                                        WHERE RPOD_NAME = ? 
                                        ) 
                                ) AND PRINT_DATE BETWEEN ? AND ?) 
                                OR UPC IN ( 
                                SELECT UPC 
                                FROM STORE_PRODUCT SP 
                                WHERE NOT EXISTS ( 
                                                    SELECT * 
                                                    FROM CONSIGNMENT C 
                                                    WHERE C.UPC = SP.UPC  
                                                )                                     
                                )     
                                ) 
                                AND CARD_NUMBER IN ( 
                                SELECT CARD_NUMBER 
                                FROM CHEQUE 
                                WHERE PRINT_DATE BETWEEN ? AND ?      
                        ) ''', (prod_name, date_from, date_to, date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_3Query', methods=['get', 'post'])
def own_3Query():
    surname = request.form['3QuerySelect']
    tablename = '???? ?????? ?????????????????? ???????????????????? _ ???????????????? ?????????????????? ????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT SUM (CH.SUM_TOTAL) AS TOTAL_SPENT, CAT.CATEGORY_NAME 
                        FROM CUSTOMER_CARD CC 
                        INNER JOIN CHEQUE CH ON CH.CARD_NUMBER = CC.CARD_NUMBER  
                        INNER JOIN SALE S ON S.CHECK_NUMBER = CH.CHECK_NUMBER  
                        INNER JOIN STORE_PRODUCT SP ON SP.UPC = S.UPC  
                        INNER JOIN PRODUCT P ON SP.ID_PRODUCT = P.ID_PRODUCT 
                        INNER JOIN CATEGORY CAT ON CAT.CATEGORY_NUMBER = P.CATEGORY_NUMBER 
                        WHERE CC.CARD_NUMBER IN ( 
                                                SELECT CARD_NUMBER 
                                                FROM CUSTOMER_CARD 
                                                WHERE CUST_SURNAME = ? 
                                                )    
                        GROUP BY CAT.CATEGORY_NUMBER  
                        ORDER BY TOTAL_SPENT DESC 
                        LIMIT 1 ''', (surname,))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_4Query', methods=['get', 'post'])
def own_4Query():
    date_from = request.form['4QueryName1']
    date_to = request.form['4QueryName2']
    tablename = '???????? ???????? ???????????????????? ?????????????? ???? ???????????????????? ?? ???????????? ?? _ ???? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT SUM(R.SUM_TOTAL) AS TOTAL_SUM, CAT.CATEGORY_NAME  
                        FROM RETURN_CONTRACT R 
                        INNER JOIN STORE_PRODUCT S ON S.UPC = R.UPC  
                        INNER JOIN PRODUCT P ON S.ID_PRODUCT = P.ID_PRODUCT  
                        INNER JOIN CATEGORY CAT ON CAT.CATEGORY_NUMBER = P.CATEGORY_NUMBER  
                        WHERE SIGNATURE_DATE BETWEEN ? AND ?  
                        GROUP BY CAT.CATEGORY_NUMBER ''', (date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_5Query', methods=['get', 'post'])
def own_5Query():
    date_from = request.form['5QueryName1']
    date_to = request.form['5QueryName2']
    tablename = '???????????? ???????????????? ?????? ???????????????? ???????? ?????????????? ???????????? ?? ???????????? ?? _ ???? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT CARD_NUMBER, CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC 
                    FROM CUSTOMER_CARD 
                    WHERE CARD_NUMBER NOT IN ( 
                         SELECT CARD_NUMBER 
                         FROM CHEQUE 
                         WHERE CHECK_NUMBER IN ( 
                                  SELECT CHECK_NUMBER 
                                  FROM SALE 
                                  WHERE UPC IN ( 
                                          SELECT UPC  
                                          FROM STORE_PRODUCT 
                                          WHERE PROMOTIONAL_PRODUCT=0)) 
                                          AND PRINT_DATE BETWEEN ? AND ? 
                                          
                    ) AND CARD_NUMBER IN ( 
                                            SELECT CARD_NUMBER 
                                            FROM CHEQUE 
                                            WHERE PRINT_DATE BETWEEN ? AND ? 
                                        ) ''', (date_from, date_to, date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_6Query', methods=['get', 'post'])
def own_6Query():
    date_from = request.form['6QueryName1']
    date_to = request.form['6QueryName2']
    tablename = '?????????????? ?????????????????? ???????????????? ?????????????? ?? ???????????? ?? _ ???? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT PRODUCT.ID_PRODUCT, PRODUCT.PRODUCT_NAME, COUNT(PRODUCT_NUMBER) AS QUANTITY 
                        FROM  PRODUCT INNER JOIN STORE_PRODUCT  
                        ON STORE_PRODUCT.ID_PRODUCT = PRODUCT.ID_PRODUCT 
                        INNER JOIN SALE ON STORE_PRODUCT.UPC=SALE.UPC 
                        INNER JOIN CHEQUE  
                        ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER 
                        WHERE CHEQUE.PRINT_DATE BETWEEN ? AND ? 
                        GROUP BY PRODUCT.ID_PRODUCT, PRODUCT.PRODUCT_NAME 
                        ORDER BY QUANTITY DESC ''', (date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_7Query', methods=['get', 'post'])
def own_7Query():
    date_from = request.form['7QueryName1']
    date_to = request.form['7QueryName2']
    tablename = '?????????????? ???????????????????? ???? ???????? ???? ?????? ???????? ?????????????? ?????????????? ?? _ ???? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT EMPLOYEE.ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC, ROLE, 
                        SUM(SUM_TOTAL) AS TOTAL_SUM   
                        FROM EMPLOYEE INNER JOIN CHEQUE  
                        ON EMPLOYEE.ID_EMPLOYEE = CHEQUE.ID_EMPLOYEE 
                        WHERE CHEQUE.PRINT_DATE BETWEEN ? AND ? 
                        GROUP BY EMPLOYEE.ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC   
                         ORDER BY TOTAL_SUM DESC''', (date_from, date_to))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_8Query', methods=['get', 'post'])
def own_8Query():
    category_name = request.form['8QuerySelect']
    tablename = '?????????????? ???????? ????????????????????, ?????? ???????????????????? ???????????? ???????? ??  _  ??????????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT * 
                        FROM PRODUCER 
                        WHERE ID_PRODUCER NOT IN ( 
                                SELECT ID_PRODUCER 
                                FROM CONSIGNMENT  
                                WHERE UPC IN ( 
                                      SELECT UPC 
                                      FROM STORE_PRODUCT 
                                      WHERE ID_PRODUCT IN ( 
                                             SELECT ID_PRODUCT 
                                             FROM PRODUCT 
                                            WHERE CATEGORY_NUMBER NOT IN( 
                                                                        SELECT CATEGORY_NUMBER 
                                                                        FROM CATEGORY 
                                                                        WHERE CATEGORY_NAME=?)) 
                                                            ) 
                                              ) AND ID_PRODUCER IN ( 
                                                            SELECT ID_PRODUCER 
                                                            FROM CONSIGNMENT  
                                              ) ''', (category_name,))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_9Query', methods=['get', 'post'])
def own_9Query():
    producer = request.form['9QuerySelect']
    tablename = '???????????? ???????? ??????????????????????(????????????????????), ?????? ???????????????????? ???????? ?? ???????? ????????????????, ?????? ???????????????????? ???????????????? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC 
                        FROM EMPLOYEE E 
                        WHERE E.ROLE = 'manager' 
                        AND E.ID_EMPLOYEE in (SELECT ID_EMPLOYEE 
                   		                        FROM CONSIGNMENT CT 
			      	                            WHERE CT.ID_PRODUCER IN (SELECT ID_PRODUCER 
                                                                       		FROM PRODUCER 
                                                                       	    WHERE RPOD_NAME = ?
            							                                ) 
                                            ); 
                        ''', (producer,))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_10Query', methods=['get'])
def own_10Query():
    tablename = '?????????????? ???????? ?????????????????? ?????????????????? ?????????????????? ?? ????????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT Res.CATEGORY_NUMBER, Res.CATEGORY_NAME 
                  FROM ((CATEGORY C INNER JOIN PRODUCT P ON C.CATEGORY_NUMBER = P.CATEGORY_NUMBER) 
                                    INNER JOIN STORE_PRODUCT SP ON P.ID_PRODUCT = SP.ID_PRODUCT) Res 
                  GROUP BY Res.CATEGORY_NUMBER, Res.CATEGORY_NAME 
                  ORDER BY SUM(Res.PRODUCTS_NUMBER) DESC 
                  LIMIT 1;''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_11Query', methods=['get'])
def own_11Query():
    tablename = '???????????? ???????? ?????????????????? ???????????????? ????????????????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT Res.CATEGORY_NUMBER, Res.CATEGORY_NAME 
                  FROM (((CATEGORY C INNER JOIN PRODUCT P ON C.CATEGORY_NUMBER = P.CATEGORY_NUMBER) 
                                     INNER JOIN STORE_PRODUCT SP ON P.ID_PRODUCT = SP.ID_PRODUCT) 
                                     INNER JOIN RETURN_CONTRACT RC ON SP.UPC = RC.UPC) Res 
                  GROUP BY Res.CATEGORY_NUMBER, Res.CATEGORY_NAME 
                  ORDER BY SUM(Res.PRODUCT_NUMBER) 
                  LIMIT 1; ''')
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


@blueprint.route('/own_12Query', methods=['get', 'post'])
def own_12Query():
    producer = request.form['12QuerySelect']
    tablename = '???????????? ???????? ??????????????????????, ?????? ?????????????????? ???????????? ???? ???????????????? ????????????????????, ?????? ???????????????? ???????????????? _'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC 
                  FROM EMPLOYEE E 
                  WHERE E.ROLE = 'manager' 
                        AND NOT EXISTS (SELECT CONTRACT_NUMBER 
                                        FROM RETURN_CONTRACT RC1 
                                        WHERE E.ID_EMPLOYEE = RC1.ID_EMPLOYEE 
                                              AND CONTRACT_NUMBER NOT IN (SELECT CONTRACT_NUMBER 
                                                                          FROM RETURN_CONTRACT RC2 
                                                                          WHERE RC2.ID_PRODUCER IN (SELECT ID_PRODUCER 
                                                                                                    FROM PRODUCER 
                                                                                                    WHERE RPOD_NAME = ? 
                                                                                                    ) 
                                                                          ) 
                                        ); ''', (producer,))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)


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


@blueprint.route('/table/<table>/')
@roles_required('Manager')  # Use of @roles_required decorator
def table(table):
    tablename = table if ' ' not in table else table.replace(' ', '_')
    con = sql.connect('dbs/zlagoda.db')
    con.row_factory = sql.Row
    cur = con.cursor()
    str_req = "select * from " + str(tablename)
    cur.execute(str_req)
    names = [description[0] for description in cur.description]
    rows = cur.fetchall()
    cur.close()
    con.close()
    tableUp = table.upper()
    return render_template('table.html', tablename=tablename, names=names, rows=rows, title=tableUp)


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
    form = ReturnContractForm()
    form.upc.data = row[0]
    form.employee.data = row[2]
    form.quantity.data = str(row[5])
    form.signature_date.data = datetime.strptime(str(row[4]), '%Y-%m-%d')

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
    form.upc.data = row[3]
    form.producer.data = row[1]
    form.employee.data = row[2]
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
@roles_required(['Cashier', 'Manager'])  # Use of @roles_required decorator
def update_cheque(rowid):
    con = sql.connect('dbs/zlagoda.db')
    cur = con.cursor()
    cur.execute("SELECT * FROM CHEQUE LIMIT 1 OFFSET " + (str(rowid - 1))),
    row = cur.fetchall()[0]
    cur.execute('''SELECT UPC, CHECK_NUMBER, PRODUCT_NUMBER
                   FROM SALE
                   WHERE CHECK_NUMBER = ?
                   ''', (row[0]))
    sales = cur.fetchall()
    print("sales")
    print(sales)
    sale = namedtuple('Sale', ['upc_code', 'check_number', 'quantity'])
    sales_arr = [sale(i[0], i[1], i[2]) for i in sales]
    data = {
        # 'sales': [
        #     sale('Bread_FIRST_LINE', 1),
        # ]
        'sales': sales_arr
    }

    print(row)
    print("sales")
    print(sales)

    cur.execute('''SELECT ID_EMPLOYEE, EMPL_SURNAME, EMPL_NAME, EMPL_PATRONYMIC
                   FROM EMPLOYEE
                   WHERE ROLE="cashier"''')
    result = cur.fetchall()
    empl_choices = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result]

    cur.execute('''SELECT CARD_NUMBER, CUST_SURNAME, CUST_NAME, CUST_PATRONYMIC
                          FROM CUSTOMER_CARD''')
    result2 = cur.fetchall()
    card_choices = [(i[0], "(" + str(i[0]) + ") " + i[1] + " " + i[2] + " " + i[3]) for i in result2]

    # form.card.text = "!row[2]"
    form = CheckForm(data=data)
    form.employee.choices = empl_choices
    form.card.choices = card_choices + [("", "---")]
    form.employee.data = row[1]  # TODO default
    form.card.data = row[2]  # TODO default

    if form.is_submitted():
        try:
            sales_data = []
            for lp in range(len(sales)):
                req_str1 = "sales-" + str(lp) + "-upc_code"
                req_str2 = "sales-" + str(lp) + "-quantity"
                req_str3 = "sales-" + str(lp) + "-check_number"
                upc_code = request.form[req_str1]
                print(upc_code)

                quantity = request.form[req_str2]
                print(quantity)

                check_number = request.form[req_str3]
                print(check_number)
                print("this upc")
                print(sales[lp][0])
                cur.execute('''UPDATE SALE
                 SET UPC = ?, PRODUCT_NUMBER = ?
                 WHERE UPC = ? AND CHECK_NUMBER = ?''', (
                    upc_code, quantity, sales[lp][0], check_number
                ))
                con.commit()
                cur.execute('''SELECT SELLING_PRICE
                 FROM SALE
                 WHERE UPC = ? AND CHECK_NUMBER = ?''', (
                    sales[lp][0], check_number
                ))
                price = cur.fetchall()[0][0]
                print("price")
                print(price)
                sale_data = [upc_code, check_number, quantity, price]
                sales_data.append(sale_data)
                con.commit()

            print("sales_data")
            print(sales_data)
            sum_total = 0
            cur.execute('''SELECT PERCENT 
                         FROM CUSTOMER_CARD
                         WHERE CARD_NUMBER=?''', (form.card.data,))
            result = cur.fetchall()

            percent = result[0][0]
            print("percent")
            print(percent)

            for sale in sales_data:
                sum_total += int(sale[2]) * int(sale[3])
            if percent != 0:
                sum_total = 0.01 * (100 - percent) * sum_total

            sum_total = round(sum_total, 2)
            vat = round(0.2 * sum_total / 1.2, 2)
            print("vat")
            print(vat)
            print("sum_total")
            print(sum_total)
            cur.execute('''UPDATE CHEQUE
             SET ID_EMPLOYEE = ?, CARD_NUMBER = ?,
             SUM_TOTAL = ?, VAT = ?
             WHERE CHECK_NUMBER = (SELECT CHECK_NUMBER FROM CHEQUE LIMIT 1 OFFSET ?)''', (
                request.form['employee'],
                request.form['card'],
                sum_total,
                vat,
                str(rowid - 1)))
            con.commit()
            cur.close()
            flash('Cheque was successfully updated', 'success')
            return redirect(url_for('blueprint.home_page'))
        except sql.Error as error:
            flash(error, 'danger')
            return render_template('check_update.html', form=form, title='Update Cheque')
        finally:
            if (con):
                con.close()
    return render_template('check_update.html', form=form, title='Update Cheque')


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
    form.category_number.data = row[1]
    form.product_name.data = row[2]
    form.characteristics.data = row[3]

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
    form.upc_prom.choices = [('-1', '---')] + groups_list

    # form.category_number = row[1]
    print(row)
    form.upc_code.data = row[0]
    form.quantity.data = str(row[4])
    form.product_number.data = row[2]
    if str(row[1]) != 'None':
        form.upc_prom.data = row[1]
    form.promotional.data = str(row[5])

    if form.is_submitted():
        try:
            if form.upc_prom.data.__len__() < 12:
                cur.execute('''UPDATE STORE_PRODUCT
                                            SET UPC = ?, UPC_PROM = NULL, ID_PRODUCT = ?, 
                                             PRODUCTS_NUMBER = ?, PROMOTIONAL_PRODUCT = ? 
                                            WHERE UPC = (SELECT UPC FROM STORE_PRODUCT LIMIT 1 OFFSET ?)''', (
                    request.form['upc_code'],
                    request.form['product_number'],
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


@blueprint.route('/<int:rowid>/update-sale', methods=['get', 'post'])
@roles_required('Manager')  # Use of @roles_required decorator
def update_sale(rowid):
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
    form.upc_prom.choices = [('-1', '---')] + groups_list

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
@roles_required(['Cashier', 'Manager'])  # Use of @roles_required decorator
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
    form.card.choices = [("", "---")] + groups_list
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
            max_id = 'c' + str(num)
            sale_prices = []
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sum_total = 0
            percent = 0
            if form.card.data.__len__() > 0:
                cur.execute('''SELECT PERCENT 
                             FROM CUSTOMER_CARD
                             WHERE CARD_NUMBER=?''', (form.card.data,))
                result = cur.fetchall()
                percent = result[0][0]
            for s in form.sales.data:
                cur.execute('''SELECT SELLING_PRICE, PRODUCTS_NUMBER
                               FROM STORE_PRODUCT
                               WHERE UPC=?''', (s['upc_code'],))
                result = cur.fetchall()
                if result.__len__() != 1:
                    flash('Incorrect UPC', 'danger')
                    return render_template('checkForm.html', form=form, title='Add check')
                if result[0][1] < int(s['quantity']):
                    flash('Incorrect Quantity', 'danger')
                    return render_template('checkForm.html', form=form, title='Add check')
                sale_prices = sale_prices + [(result[0][0], s['quantity'], s['upc_code'], result[0][1])]
            for sale in sale_prices:
                sum_total += int(sale[1]) * int(sale[0])
            if percent != 0:
                sum_total = 0.01 * (100 - percent) * sum_total
            sum_total = round(sum_total, 2)
            vat = round(0.2 * sum_total / 1.2, 2)
            if form.card.data.__len__() > 0:
                cur.execute('''INSERT INTO CHEQUE(CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT)
                                                              VALUES (?, ?, ?, ?, ?, ?);''',
                            (max_id, form.employee.data,
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
                cur.execute('''UPDATE STORE_PRODUCT
                                          SET PRODUCTS_NUMBER = ?
                                          WHERE UPC=?''', (int(sale[3]) - int(sale[1]), sale[2]))
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
@roles_required(['Cashier', 'Manager'])
def cashier_queries():
    tablename = 'Cashier Queries'
    _1Query = '?????????????? ???????????? ??????????,  ???????????????????????? ?????????? ?????????????? ???? ???????????? ???????????? ????????'
    _2Query = '???? ?????????????? ???????? ?????????????? ?????? ???????????????????? ?????? ?????????? ??????'
    _3Query = '?????????????? ?????? ???????????????????? ?????? ?????????????? ?? ???????????? ??????????????????, ???? ?????? ?????????? ??????????????'
    _4Query = '???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ?????????????? ?? ???????????? ??????????????????'
    _5Query = '?????????????? ???????????? ??????????????, ???? ???????????????? ???????????? ??????????????????, ?????????????????????????? ???? ????????????'
    _6Query = '?????????????? ???????????? ???????? ??????????????, ?????????????????????????? ???? ????????????'
    _7Query = '?????????????? ???????????? ???????? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
    _8Query = '?????????????? ???????????? ???????? ???? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
    _9Query = '???? ?????????????? ???????? ?????????????? ???????????? ???????? ??????????????, ???????????????????? ?????? ???????????? ???????? ?? ?? ?????????? ????????'
    _10Query = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????'
    _11Query = '???? ID_???????????????????? ???????????? ?????? ???????????????????? ?????? ????????'

    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()

        # 1 Query
        toExec = "SELECT ID_EMPLOYEE, EMPL_SURNAME FROM EMPLOYEE WHERE ROLE='cashier' ORDER BY EMPL_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _1QueryCRows = []
        for i in range(0, len(tmp)):
            _1QueryCRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 2 Query
        toExec = "SELECT CHECK_NUMBER FROM CHEQUE ORDER BY CHECK_NUMBER DESC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _2QueryCRows = []
        for i in range(0, len(tmp)):
            _2QueryCRows.append(tmp[i][names[0]])

        # 3 Query
        toExec = "SELECT CUST_SURNAME FROM CUSTOMER_CARD ORDER BY CUST_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _3QueryCRows = []
        for i in range(0, len(tmp)):
            _3QueryCRows.append(tmp[i][names[0]])

        # 5 Query
        toExec = "SELECT CATEGORY_NAME FROM CATEGORY ORDER BY CATEGORY_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _5QueryCRows = []
        for i in range(0, len(tmp)):
            _5QueryCRows.append(tmp[i][names[0]])

        # 9 Query
        toExec = "SELECT CHECK_NUMBER FROM CHEQUE ORDER BY CHECK_NUMBER DESC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _9QueryCRows = []
        for i in range(0, len(tmp)):
            _9QueryCRows.append(tmp[i][names[0]])

        # 10 Query
        toExec = "SELECT UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _10QueryCRows = []
        for i in range(0, len(tmp)):
            _10QueryCRows.append(tmp[i][names[0]])

        # 11 Query
        toExec = "SELECT ID_EMPLOYEE, EMPL_SURNAME FROM EMPLOYEE WHERE ROLE='cashier' ORDER BY EMPL_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _11QueryCRows = []
        for i in range(0, len(tmp)):
            _11QueryCRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()

    return render_template('cashier_queries.html', tablename=tablename, _1Query=_1Query, _1QueryCRows=_1QueryCRows,
                           _2Query=_2Query, _2QueryCRows=_2QueryCRows,
                           _3Query=_3Query, _3QueryCRows=_3QueryCRows,
                           _4Query=_4Query,
                           _5Query=_5Query, _5QueryCRows=_5QueryCRows,
                           _6Query=_6Query,
                           _7Query=_7Query,
                           _8Query=_8Query,
                           _9Query=_9Query, _9QueryCRows=_9QueryCRows,
                           _10Query=_10Query, _10QueryCRows=_10QueryCRows,
                           _11Query=_11Query, _11QueryCRows=_11QueryCRows)


@blueprint.route('/1QueryC', methods=['get', 'post'])
@roles_required(['Cashier', 'Manager'])
def cashier_1Query():
    cashier_id = request.form['1QueryCSelect']
    date_from = request.form['1QueryCName1']
    date_to = request.form['1QueryCName2']
    tablename = '?????????????? ???????????? ??????????,  ???????????????????????? ?????????? ?????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM CHEQUE WHERE PRINT_DATE BETWEEN '{}' AND '{}' AND ID_EMPLOYEE='{}'".format(date_from,
                                                                                                      date_to,
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
@roles_required(['Cashier', 'Manager'])
def cashier_2Query():
    check_number = request.form['2QueryCSelect']
    tablename = '???? ?????????????? ???????? ?????????????? ?????? ???????????????????? ?????? ?????????? ??????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, 
                            SALE.UPC,   PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME
                      FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER
                      INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC
                      INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT
                      WHERE CHEQUE.CHECK_NUMBER=?''', (check_number,))
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
@roles_required(['Cashier', 'Manager'])
def cashier_3Query():
    surname = request.form['3QueryCSelect']
    tablename = '?????????????? ?????? ???????????????????? ?????? ?????????????? ?? ???????????? ??????????????????, ???? ?????? ?????????? ??????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM CUSTOMER_CARD
                      WHERE CUST_SURNAME=?''', (surname,))
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
@roles_required(['Cashier', 'Manager'])
def cashier_4Query():
    percent = request.form['4QueryCName']
    tablename = '???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ?????????????? ?? ???????????? ??????????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CUSTOMER_CARD WHERE PERCENT='{}'".format(percent))
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
@roles_required(['Cashier', 'Manager'])
def cashier_5Query():
    category_name = request.form['5QueryCSelect']
    tablename = '?????????????? ???????????? ??????????????, ???? ???????????????? ???????????? ??????????????????, ?????????????????????????? ???? ????????????'
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
@roles_required(['Cashier', 'Manager'])
def cashier_6Query():
    tablename = '?????????????? ???????????? ???????? ??????????????, ?????????????????????????? ???? ????????????'
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
@roles_required(['Cashier', 'Manager'])
def cashier_7Query():
    if request.form['7QueryCSelect1'] == '?????????????????? ??????????????':
        order_by = 'PRODUCTS_NUMBER'
    else:
        order_by = 'UPC'
    if request.form['7QueryCSelect2'] == 'ASC':
        sortType = 'ASC'
    else:
        sortType = 'DESC'
    tablename = '?????????????? ???????????? ???????? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
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
@roles_required(['Cashier', 'Manager'])
def cashier_8Query():
    if request.form['8QueryCSelect1'] == '?????????????????? ??????????????':
        order_by = 'PRODUCTS_NUMBER'
    else:
        order_by = 'UPC'
    if request.form['8QueryCSelect2'] == 'ASC':
        sortType = 'ASC'
    else:
        sortType = 'DESC'
    tablename = '?????????????? ???????????? ???????? ???? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
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
@roles_required(['Cashier', 'Manager'])
def cashier_9Query():
    check_num = request.form['9QueryCSelect']
    tablename = '???? ?????????????? ???????? ?????????????? ???????????? ???????? ??????????????, ???????????????????? ?????? ???????????? ???????? ?? ?? ?????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT PRODUCT_NAME, CHARACTERISTICS, CATEGORY_NAME, SALE.UPC, PRODUCT_NUMBER, SALE.SELLING_PRICE
                      FROM SALE INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC
                      INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT
                      INNER JOIN CATEGORY ON PRODUCT.CATEGORY_NUMBER=CATEGORY.CATEGORY_NUMBER
                      WHERE SALE.CHECK_NUMBER=?''', (check_num,))
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
@roles_required(['Cashier', 'Manager'])
def cashier_10Query():
    upc = request.form['10QueryCSelect']
    tablename = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????, ?????????? ???? ???????????????????????????? ????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT STORE_PRODUCT.UPC, STORE_PRODUCT.ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PRODUCT_NAME, CHARACTERISTICS FROM STORE_PRODUCT INNER JOIN PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT WHERE UPC='{}'".format(
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
@roles_required(['Cashier', 'Manager'])
def cashier_11Query():
    id = request.form['11QueryCSelect']
    tablename = '???? ID_???????????????????? ???????????? ?????? ???????????????????? ?????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute('''SELECT *
                      FROM EMPLOYEE 
                      WHERE ID_EMPLOYEE=?
                   ''', (id,))
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
    groups_list = [(i[0], "(" + str(i[0]) + ") ") for i in result]
    form.upc_prom.choices = [('', '---')] + groups_list

    if form.validate_on_submit():
        try:
            con = sql.connect('dbs/zlagoda.db')
            con.row_factory = sql.Row
            cur = con.cursor()
            if form.upc_prom.data.__len__() < 12:
                if form.quantity.data != '0':
                    flash('You can set only 0 quantity for new no promotional product', 'danger')
                    return render_template('form.html', form=form, title='Add Store Product')
                cur.execute('''INSERT INTO STORE_PRODUCT(UPC, ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT)
                                                  VALUES (?, ?,?, ?, ?);''', (
                    form.upc_code.data, form.product_number.data, 0,
                    0, form.promotional.data))
            else:
                if form.promotional.data == '1':
                    flash('You can`t set UPC prom for promotional product', 'danger')
                    return render_template('form.html', form=form, title='Add Store Product')
                cur.execute('''SELECT PURCHASE_PRICE
                FROM CONSIGNMENT 
                WHERE UPC IN (SELECT UPC
                            FROM STORE_PRODUCT
                            WHERE PROMOTIONAL='0' AND ID_PRODUCT=?
                )''', (form.product_number.data,))
                result = cur.fetchall()
                if result.__len__() < 1:
                    flash('You can`t create promotional product without store product', 'danger')
                    return render_template('form.html', form=form, title='Add Store Product')
                price = round(1.34 * float(result[0][0]), 2)
                cur.execute('''INSERT INTO STORE_PRODUCT(UPC, UPC_PROM, ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PROMOTIONAL_PRODUCT)
                                   VALUES (?, ?, ?, ?, ?, ?);''', (
                    form.upc_code.data, form.upc_prom.data, form.product_number.data, price,
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
            # ??????????. ???????? + ??????????. ???????? * 0,3 + 0,2 * (??????????. ???????? + ??????????. ???????? * 0,3).
            new_price = round(1.56 * float(form.price.data), 2)
            cur.execute("SELECT PRODUCTS_NUMBER FROM STORE_PRODUCT WHERE UPC=?", (form.upc.data,))
            number = cur.fetchall()[0][0]
            cur.execute('''UPDATE STORE_PRODUCT
                           SET SELLING_PRICE = ?, PRODUCTS_NUMBER = ?
                           WHERE UPC=?''', (new_price, number + int(form.quantity.data), form.upc.data))
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
            number = cur.fetchall()[0][0] - int(form.quantity.data)
            if number < 0:
                flash('Result quantity of product after returning must be more than 0', 'danger')
                return render_template('form.html', form=form, title='Add Return Contract')
            cur.execute('''SELECT ID_PRODUCER, PURCHASE_PRICE FROM CONSIGNMENT
            WHERE UPC IN (SELECT UPC
            FROM STORE_PRODUCT
            WHERE UPC=? OR UPC_PROM=?
            ) AND SIGNATURE_DATE IN (SELECT MAX(SIGNATURE_DATE)
            FROM CONSIGNMENT WHERE UPC IN (SELECT UPC
            FROM STORE_PRODUCT
            WHERE UPC=? OR UPC_PROM=?)
            )''', (form.upc.data, form.upc.data, form.upc.data, form.upc.data))
            result = cur.fetchall()
            price = result[0][1]
            prod = result[0][0]

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
                eid, prod, form.employee.data, form.upc.data, form.signature_date.data,
                form.quantity.data,
                price * int(form.quantity.data)))
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
    _1Query = '?????????????? ???????????? ??????????????????????, ???? ???????????????? ???????????? ????????????, ?????????????????????????? ???? ??????????????????'
    _2Query = '?????????????? ???????????? ??????????????, ???? ???????????????? ???????????? ??????????????????, ?????????????????????????? ???? ????????????'
    _3Query = '???? ?????????????????? ???????????????????? ???????????? ???????? ?????????????? ???? ????????????'
    _4Query = '?????????????? ???????????? ???????? ????????????????????, ???? ???????????????????? ???????????? ???? ????????????????'
    _5Query = '???? ???????????? ?????????????????? ?????????????? ???????? ???????????????????? ?????????????? ???? ????????????'
    _6Query = '?????????????? ???????????? ???????? ??????????????, ?????????????????????????? ???? ????????????'
    _7Query = '?????????????? ???????????? ???????? ??????????????????, ?????????????????????????? ???? ????????????'
    _8Query = '?????????????? ???????????? ???????? ??????????????, ???? ???????????????? ???????????? ??????????????????'
    _9Query = '?????????????? ???????????? ?????????????? ?? ????????????????, ???? ???????????????? ?????????????? ????????????'
    _10Query = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????'
    _11Query = '?????????????? ???????????? ???????? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
    _12Query = '?????????????? ???????????? ???????? ???? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
    _13Query = '?????????????? ???????????? ???????? ?????????????????? ???? ???????????? ??????????, ???????????????????? ???????????????????? ???? ???????????? ???????????? ????????'
    _14Query = '?????????????? ???????????? ???????? ??????????????????, ???????????????????? ???????????? ???????????????????? ???? ???????????? ???????????? ????????'
    _15Query = '?????????????? ???????????? ???????? ??????????????????, ???????????????????? ????????-???????? ???????????????????? ???? ???????????? ???????????? ????????'
    _16Query = '?????????????????? ???????????????? ?????????????????? ???????????????????? ?????????????? ?????????????? ???????????? ???? ???????????? ???????????? ????????'
    _17Query = '?????????????? ???????????? ???????? ?????????????????? ???????????????????? ???? ???????????? ??????????, ???????????????????? ???????????????????? ???? ???????????? ???????????? ????????'
    _18Query = '?????????????? ???????????? ???????? ?????????????????? ????????????????????, ???????????????????? ???????????? ???????????????????? ???? ???????????? ???????????? ????????'
    _19Query = '?????????????? ???????????? ???????? ?????????????????? ????????????????????, ???????????????????? ????????-???????? ???????????????????? ???? ???????????? ???????????? ????????'
    _20Query = '?????????????????? ???????????????? ?????????????????? ???????????????????? ?????????????? ?????????????? ???????????? ???? ???????????? ???????????? ????????'
    _21Query = '?????????????? ???????????? ??????????, ???????????????????????? ???????????? ?????????????? ???? ???????????? ???????????? ???????? (?? ???????????????????? ?????????????????? ???????????????? ??????????????, ???? ??-?????? ???? ????????)'
    _22Query = '?????????????? ???????????? ??????????, ???????????????????????? ?????????? ???????????????? ???? ???????????? ???????????? ???????? (?? ???????????????????? ?????????????????? ???????????????? ??????????????, ???? ??-?????? ???? ????????)'
    _23Query = '?????????????????? ???????????????? ?????????????????? ?????????????? ?????????????? ????????????, ?????????????????? ???? ???????????? ???????????? ????????'
    _24Query = '?????????????? ???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ??????????????, ???? ?????????? ??????, ??????????????, ???????????? (???????? ??????????????)'
    _25Query = '?????????????? ???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ?????????????? ???? ???????????? ??????????????????'
    _26Query = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????, ?????????? ???? ???????????????????????????? ????????????'

    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()

        # 2 Query
        toExec = "SELECT CATEGORY_NAME FROM CATEGORY ORDER BY CATEGORY_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _2QueryRows = []
        for i in range(0, len(tmp)):
            _2QueryRows.append(tmp[i][names[0]])

        # 3 Query
        toExec = "SELECT EMPL_SURNAME FROM EMPLOYEE ORDER BY EMPL_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _3QueryRows = []
        for i in range(0, len(tmp)):
            _3QueryRows.append(tmp[i][names[0]])

        # 5 Query
        toExec = "SELECT RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _5QueryRows = []
        for i in range(0, len(tmp)):
            _5QueryRows.append(tmp[i][names[0]])

        # 8 Query
        toExec = "SELECT CATEGORY_NAME FROM CATEGORY ORDER BY CATEGORY_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _8QueryRows = []
        for i in range(0, len(tmp)):
            _8QueryRows.append(tmp[i][names[0]])

        # 9 Query
        toExec = "SELECT ID_PRODUCT, PRODUCT_NAME FROM PRODUCT ORDER BY PRODUCT_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _9QueryRows = []
        for i in range(0, len(tmp)):
            _9QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 10 Query
        toExec = "SELECT UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _10QueryRows = []
        for i in range(0, len(tmp)):
            _10QueryRows.append(tmp[i][names[0]])

        # 13 Query
        toExec = "SELECT ID_PRODUCT, PRODUCT_NAME FROM PRODUCT ORDER BY PRODUCT_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _13QueryRows = []
        for i in range(0, len(tmp)):
            _13QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 14 Query
        toExec = "SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _14QueryRows = []
        for i in range(0, len(tmp)):
            _14QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 16 Query
        toExec = "SELECT ID_PRODUCT, UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _16QueryRows = []
        for i in range(0, len(tmp)):
            _16QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 17 Query
        toExec = "SELECT ID_PRODUCT, UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _17QueryRows = []
        for i in range(0, len(tmp)):
            _17QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 18 Query
        toExec = "SELECT ID_PRODUCER, RPOD_NAME FROM PRODUCER ORDER BY RPOD_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _18QueryRows = []
        for i in range(0, len(tmp)):
            _18QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 20 Query
        toExec = "SELECT ID_PRODUCT, UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _20QueryRows = []
        for i in range(0, len(tmp)):
            _20QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 21 Query
        toExec = "SELECT ID_EMPLOYEE, EMPL_SURNAME FROM EMPLOYEE WHERE ROLE='cashier' ORDER BY EMPL_SURNAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _21QueryRows = []
        for i in range(0, len(tmp)):
            _21QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 23 Query
        toExec = "SELECT ID_PRODUCT, PRODUCT_NAME FROM PRODUCT ORDER BY PRODUCT_NAME"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _23QueryRows = []
        for i in range(0, len(tmp)):
            _23QueryRows.append((tmp[i][names[0]], tmp[i][names[1]]))

        # 26 Query
        toExec = "SELECT UPC FROM STORE_PRODUCT ORDER BY UPC"
        cur.execute(toExec)
        names = [description[0] for description in cur.description]
        tmp = cur.fetchall()
        _26QueryRows = []
        for i in range(0, len(tmp)):
            _26QueryRows.append(tmp[i][names[0]])

        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()

    return render_template('admin_queries.html', tablename=tablename, _1Query=_1Query,
                           _2Query=_2Query, _2QueryRows=_2QueryRows,
                           _3Query=_3Query, _3QueryRows=_3QueryRows,
                           _4Query=_4Query,
                           _5Query=_5Query, _5QueryRows=_5QueryRows,
                           _6Query=_6Query,
                           _7Query=_7Query,
                           _8Query=_8Query, _8QueryRows=_8QueryRows,
                           _9Query=_9Query, _9QueryRows=_9QueryRows,
                           _10Query=_10Query, _10QueryRows=_10QueryRows,
                           _11Query=_11Query,
                           _12Query=_12Query,
                           _13Query=_13Query, _13QueryRows=_13QueryRows,
                           _14Query=_14Query, _14QueryRows=_14QueryRows,
                           _15Query=_15Query,
                           _16Query=_16Query, _16QueryRows=_16QueryRows,
                           _17Query=_17Query, _17QueryRows=_17QueryRows,
                           _18Query=_18Query, _18QueryRows=_18QueryRows,
                           _19Query=_19Query,
                           _20Query=_20Query, _20QueryRows=_20QueryRows,
                           _21Query=_21Query, _21QueryRows=_21QueryRows,
                           _22Query=_22Query,
                           _23Query=_23Query, _23QueryRows=_23QueryRows,
                           _24Query=_24Query,
                           _25Query=_25Query,
                           _26Query=_26Query, _26QueryRows=_26QueryRows)


@blueprint.route('/1Query', methods=['get'])
@roles_required('Manager')
def admin_1Query():
    tablename = '?????????????? ???????????? ??????????????????????, ???? ???????????????? ???????????? ????????????, ?????????????????????????? ???? ??????????????????'
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
    category_name = request.form['2QuerySelect']
    tablename = '?????????????? ???????????? ??????????????, ???? ???????????????? ???????????? ??????????????????, ?????????????????????????? ???? ????????????'
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
    surname = request.form['3QuerySelect']
    tablename = '???? ?????????????????? ???????????????????? ???????????? ???????? ?????????????? ???? ????????????'
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
    tablename = '?????????????? ???????????? ???????? ????????????????????, ???? ???????????????????? ???????????? ???? ????????????????'
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
    name = request.form['5QuerySelect']
    tablename = '???? ???????????? ?????????????????? ?????????????? ???????? ???????????????????? ?????????????? ???? ????????????'
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
    tablename = '?????????????? ???????????? ???????? ??????????????, ?????????????????????????? ???? ????????????'
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
    tablename = '?????????????? ???????????? ???????? ??????????????????, ?????????????????????????? ???? ????????????'
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
    category_name = request.form['8QuerySelect']
    tablename = '?????????????? ???????????? ???????? ??????????????, ???? ???????????????? ???????????? ??????????????????'
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
    product_id = request.form['9QuerySelect']
    tablename = '?????????????? ???????????? ?????????????? ?? ????????????????, ???? ???????????????? ?????????????? ????????????'
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
    upc = request.form['10QuerySelect']
    tablename = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????'
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
    if request.form['11QuerySelect1'] == '?????????????????? ??????????????':
        order_by = 'PRODUCTS_NUMBER'
    else:
        order_by = 'UPC'
    if request.form['11QuerySelect2'] == 'ASC':
        sortType = 'ASC'
    else:
        sortType = 'DESC'

    tablename = '?????????????? ???????????? ???????? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
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
    if request.form['12QuerySelect1'] == '?????????????????? ??????????????':
        order_by = 'PRODUCTS_NUMBER'
    else:
        order_by = 'UPC'
    if request.form['12QuerySelect2'] == 'ASC':
        sortType = 'ASC'
    else:
        sortType = 'DESC'
    tablename = '?????????????? ???????????? ???????? ???? ???????????????? ??????????????, ?????????????????????????? ???? ?????????????????? ?????????????? ????????????/ ???? ????????????'
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
    product_id = request.form['13QuerySelect']
    date_from = request.form['13QueryName1']
    date_to = request.form['13QueryName2']
    tablename = '?????????????? ???????????? ???????? ?????????????????? ???? ???????????? ??????????, ???????????????????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        toExec = "SELECT * FROM CONSIGNMENT WHERE UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT='{}') AND SIGNATURE_DATE BETWEEN '{}' AND '{}'".format(
            product_id, date_from, date_to)
        print(toExec)
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


@blueprint.route('/14Query', methods=['get', 'post'])
@roles_required('Manager')
def admin_14Query():
    producer_id = request.form['14QuerySelect']
    date_from = request.form['14QueryName1']
    date_to = request.form['14QueryName2']
    tablename = '?????????????? ???????????? ???????? ??????????????????, ???????????????????? ???????????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CONSIGNMENT WHERE ID_PRODUCER='{}' AND SIGNATURE_DATE BETWEEN '{}' AND '{}' ".format(
            producer_id, date_from, date_to))
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
    tablename = '?????????????? ???????????? ???????? ??????????????????, ???????????????????? ????????-???????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CONSIGNMENT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}'".format(date_from, date_to))
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
    product_id = request.form['16QuerySelect']
    date_from = request.form['16QueryName1']
    date_to = request.form['16QueryName2']
    tablename = '?????????????????? ???????????????? ?????????????????? ???????????????????? ?????????????? ?????????????? ???????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCTS_NUMBER) AS QUANTITY FROM CONSIGNMENT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}'  AND UPC IN(SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT='{}') ".format(
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
    product_id = request.form['17QuerySelect']
    date_from = request.form['17QueryName1']
    date_to = request.form['17QueryName2']
    tablename = '?????????????? ???????????? ???????? ?????????????????? ???????????????????? ???? ???????????? ??????????, ???????????????????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}' AND UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT='{}')".format(
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
    producer_id = request.form['18QuerySelect']
    date_from = request.form['18QueryName1']
    date_to = request.form['18QueryName2']
    tablename = '?????????????? ???????????? ???????? ?????????????????? ????????????????????, ???????????????????? ???????????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}' AND ID_PRODUCER='{}'".format(
                date_from,
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
    tablename = '?????????????? ???????????? ???????? ?????????????????? ????????????????????, ???????????????????? ????????-???????? ???????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}'".format(date_from, date_to))
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
    product_id = request.form['20QuerySelect']
    date_from = request.form['20QueryName1']
    date_to = request.form['20QueryName2']
    tablename = '?????????????????? ???????????????? ?????????????????? ???????????????????? ?????????????? ?????????????? ???????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCT_NUMBER) AS QUANTITY FROM RETURN_CONTRACT WHERE SIGNATURE_DATE BETWEEN '{}' AND '{}' AND UPC IN (SELECT UPC FROM STORE_PRODUCT WHERE ID_PRODUCT='{}')".format(
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
    cashier_id = request.form['21QuerySelect']
    date_from = request.form['21QueryName1']
    date_to = request.form['21QueryName2']
    tablename = '?????????????? ???????????? ??????????, ???????????????????????? ???????????? ?????????????? ???? ???????????? ???????????? ???????? (?? ???????????????????? ?????????????????? ???????????????? ??????????????, ???? ??-?????? ???? ????????)'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, SALE.UPC, PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN '{}' AND '{}'  AND ID_EMPLOYEE='{}'".format(
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
    tablename = '?????????????? ???????????? ??????????, ???????????????????????? ?????????? ???????????????? ???? ???????????? ???????????? ???????? (?? ???????????????????? ?????????????????? ???????????????? ??????????????, ???? ??-?????? ???? ????????)'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT CHEQUE.CHECK_NUMBER, ID_EMPLOYEE, CARD_NUMBER, PRINT_DATE, SUM_TOTAL, VAT, SALE.UPC, PRODUCT_NUMBER, SALE.SELLING_PRICE, PRODUCT_NAME FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN '{}' AND '{}'".format(
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
    product_id = request.form['23QuerySelect']
    date_from = request.form['23QueryName1']
    date_to = request.form['23QueryName2']
    tablename = '?????????????????? ???????????????? ?????????????????? ?????????????? ?????????????? ????????????, ?????????????????? ???? ???????????? ???????????? ????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT SUM(PRODUCT_NUMBER) AS QUANTITY FROM CHEQUE INNER JOIN SALE ON CHEQUE.CHECK_NUMBER=SALE.CHECK_NUMBER INNER JOIN STORE_PRODUCT ON SALE.UPC=STORE_PRODUCT.UPC INNER JOIN PRODUCT ON STORE_PRODUCT.ID_PRODUCT=PRODUCT.ID_PRODUCT WHERE PRINT_DATE BETWEEN '{}' AND '{}' AND PRODUCT.ID_PRODUCT='{}'".format(
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
    tablename = '?????????????? ???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ??????????????, ???? ?????????? ??????, ??????????????, ???????????? (???????? ??????????????)'
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
    tablename = '?????????????? ???????????? ???????? ?????????????????? ????????????????, ???? ?????????? ?????????? ?????????????? ???? ???????????? ??????????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT * FROM CUSTOMER_CARD WHERE PERCENT='{}'".format(percent))
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
    upc = request.form['26QuerySelect']
    tablename = '???? UPC-???????????? ???????????? ???????? ?????????????? ????????????, ?????????????????? ?????????????? ?????????????? ????????????, ?????????? ???? ???????????????????????????? ????????????'
    try:
        con = sql.connect('dbs/zlagoda.db')
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(
            "SELECT STORE_PRODUCT.UPC, STORE_PRODUCT.ID_PRODUCT, SELLING_PRICE, PRODUCTS_NUMBER, PRODUCT_NAME, CHARACTERISTICS FROM STORE_PRODUCT INNER JOIN PRODUCT ON PRODUCT.ID_PRODUCT=STORE_PRODUCT.ID_PRODUCT WHERE UPC=?",
            (upc,))
        names = [description[0] for description in cur.description]
        rows = cur.fetchall()
        cur.close()
    except sql.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (con):
            con.close()
    return render_template("list.html", rows=rows, tablename=tablename, titles=names)
