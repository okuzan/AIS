from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, validators
from wtforms.validators import DataRequired, Email


class CategoryForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired()])
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
                                                        validators.Regexp(r'(^\d{5}$)|(^\d{9}$)|(^\d{5}-\d{4}$)',
                                                                          message="Incorrect zip code format, it can be xxxxx or xxxxxxxxx or xxxxx-xxxx (only numbers allowed)")])

    phone_number = StringField("Phone: ", validators=[DataRequired(message="This field can not be empty"),
                                                        validators.Regexp(r'^\+\d{12}$',
                                                                          message="Incorrect phone format +xxxxxxxxxxxx")])

    submit = SubmitField("Submit")
