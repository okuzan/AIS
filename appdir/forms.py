from flask_admin.form import DatePickerWidget
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, validators, PasswordField, SelectField
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import DateField


class CategoryForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired(message="This field can not be empty")])
    submit = SubmitField("Submit")


class ProducerForm(FlaskForm):
    contract_number = StringField("Contract number: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=15, message="Contract number can not contain more than 15 symbols")])
    name = StringField("Name: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50, message="Producer name can not contain more than 50 symbols")])
    country = StringField("Country: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50, message="Producer name can not contain more than 50 symbols")])
    city = StringField("City: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50, message="Producer name can not contain more than 50 symbols")])
    street = StringField("Street: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50, message="Producer name can not contain more than 50 symbols")])
    zip_code = StringField("Zip code: ", validators=[DataRequired(message="This field can not be empty"),
                                                        validators.Regexp(r'(^\d{5}$)|(^\d{9}$)',
                                                                          message="Incorrect zip code format, it can be xxxxx or xxxxxxxxx (only numbers allowed)")])

    phone_number = StringField("Phone: ", validators=[DataRequired(message="This field can not be empty"),
                                                        validators.Regexp(r'^\+\d{12}$',
                                                                          message="Incorrect phone format +xxxxxxxxxxxx")])

    submit = SubmitField("Submit")

class EmployeeForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Employee name can not contain more than 50 symbols")])
    surname = StringField("Surname: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Employee surname can not contain more than 50 symbols")])
    patronymic = StringField("Patronymic: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Employee patronymic can not contain more than 50 symbols")])
    password = PasswordField("Password: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Password can not contain more than 50 symbols")])

    role = SelectField('Role', choices=[('M', 'manager'), ('C', 'cashier')])

    salary = StringField("Salary: ", validators=[DataRequired(message="This field can not be empty"),
                                                     validators.Regexp(r'(^\d+\.?\d+$)',
                                                                           message="Incorrect salary format")])

    date_of_birth = DateField('Date Of Birth', format='%Y-%m-%d',
                              validators=[DataRequired("This field can not be empty")])

    date_of_start = DateField('Date Of Start', format='%Y-%m-%d',
                              validators=[DataRequired("This field can not be empty")])

    city = StringField("City: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50,
                                                               message="Producer name can not contain more than 50 symbols")])
    street = StringField("Street: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Producer name can not contain more than 50 symbols")])
    zip_code = StringField("Zip code: ", validators=[DataRequired(message="This field can not be empty"),
                                                     validators.Regexp(r'(^\d{5}$)|(^\d{9}$)',
                                                                       message="Incorrect zip code format, it can be xxxxx or xxxxxxxxx (only numbers allowed)")])

    phone_number = StringField("Phone: ", validators=[DataRequired(message="This field can not be empty"),
                                                      validators.Regexp(r'^\+\d{12}$',
                                                                        message="Incorrect phone format +xxxxxxxxxxxx")])

    submit = SubmitField("Submit")


class CustomerForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired(message="This field can not be empty"),
                                             validators.Length(max=50,
                                                               message="Employee name can not contain more than 50 symbols")])
    surname = StringField("Surname: ", validators=[DataRequired(message="This field can not be empty"),
                                                   validators.Length(max=50,
                                                                     message="Employee surname can not contain more than 50 symbols")])
    patronymic = StringField("Patronymic: ", validators=[DataRequired(message="This field can not be empty"),
                                                         validators.Length(max=50,
                                                                           message="Employee patronymic can not contain more than 50 symbols")])

    city = StringField("City: ", validators=[DataRequired(message="This field can not be empty"),
                                                 validators.Length(max=50,
                                                                   message="Producer name can not contain more than 50 symbols")])
    street = StringField("Street: ", validators=[DataRequired(message="This field can not be empty"),
                                                     validators.Length(max=50,
                                                                       message="Producer name can not contain more than 50 symbols")])
    zip_code = StringField("Zip code: ", validators=[DataRequired(message="This field can not be empty"),
                                                         validators.Regexp(r'(^\d{5}$)|(^\d{9}$)',
                                                                           message="Incorrect zip code format, it can be xxxxx or xxxxxxxxx (only numbers allowed)")])

    phone_number = StringField("Phone: ", validators=[DataRequired(message="This field can not be empty"),
                                                      validators.Regexp(r'^\+\d{12}$',
                                                                        message="Incorrect phone format +xxxxxxxxxxxx")])
    percent = StringField("Percent: ", validators=[DataRequired(message="This field can not be empty"),
                                                   validators.Regexp(r'^\d{1,2}$')])

    submit = SubmitField("Submit")


class ProductForm(FlaskForm):
    category_number = SelectField(u'Category number', coerce=int, validators=[DataRequired()])
    product_name = StringField("Product name: ", validators=[DataRequired(message="This field can not be empty"),
                                                             validators.Length(max=50,
                                                                               message="Product name can not contain more than 50 symbols")])

    characteristics = StringField("Characteristics: ", validators=[DataRequired(message="This field can not be empty"),
                                                                   validators.Length(max=100,
                                                                                     message="Producer name can not contain more than 100 symbols")])

    submit = SubmitField("Submit")
