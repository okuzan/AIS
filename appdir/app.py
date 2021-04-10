from appdir import app, db
from appdir.models import User, Role, UserRoles
from flask_user import UserManager, UserMixin


# Start development web server
if __name__ == '__main__':

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)
    app.run(host='localhost', port=3000, debug=True)
