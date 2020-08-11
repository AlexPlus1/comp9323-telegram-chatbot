# Feedback class
# M to 1 to Users amnd Tasks

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base


class Feedback(Base):
    __tablename__ = "Feedback"

    feedback_id = Column(Integer, primary_key=True)
    feedback_type = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    user = relationship("Users", backref="Feedback")
    task_id = Column(Integer, ForeignKey("Tasks.task_id"))
    task = relationship("Tasks", backref="Feedback")
