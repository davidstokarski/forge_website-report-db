"""

TODO:
    - 

"""

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_from_directory, send_file, make_response, current_app
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from apps.forms import *
from apps.progs import *
from apps.send_email import send_email
from apps.models import Scrape, TwitterScrape
from apps import db, task_executor
import asyncio
from apps.functions.twitter import twitter_function

views = Blueprint('twitter', __name__)
views_twitter = views

# send email


def send_scrape_email(scrape):
    print("beep boop sending email to ", scrape.email)
    # send_email(scrape.email,"YOUR SCRAPE WORKED","THIS IS THE TEXT PART","","THIS IS THE CUSTOM ID") #turn back on if u want to send email


'''     TWITTER SCRAPER FUNCTIONS     '''
# twitter scraper function


def twitter_scraper_task(app, email, keywords_list, limit, create_date):
    try:
        with app.app_context():
            new_scrape = TwitterScrape(email, str(
                keywords_list), limit, create_date, in_progress=True)
            db.session.add(new_scrape)
            db.session.commit()
            print("In progress: ", TwitterScrape.query.filter_by(
                id=new_scrape.id).first().in_progress)
            # this is bad because there has to be a loading page # turn on to scrape
            df = asyncio.run(twitter_function(keywords_list, limit, True))
            csv = df.to_csv()
            # save to datavase
            new_scrape.file = csv
            send_scrape_email(new_scrape)
            new_scrape.in_progress = False
            db.session.commit()
            print("In progress: ", TwitterScrape.query.filter_by(
                id=new_scrape.id).first().in_progress)
    except Exception as e:
        print("Got scraping exception:", e)

# twitter scraper


@views.route('/twitter-scraper', methods=['GET', 'POST'])
@login_required
async def twitter_scraper():
    twitter_form = TwitterForm(request.form)
    if request.method == 'POST':
        email = request.form.get('email')
        keywords = request.form.get('keywords')
        limit = request.form.get('limit')
        temp = keywords.split(',')
        keywords_list = []
        for item in temp:
            keywords_list.append(item.strip())
        create_date = datetime.today()
        app = current_app._get_current_object()
        task_executor.submit(twitter_scraper_task, app,
                             email, keywords_list, limit, create_date)
        print("Running scrape for: ", email, keywords_list)
        return redirect(url_for('views.twitter.twitter_scraper_jobs', email=email))
    return render_template('home/twitter-scraper.html', form=twitter_form, email=current_user.email)

# previous twitter files


@views.route('/twitter-scraper-jobs/<email>')
@login_required
def twitter_scraper_jobs(email):
    all_jobs = TwitterScrape.query.filter_by(email=email).all()
    print(all_jobs)
    return render_template('temp/twitter_scraper_jobs.html', all_jobs=all_jobs, email=email)

# twitter scraper success


@views.route('/twitter-scraper-success/<id>')
@login_required
def twitter_scraper_success(id):
    scrape = Scrape.query.filter_by(id=id).first()
    return render_template('temp/twitter_scraper_success.html', id=id, scrape=scrape)

# download twitter file


@views.route('/download-twitter-scrape/<id>')
@login_required
def download_twitter_scrape(id):
    file = TwitterScrape.query.filter_by(id=id).first()
    response = make_response(file.file)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachement'
    response.headers['Content-Disposition'] = f'attachement; filename="forge_twitter_scrape_{file.id}.csv"'
    return response
