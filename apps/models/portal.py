from ast import For
from unicodedata import category
from sqlalchemy import Enum, Column, String, Integer, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property
from apps.models import db, User, Base

import enum

class Status(enum.Enum):
    irrelevant = "irrelevant"
    pending = "pending"
    done = "done"
    

# role_association_table = Table(
#     "role_association",
#     Base.metadata,
#     Column("reviewer_id", ForeignKey("reviewer.id")),
#     Column("role_id", ForeignKey("role.id")),
# )

# class Reviewer(Base):
#     __tablename__ = "reviewer"
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, ForeignKey("user.id"))
#     user = relationship("User", back_populates="reviewer", uselist=False)
#     role_id = Column(Integer, ForeignKey("role.id"))
#     role = relationship("Role")
#     @hybrid_property
#     def permissions(self):
#         return self.role.permissions # update when it's the sum of all the roles
    
#     def __init__(self, user, *, role=None):
#         self.user = user
#         self.role = role or user.role

class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    name = Column(String())
    permissions = Column(Integer)

    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions
    

class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(Status))
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    role_id = Column(Integer, ForeignKey("role.id"))
    role = relationship("Role")

    article_source =    Column(String(), nullable=True)
    article_title =     Column(String(), nullable=True)
    article_text =      Column(String(), nullable=True)
    summary_title =     Column(String(), nullable=True)
    summary_text =      Column(String(), nullable=True)
    attributes =        Column(String(), nullable=True)
    category =          Column(String(), nullable=True)
    city =              Column(String(), nullable=True)
    incident_date =     Column(String(), nullable=True)
    location =          Column(String(), nullable=True)
    project =           Column(String(), nullable=True)
    sub_category =      Column(String(), nullable=True)
    # not_relevant =      Column(String(), mullable=True)
    # title = Column(String(), nullable=True)
    # content = Column(String(), nullable=True)

    # file = Column(String(), nullable=True)
    # search_terms = Column(String(100), nullable=False)
    # limit = Column(String(64), nullable=True)
    # create_date = Column(DateTime())
    # in_progress = Column(Boolean(), default=True)

    def __init__(self, *, status=Status.pending, user: User, role: Role=None, article_source, article_title, article_text, attributes=None, category, city=None, incident_date=None, location=None, project=None, sub_category=None, summary_text=None, summary_title=None):
        # self.current_reviewer_id = Column(Integer, ForeignKey("current_reviewer.id"))
        self.user = user
        self.status = status
        self.role = role or (user.role if user else None)
        # self.next_reviewer_id = next_reviewer_id
        self.article_source = article_source
        self.article_title = article_title
        self.article_text = article_text
        self.attributes = attributes
        self.category = category
        self.city = city
        self.incident_date = incident_date
        self.location = location
        self.project = project
        self.sub_category = sub_category
        self.summary_text = summary_text
        self.summary_title = summary_title

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
