""" Flask application factory """

from flask import Flask
from config import Config
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from routes import blueprint


# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint)

# Initialize Flask-BabelEx
babel = Babel(app)

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)

# Create all database tables
db.create_all()


from appdir import routes, models

# # Create 'member@example.com' user with no roles
# if not User.query.filter(User.email == 'member@example.com').first():
#     user = User(
#         email='member@example.com',
#         email_confirmed_at=datetime.datetime.utcnow(),
#         password=user_manager.hash_password('Password1'),
#     )
#     user.roles.append(Role(name='Cashier'))
#     db.session.add(user)
#     db.session.commit()
#
# # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
# if not User.query.filter(User.email == 'admin@example.com').first():
#     user = User(
#         email='admin@example.com',
#         email_confirmed_at=datetime.datetime.utcnow(),
#         password=user_manager.hash_password('Password1'),
#     )
#     user.roles.append(Role(name='Manager'))
#     db.session.add(user)
#     db.session.commit()
