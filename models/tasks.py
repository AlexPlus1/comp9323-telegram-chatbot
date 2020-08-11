# Tasks Class
# M to 1 to Teams

import arrow

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType

import consts

from models.base import Base


class Tasks(Base):
    __tablename__ = "Tasks"

    task_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    due_date = Column(ArrowType)
    status = Column(String, nullable=False)
    summary = Column(String)
    team_id = Column(Integer, ForeignKey("Teams.team_id"))
    team = relationship("Teams", backref="Tasks")
    user_id = Column(Integer, ForeignKey("Users.user_id"))
    user = relationship("Users", backref="Tasks")
    feedback = relationship('Feedback')

    def formatted_date(self):
        if self.due_date is not None:
            return (
                arrow.get(self.due_date).to(consts.TIMEZONE).format("ddd D MMM, YYYY")
            )
