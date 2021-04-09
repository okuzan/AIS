# from flask_sqlalchemy import SQLAlchemy
# from flask_user import UserManager, UserMixin
# from flask import render_template_string, Blueprint
#
# db = SQLAlchemy()
# blueprint2 = Blueprint('blueprint2', __name__)
#
#
# class User(db.Model, UserMixin):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
#
#     # User authentication information. The collation='NOCASE' is required
#     # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
#     email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
#     email_confirmed_at = db.Column(db.DateTime())
#     password = db.Column(db.String(255), nullable=False, server_default='')
#
#     # User information
#     first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
#     last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
#
#     # Define the relationship to Role via UserRoles
#     roles = db.relationship('Role', secondary='user_roles')
#
#
# # Define the Role data-model
# class Role(db.Model):
#     __tablename__ = 'roles'
#     id = db.Column(db.Integer(), primary_key=True)
#     name = db.Column(db.String(50), unique=True)
#
#
# # Define the UserRoles association table
# class UserRoles(db.Model):
#     __tablename__ = 'user_roles'
#     id = db.Column(db.Integer(), primary_key=True)
#     user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
#     role_id = db
