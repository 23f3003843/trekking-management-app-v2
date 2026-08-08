from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from flask_mail import Mail
from celery import Celery

#Application extensions
database = SQLAlchemy()
jwt_manager = JWTManager()
cors = CORS()
cache_manager = Cache()
mail_service = Mail()

celery_app = Celery(__name__)
