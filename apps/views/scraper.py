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
from apps.models import Scrape, TwitterScrape, User
import os
import json
import asyncio

views = Blueprint('scraper', __name__)
views_scraper = views

# send email


def send_scrape_email(scrape):
    print("beep boop sending email to ", scrape.email)
    # send_email(scrape.email,"YOUR SCRAPE WORKED","THIS IS THE TEXT PART","","THIS IS THE CUSTOM ID") #turn back on if u want to send email


'''     WEB SCRAPER FUNCTIONS     '''
# web scraper funciton


def scraper_task(app, email, keywords_list, start_date, end_date, create_date):
    try:
        with app.app_context():
            new_scrape = Scrape(email, str(
                keywords_list), start_date, end_date, create_date, in_progress=True)
            db.session.add(new_scrape)
            db.session.commit()
            print("In progress: ", Scrape.query.filter_by(
                id=new_scrape.id).first().in_progress)
            # this is bad because there has to be a loading page # turn on to scrape
            df = asyncio.run(scraper_function(
                keywords_list, start_date, end_date))
            csv = df.to_csv()
            # save to datavase
            new_scrape.file = csv
            send_scrape_email(new_scrape)
            new_scrape.in_progress = False
            db.session.commit()
            print("In progress: ", Scrape.query.filter_by(
                id=new_scrape.id).first().in_progress)
    except Exception as e:
        print("Got scraping exception", e)

# web scraper home


@views.route('/scraper-home', methods=['GET', 'POST'])
@login_required
async def scraper_home():
    scraper_form = ScraperForm(request.form)
    if request.method == 'POST':
        email = request.form.get('email')
        keywords = request.form.get('keywords')
        start_date = datetime.strptime(
            request.form.get('start_date'), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get('end_date'), "%Y-%m-%d")
        print(start_date, end_date)
        temp = keywords.split(',')
        keywords_list = []
        for item in temp:
            keywords_list.append(item.strip())
        create_date = datetime.today()
        app = current_app._get_current_object()
        task_executor.submit(scraper_task, app, email,
                             keywords_list, start_date, end_date, create_date)
        print("Running scrape for: ", email, keywords_list)
        return redirect(url_for('views.scraper.scraper_jobs', email=email))
    week_back = datetime.today()-timedelta(days=7)
    start_date = week_back
    end_date = datetime.today()
    return render_template('home/scraper-home.html', form=scraper_form, start_date=start_date, end_date=end_date, email=current_user.email)

# previous web files


@views.route('/scraper-jobs/<email>')
@login_required
def scraper_jobs(email):
    all_jobs = Scrape.query.filter_by(email=email).all()
    print(all_jobs)
    return render_template('temp/scraper_jobs.html', all_jobs=all_jobs, email=email)

# web scraper success


@views.route('/scraper-success/<id>')
@login_required
def scraper_success(id):
    scrape = Scrape.query.filter_by(id=id).first()
    return render_template('temp/scraper_success.html', id=id, scrape=scrape)


@views.route('/download-scrape/<id>')
@login_required
def download_scrape(id):
    scrape = Scrape.query.filter_by(id=id).first()
    response = make_response(scrape.file)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachement; filename="forge_web_scrape_{scrape.id}.csv"'
    return response

# Send a POST request to either of these via form to get CSV or JSON *directly*
# You don't need to render a whole view unless that suits your tastes better
@views.route('/scrape-json', methods=['POST'])
@login_required
async def scrape_json():
    # email = request.form.get('email')
    keywords = [keyword.strip()
                for keyword in request.form.get('keywords').split(',')]
    df = await scraper_function(keywords)
    return jsonify(df)


@views.route('/scrape-csv', methods=['POST'])
@login_required
async def scrape_csv():
    # email = request.form.get('email')
    keywords = [keyword.strip()
                for keyword in request.form.get('keywords').split(',')]
    df = await scraper_function(keywords)
    download_name = f'scrape_results_{datetime.now().strftime("YYYY-MM-DD-HH-MM-SS")}.csv'
    return send_file(df.to_csv(), 'text/csv', False, download_name)
