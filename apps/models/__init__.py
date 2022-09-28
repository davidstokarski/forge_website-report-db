from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, event, Boolean
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()
Base = db.make_declarative_base(db.Model)



# Base.metadata.create_all(engine)

from .auth import User 
from .scraper import Scrape
from .twitter import TwitterScrape
from .portal import Report, Role
from .messages import Message