import sys
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_restful import Api
from flask_wtf import CSRFProtect
from dashboard.config import Config

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdin))

# db
db = SQLAlchemy()
migrate = Migrate()

# login manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

# email
mail = Mail()

# api
api = Api()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # init db
    db.init_app(app)
    migrate.init_app(app, db)

    # login manager
    login_manager.init_app(app)
    login_manager.login_message_category = 'warning'

    # csrf
    CSRFProtect().init_app(app)

    # mail
    mail.init_app(app)

    from dashboard.url_converters import DateConverter
    app.url_map.converters['date'] = DateConverter

    # api/blueprints
    from dashboard.rest.routes import api_blueprint
    api.init_app(api_blueprint)
    app.register_blueprint(api_blueprint)

    from dashboard.users.routes import users_blueprint
    app.register_blueprint(users_blueprint, url_prefix='/users')

    from dashboard.dashboard.routes import dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)

    from dashboard.popups.routes import popups_blueprint
    app.register_blueprint(popups_blueprint, url_prefix='/popups')

    app.app_context().push()
    db.create_all()

    # template filters
    import dashboard.template_filters

    return app
