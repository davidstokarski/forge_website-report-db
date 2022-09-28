"""

TODO:
    - 

"""

from apps.views.twitter import views_twitter
from apps.views.scraper import views_scraper
from apps.views.portal import views_portal
from apps.views.auth import views_auth
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_from_directory, send_file, make_response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import calendar
from apps.forms import *
from apps.progs import *
from apps.models import Scrape, TwitterScrape, User
import os
import json
import asyncio

views = Blueprint('views', __name__)

'''     HOME ROUTE     '''
# home routing
@views.route('/')
# @login_required # actually, this can be handled in the html file
def home():
    # if user is logged in
    if current_user.is_authenticated:
        # gets total scrapes
        total_length = len(Scrape.query.all())+len(TwitterScrape.query.all())
        date = datetime.today()
        # gets today and previous week
        dates = []
        for x in range(0, 7):
            day = date-timedelta(days=x)
            dates.append(day)
        # creates list for all web scrapes
        week_total = 0
        raw_web = Scrape.query.filter_by(email=current_user.email)
        web_scrapes = []
        for x in raw_web:
            web_scrapes.append(x.create_date.strftime("%Y-%m-%d"))
        # creates list for all twitter scrapes
        raw_twitter = TwitterScrape.query.filter_by(email=current_user.email)
        twitter_scrapes = []
        for y in raw_twitter:
            twitter_scrapes.append(y.create_date.strftime("%Y-%m-%d"))
        # finds scrapes per day
        num_dict = {}
        num_files = []
        for date in dates:
            num = web_scrapes.count(date.strftime(
                "%Y-%m-%d"))+twitter_scrapes.count(date.strftime("%Y-%m-%d"))
            num_dict[date] = num
            num_files.append(num)
            week_total += num
        # filters dates to be weekday names
        filtered_dates = []
        for x in list(dict(reversed(list(num_dict.items()))).keys()):
            filtered_dates.append(calendar.day_name[x.weekday()][0])
        num_files.reverse()
        num_dates = filtered_dates
        # get months starting at current month
        months=[]
        months_nums=[]
        for x in range(0,12):
            txt=date-relativedelta(months=x)
            months.append(calendar.month_name[txt.date().month][0:3])
            months_nums.append(txt.date().month)
        months.reverse()
        months_nums.reverse()
        # filters lists of web and twitter to only include month
        web_scrapes_month=[]
        for item in web_scrapes:
            if item.split('-')[0]==str(date.strftime('%Y')):
                txt=item.split('-')[1].split('0')[1]
                web_scrapes_month.append(txt)
        twitter_scrapes_month=[]
        for item in twitter_scrapes:
            if item.split('-')[0]==str(date.strftime('%Y')):
                txt=item.split('-')[1].split('0')[1]
                twitter_scrapes_month.append(txt)
        # gets amount of reports generated per month
        web_month_data=[]
        twitter_month_data=[]
        for month in months_nums:
            web_month_data.append(web_scrapes_month.count(str(month)))
            twitter_month_data.append(twitter_scrapes_month.count(str(month)))
        package={"months": months, "web_month_data": web_month_data, "twitter_month_data": twitter_month_data, "num_dates": num_dates, "num_files": num_files, "total_length": total_length, "week_total": week_total}
        return render_template('home/index.html', current_user=current_user, package=package)
    # if user is not logged in
    else:
        # gets total scrapes
        total_length = len(Scrape.query.all())+len(TwitterScrape.query.all())
        date = datetime.today()
        # gets today and previous week
        dates = []
        for x in range(0, 7):
            day = date-timedelta(days=x)
            dates.append(day)
        # creates list for all web scrapes
        week_total = 0
        raw_web = Scrape.query.filter_by()
        web_scrapes = []
        for x in raw_web:
            web_scrapes.append(x.create_date.strftime("%Y-%m-%d"))
        # creates list for all twitter scrapes
        raw_twitter = TwitterScrape.query.filter_by()
        twitter_scrapes = []
        for y in raw_twitter:
            twitter_scrapes.append(y.create_date.strftime("%Y-%m-%d"))
        # finds scrapes per day
        num_dict = {}
        num_files = []
        for date in dates:
            num = web_scrapes.count(date.strftime(
                "%Y-%m-%d"))+twitter_scrapes.count(date.strftime("%Y-%m-%d"))
            num_dict[date] = num
            num_files.append(num)
            week_total += num
        # filters dates to be weekday names
        filtered_dates = []
        for x in list(dict(reversed(list(num_dict.items()))).keys()):
            filtered_dates.append(calendar.day_name[x.weekday()][0])
        num_files.reverse()
        num_dates = filtered_dates
        print(num_dates)
        package = {"num_dates": num_dates, "num_files": num_files,
                   "total_length": total_length, "week_total": week_total}
        print(package)
        return render_template('home/index2.html', current_user=current_user, package=package)

'''     UNAUTHED USER     '''
# about us
@views.route('/about-us')
def about_us():
    return render_template('services/about_us.html')

# functions
@views.route('/functions')
def functions():
    return render_template('services/functions.html')

# projects
@views.route('/projects')
def projects():
    return render_template('services/projects.html')

'''     AUTH FUNCTIONS     '''
views.register_blueprint(views_auth)

'''     WEB SCRAPER FUNCTIONS     '''
views.register_blueprint(views_scraper)

'''     TWITTER SCRAPER FUNCTIONS     '''
views.register_blueprint(views_twitter)

'''     PORTAL FUNCTIONS     '''
views.register_blueprint(views_portal)

'''     ROUTING FOR SPECIAL PROJECTS     '''
@views.route('/bsa')
@login_required
def southcom():
    return render_template('special-projects/bsa/home.html')


@views.route('/ssb')
@login_required
def ssb():
    return render_template('special-projects/ssb/home.html')


@views.route('/vanguard')
@login_required
def vanguard():
    return render_template('special-projects/vangaurd/home.html')


@views.route('/archived-reports')
@login_required
def archived_reports():
    return render_template('special-projects/archived-reports.html')


'''     MISC FUNCS     '''
# upload a file to be processed


@views.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    ALLOWED_FILES = ['csv']
    if request.method == 'POST':
        file = request.files['upload_csv']
        if file and allowed_file(file.filename, ALLOWED_FILES):
            filename = secure_filename(file.filename)
            new_filename = f'{filename.split(".")[0]}_{str(datetime.now())}.csv'
            save_location = os.path.join('apps', 'input', new_filename)
            file.save(save_location)
            map = process_csv(save_location)
        return redirect(url_for('views.SSB_map'))
    return render_template('home/upload.html', current_user=current_user)

# send email


def send_scrape_email(scrape):
    print("beep boop sending email to ", scrape.email)
    # send_email(scrape.email,"YOUR SCRAPE WORKED","THIS IS THE TEXT PART","","THIS IS THE CUSTOM ID") #turn back on if u want to send email

# temp routing for heatmap


@views.route('/SSB_map')
@login_required
def SSB_map():
    return render_template('temp/heatmap.html')

# temp routing for cluster map


@views.route('/ClusterMapTestSSB')
@login_required
def ClusterMapTestSSB():
    return render_template('temp/ClusterMapTestSSB.html')

# makes sure page has ending .html


@views.route('/<template>')
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        # Detect the current page
        segment = get_segment(request)
        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("info/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('info/page-404.html'), 404

    except:
        return render_template('info/page-500.html'), 500

# Helper - Extract current page name from request


def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
