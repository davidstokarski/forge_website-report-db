"""

TODO:
    - 

"""

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_from_directory, send_file, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound
from datetime import datetime, timedelta
import calendar
from sqlalchemy import func
from apps.forms import *
from apps.progs import *
from apps.functions.scraper import scraper_function
from apps import db, task_executor
from apps.models import Scrape, TwitterScrape, User, Report, Message
import os
import json
import asyncio

from apps.utils.perms import IS_ADMIN

views = Blueprint('messages', __name__)
views_messages = views

'''     MESSAGES     '''
# messages home
@views.route('/message/<receive_user>', methods=['GET','POST'])
@login_required
def home(receive_user):
    # establishes select_user var
    receive_user=receive_user

    # gets all usernames
    all_users=User.query.all()
    usernames=[]
    texts_list=[]
    package={}
    for user in all_users:
        if user.username not in usernames: # and user.username != current_user.username:
            usernames.append(user.username)

    # form submit
    if request.method == 'POST':
        package['receive_user']=receive_user
        text=request.form['text']
        if receive_user!='select user' and text!='':
            send_time=datetime.today()
            new_message=Message(receive_user,current_user.username,text,send_time)
            db.session.add(new_message)
            db.session.commit()

    # gets all relevant messages
    texts_raw=Message.query.all()
    texts_list=[]
    for item in texts_raw:
        dict={'send_time':item.send_time,'send_user':item.send_user,'receive_user':item.receive_user,'text':item.text}
        if (dict['send_user']==current_user.username and dict['receive_user']==receive_user) or (dict['send_user']==receive_user and dict['receive_user']==current_user.username):
            texts_list.append(dict)
    texts_list.reverse()
    
    package={
        'users': usernames,
        'receive_user': receive_user,
        'texts': texts_list,
        'user': current_user.username
        }
    
    return render_template('messages/home.html', package=package)