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
# from apps.forms import *
from apps.progs import *
from apps.functions.scraper import scraper_function
from apps import db, task_executor
from apps.models import Scrape, TwitterScrape, User, Report
import os
import json
import asyncio
import pandas as pd

from apps.utils.perms import IS_ADMIN

views = Blueprint('portal', __name__)
views_portal = views

'''     PORTAL     '''
# portal home
@views.route('/si-portal')
@login_required
def home():
    return render_template('portal/index.html')

# analyst
@views.route('/si-portal/analyst',methods=['GET','POST'])
@login_required
def analyst():
    reports = Report.query.filter_by(user_id=current_user.id).all()
    print(reports)
    return render_template('portal/analyst.html', reports=reports)

@views.route('/si-portal/bulk-upload-wizard',methods=['GET','POST'])
@login_required
def bulk_upload_wizard():
    return render_template('portal/bulk-upload.html')

@views.route('/si-portal/edit-report/<id>',methods=['GET','POST'])
@login_required
def edit_report(id):
    if id == "new":
        report = {}
    else: 
        report = Report.query.filter_by(id = id).first()
        if not report:
            os.abort(404)
        report = report.as_dict()
        report = {
            "status": report["status"].value,
            "article_source": report["article_source"],
            "article_title": report["article_title"],
            "article_text": report["article_text"],
            "attributes": report["attributes"],
            "category": report["category"],
            "city": report["city"],
            "incident_date": report["incident_date"],
            "location": report["location"],
            "project": report["project"],
            "sub_category": report["sub_category"],
            "summary_text": report["summary_text"],
            "summary_title": report["summary_title"]
        }
        
    if request.method=='POST':
        analyst_form = Report(request.form)
        print(analyst_form.article_text)

    print(report)
    try:
        print(json.dumps(report))
    except Exception as e:
        print(e)    
    return render_template('portal/edit-report.html', report=report)

# reviewer
@views.route('/si-portal/reviewer',methods=['GET','POST'])
@login_required
def reviewer():
    return render_template('portal/reviewer.html')

# publisher
@views.route('/si-portal/publisher',methods=['GET','POST'])
@login_required
def publisher():
    return render_template('portal/publisher.html')

@views.route('/si-portal/publication/bulk-upload', methods=['POST'])
@login_required
def bulk_upload():
    # if current_user.has_permissions([IS_ADMIN])
    # current_reviewer = 
    # next_reviewer
    
    # article_source = request.form['article_source']
    # article_title = request.form['article_title']
    # article_text = request.form['article_text']
    # attributes = request.form['attributes']
    # category = request.form['category']
    # city = request.form['city']
    # incident_date = request.form['incident_date']
    # location = request.form['location']
    # project = request.form['project']
    # sub_category = request.form['sub_category']
    df = pd.read_csv(request.files['upload_csv'], encoding="utf-8")
    user = User.query.filter_by(id=current_user.id).first()
    for index, row in df.iterrows():
        kwargs = dict(row)
        new_report = Report(user=user, **kwargs)
        db.session.add(new_report)
    
    db.session.commit()
    return jsonify(request.form)
    pass

@views.route('/si-portal/publication/create', methods=['POST'])
@login_required
def publish_create():
    # if current_user.has_permissions([IS_ADMIN])
    # current_reviewer = 
    # next_reviewer
    
    # article_source = request.form['article_source']
    # article_title = request.form['article_title']
    # article_text = request.form['article_text']
    # attributes = request.form['attributes']
    # category = request.form['category']
    # city = request.form['city']
    # incident_date = request.form['incident_date']
    # location = request.form['location']
    # project = request.form['project']
    # sub_category = request.form['sub_category']
    params = dict(request.form)
    print(params)


    # article_source=article_source, article_title=article_title, article_text=article_text, attributes=attributes, category=category, city=city, incident_date=incident_date, location=location, project=project, sub_category=sub_category
    # if current_user.reviewer is None:
    #     # print(current_user.reviewer)
    #     # reviewer = Reviewer(current_user, role=current_user.reviewer.role)
    #     # db.session.add(reviewer)
    #     print("Current user be no reviewer")
    # else:
    #     reviewer = current_user.reviewer

    # print(reviewer)
    # TOOD: make this work for non-new reports
    
    db.session.commit()
    return jsonify(request.form)
    pass