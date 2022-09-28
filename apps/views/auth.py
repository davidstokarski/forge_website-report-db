from re import L
from flask import Blueprint, render_template, request, flash, redirect, url_for
from apps.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from apps import db, superadmin_emails
from apps.models import Scrape, Role
from apps.authentication import SessionUser
from apps.authentication.forms import LoginForm, CreateAccountForm
from flask_login import login_user, login_required, logout_user, current_user, UserMixin
from sqlalchemy.orm.exc import UnmappedClassError, UnmappedInstanceError

auth = Blueprint('auth', __name__)
views_auth = auth


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        return
    return render_template("accounts/profile.html", user=current_user, Scrape=Scrape)


@auth.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        return
    return render_template("accounts/edit-profile.html", user=current_user)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    print("CATCH ME", current_user)
    login_form = LoginForm(request.form)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter((User.email == email)
                                 | (User.username == email)).first()

        # Check the password and user
        if user and user.email != "":
            print(user.email, user.password)
            if check_password_hash(user.password, password) or user.password == password:
                session_user = SessionUser(user)
                session_user.id = user.id
                login_user(session_user, remember=True)
                return redirect(url_for('views.home'))
            else:
                return render_template('accounts/login.html',
                                       msg='Password incorrect',
                                       success=False,
                                       form=login_form)

    return render_template("accounts/login.html", user=current_user, form=login_form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    create_account_form = CreateAccountForm(request.form)
    if request.method == 'POST':
        if 'register' in request.form:

            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_passowrd = request.form.get('confirm_password')

            # Check email exists
            user = User.query.filter_by(email=email).first()
            if user:
                return render_template('accounts/register.html',
                                       msg='Email already registered',
                                       success=False,
                                       form=create_account_form)
            elif len(password) < 8:
                return render_template('accounts/register.html',
                                       msg='Password is less than 8 characters',
                                       success=False,
                                       form=create_account_form)
            elif password != confirm_passowrd:
                return render_template('accounts/register.html',
                                       msg="Passwords don't match",
                                       success=False,
                                       form=create_account_form)
            else:
                # TODO: Make this not hardcoded
                if email in superadmin_emails:
                    pass
                    # user.privilege = user.privilege | privilege
                    # user.privilege |= privilege -- but im making the role below. see there
                    # else we can create the user
                    role=Role.query.filter_by(name='Superadmin').first()
                else:
                    role = Role.query.filter_by(name="Default").first()
                new_user = User(email, username, generate_password_hash(
                    password, method='sha256'), role=role)
                
                # current_user=new_user
                session_user = SessionUser(new_user)
                session_user.id = new_user.id

                # current_user.record = new_user
                # current_user.is_authenticated = True
                db.session.add(new_user)
                db.session.commit()
                session_user = SessionUser(new_user)
                session_user.id = new_user.id
                login_user(session_user, remember=True)
                return redirect(url_for('views.home'))

            return redirect(url_for('views.home'))

        return render_template("accounts/register.html", user=current_user, form=create_account_form)
    return render_template("accounts/register.html", form=create_account_form)
