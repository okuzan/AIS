""" Flask application config """

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = 'you-will-never-guess-this-strong-password'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'cdutboryslav@gmail.com'
    MAIL_PASSWORD = 'cdut2020'
    MAIL_DEFAULT_SENDER = '"MyApp" <noreply@example.com>'

    # Flask-User settings
    USER_APP_NAME = "AIS"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True  # Enable email authentication
    USER_ENABLE_USERNAME = False  # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "cdutboryslav@gmail.com"

