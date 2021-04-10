from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email

class CategoryForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired()])
    submit = SubmitField("Submit")
