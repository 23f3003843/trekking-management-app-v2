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

#Celery instance is created
import os
celery_app = Celery(
    __name__,
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)