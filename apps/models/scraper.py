from sqlalchemy import Column, String, Integer, DateTime, Boolean
from apps.models import db


class Scrape(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    file = Column(String(), nullable=True)
    search_terms = Column(String(100), nullable=False)
    start_date = Column(DateTime())
    end_date = Column(DateTime())
    create_date = Column(DateTime())
    in_progress = Column(Boolean(), default=True)

    def __init__(self, email, search_terms, start_date, end_date, create_date, *, file=None, in_progress=True):
        self.email = email
        self.file = file
        self.search_terms = search_terms
        self.start_date = start_date
        self.end_date = end_date
        self.create_date = create_date
        self.in_progress = in_progress
