from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from flask_login import LoginManager
from concurrent.futures import ThreadPoolExecutor
from mailjet_rest import Client
from apps.authentication import SessionUser
from apps.models import db, Scrape, User, Role

DB_NAME = "database.db"
api_key = '899d506271c6c179692126a51c261c14'
api_secret = 'fd705cdfb7db8dfdd7763cd41f9cb966'
# turn back on if u want to send email
mailjet = Client(auth=(api_key, api_secret), version='v3.1')
task_executor = ThreadPoolExecutor(2)
superadmin_emails=["davidstokarski@gmail.com",'elijah@parentschooling.com']

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'qwerty'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from .views import views

    app.register_blueprint(views, url_prefix='/')

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'views.auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        print("LOADING USER", id)
        user = User.query.filter_by(id=id).first()
        if not user:
            return

        session_user = SessionUser(user)
        session_user.id = user.id
        return session_user

    @login_manager.request_loader
    def request_loader(request):
        id = request.form.get('id')
        user = User.query.filter_by(id=id).first()
        if not user:
            return
        session_user = SessionUser(user)
        session_user.id = user.id
        return session_user

    # Remove all dead jobs
    with app.app_context():
        # db.create_all()
        n_removed_jobs = db.session.query(Scrape).filter(
            Scrape.in_progress == True).delete()
        print(f"Removing {n_removed_jobs} dead jobs")
        db.session.commit()

    return app


def create_database(app):
    if not path.exists('apps/'+DB_NAME):
        with app.app_context():
            db.create_all(app=app)
    # @event.listens_for(Role.__table__, 'after_create')
    # def insert_initial_values(*args, **kwargs):
            db.session.add(Role(name='Bot', permissions=0b00000))
            db.session.add(Role(name='Default', permissions=0b00000))
            db.session.add(Role(name='Analyst', permissions=0b10000))
            db.session.add(Role(name='Reviewer', permissions=0b11000))
            db.session.add(Role(name='Editor', permissions=0b11100))
            db.session.add(Role(name='Publisher', permissions=0b11110))
            db.session.add(Role(name='Superadmin', permissions=0b11111))
            db.session.commit()
