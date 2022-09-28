from sqlalchemy import Column, String, Integer, DateTime, Boolean
from apps.models import db


class Message(db.Model):
    id = Column(Integer, primary_key=True)
    receive_user=Column(String())
    send_user=Column(String())
    text=Column(String())
    send_time=Column(DateTime())

    def __init__(self, receive_user, send_user, text, send_time):
        self.receive_user = receive_user
        self.send_user = send_user
        self.text = text
        self.send_time = send_time