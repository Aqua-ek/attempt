from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


db = SQLAlchemy()
login_manager = LoginManager()

socketio = SocketIO()
