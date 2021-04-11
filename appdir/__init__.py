""" Flask application factory """

from flask import Flask
from flask_bootstrap import Bootstrap

from config import Config
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy


# Create Flask app load app.config
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Flask-BabelEx
babel = Babel(app)

# Initialize Flask-SQLAlchemy
db = SQLAlchemy(app)
Bootstrap(app)
# Setup Flask-User and specify the User data-model
# user_manager = UserManager(app, db, User)

# Create all database tables
# db.create_all()

from routes import blueprint
app.register_blueprint(blueprint)
app.config['WTF_CSRF_ENABLED'] = False
