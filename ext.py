from flask_sqlalchemy import SQLAlchemy
from flask_socketio import  SocketIO
from flask_login import LoginManager
db=SQLAlchemy()
login_manager=LoginManager()

socketio=SocketIO()