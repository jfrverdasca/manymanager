from os import getenv


class Config:
    FLASK_DEBUG = getenv('FLASK_DEBUG')
    SECRET_KEY = getenv('SECRET_KEY')

    # database configurations
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URL')

    # email configurations
    MAIL_SERVER = getenv('MAIL_SERVER')
    MAIL_PORT = getenv('MAIL_PORT')
    MAIL_USE_TLS = getenv('MAIL_USE_TLS')
    MAIL_USERNAME = getenv('MAIL_USERNAME')
    MAIL_PASSWORD = getenv('MAIL_PASSWORD')

    # custom configurations
    PASSWORD_TOKEN_EXPIRATION_SECONDS = 1800  # 30 minutes
    SHARE_TOKEN_EXPIRATION_SECONDS = 172800  # 24 hours
    DATETIME_FORMAT = getenv('DATETIME_FORMAT', '%d-%m-%Y %H:%M:%S')
