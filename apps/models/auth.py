from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from apps.models import db

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String(100),  unique=True)
    password = Column(String(64))
    username = Column(String(64), unique=True)
    permissions = Column(Integer)
    role_id = Column(Integer, ForeignKey("role.id"))
    role = relationship("Role")

    @hybrid_property
    def permissions(self):
        return self.role.permissions # update when it's the sum of all the roles

    def __init__(self, email, username, password, role):
        self.email = email
        self.password = password
        self.username = username
        self.role = role
