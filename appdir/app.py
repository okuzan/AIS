# from appdir.models import db, User, Role, UserRoles

# db = SQLAlchemy()
from appdir import create_app


# Start development web server
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=3000, debug=True)
