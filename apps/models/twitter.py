from sqlalchemy import Column, String, Integer, DateTime, Boolean
from apps.models import db


class TwitterScrape(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    file = Column(String(), nullable=True)
    search_terms = Column(String(100), nullable=False)
    limit = Column(String(64), nullable=True)
    create_date = Column(DateTime())
    in_progress = Column(Boolean(), default=True)

    def __init__(self, email, search_terms, limit, create_date, *, file=None, in_progress=True):
        self.email = email
        self.file = file
        self.search_terms = search_terms
        self.limit = limit
        self.create_date = create_date
        self.in_progress = in_progress
