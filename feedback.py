# Feedback class
# M to 1 to Users amnd Tasks

from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Feedback(Base):
    __tablename__ = 'Feedback'

    feedback_id = Column(Integer, primary_key=True)
    text = Column(String)
    users_id = Column(Integer, ForeignKey('Users.user_id'))
    users = relationship("Users", backref = "Feedback")
    tasks_id = Column(Integer, ForeignKey('Tasks.task_id'))
    tasks = relationship("Tasks", backref = "Feedback")

    def __init__(self, text, users, tasks):
        self.text = text
        self.users = users
        self.tasks = tasks
