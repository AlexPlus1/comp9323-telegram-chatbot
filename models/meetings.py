# Meetints class
# M to 1 Teams
import arrow

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType

import consts
from models.base import Base


class Meetings(Base):
    __tablename__ = "Meetings"

    meeting_id = Column(Integer, primary_key=True)
    # changed datetime, added duration
    datetime = Column(ArrowType)
    duration = Column(Integer)
    has_reminder = Column(Boolean, server_default="0")
    agenda = Column(String)
    notes = Column(String)
    teams_id = Column(Integer, ForeignKey("Teams.team_id"))
    teams = relationship("Teams", backref="Meetings")

    def formatted_datetime(self):
        return (
            arrow.get(self.datetime).to(consts.TIMEZONE).format(consts.DATETIME_FORMAT)
        )
