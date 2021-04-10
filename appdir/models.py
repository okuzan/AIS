from flask_user.forms import RegisterForm
from wtforms import BooleanField, StringField

from appdir import app, db
from flask_user import UserManager, UserMixin
from datetime import datetime
from flask_user.signals import user_registered


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')


# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'), default=1)


# Setup Flask-User and specify the User data-model
class CustomRegisterForm(RegisterForm):
    role = StringField('Role')


class CustomeUserManager(UserManager):
    def __init__(self, app, db, UserClass, **kwargs):
        super().__init__(app, db, UserClass, **kwargs)
        self.RegisterFormClass = CustomRegisterForm

    def customize(self, app):
        pass


user_manager = CustomeUserManager(app, db, User)

# Create 'member@example.com' user with 'Cashier' role
if not User.query.filter(User.email == 'member@example.com').first():
    user = User(
        email='member@example.com',
        email_confirmed_at=datetime.datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    user.roles.append(Role(name='Cashier'))
    db.session.add(user)
    db.session.commit()

# Create 'admin@example.com' user with 'Manager'role
if not User.query.filter(User.email == 'admin@example.com').first():
    user = User(
        email='admin@example.com',
        email_confirmed_at=datetime.datetime.utcnow(),
        password=user_manager.hash_password('Password1'),
    )
    user.roles.append(Role(name='Manager'))
    db.session.add(user)
    db.session.commit()



@user_registered.connect_via(app)
def _after_user_registered_hook(sender, user, **extra):
    print(sender)
    role = Role.query.filter_by(name='Manager').one()
    user.roles.append(role)
    app.user_manager.db.session.commit()


# Create all database tables
db.create_all()
