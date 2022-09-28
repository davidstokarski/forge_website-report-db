# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,EmailField 
from wtforms.validators import Email, DataRequired, Length

# login and registration


class LoginForm(FlaskForm):
    email = StringField('Email',
                            id='email',
                            validators=[DataRequired()]) 
    password = PasswordField('Password',
                            id='password',
                            validators=[DataRequired()])


class CreateAccountForm(FlaskForm):
    username = StringField('Username',
                            id='username',
                            validators=[DataRequired()])
    email = EmailField('Email',
                            id='email',
                            validators=[DataRequired(), Email()])
    password = PasswordField('Password',
                            id='password',
                            validators=[DataRequired(), Length(min=8, message="Please select a memorable password 8 characters or longer")])
    confirm_password = PasswordField('Password',
                            id='confirm_password',
                            validators=[DataRequired()])
