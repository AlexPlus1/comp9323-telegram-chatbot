# Meetints class
# M to 1 Teams

from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Meetings(Base):
    __tablename__ = 'Meetings'

    meeting_id = Column(Integer, primary_key=True)
    date_time = Column(Date)
    has_reminder = Column(Boolean)
    notes = Column(String)
    teams_id = Column(Integer, ForeignKey('Teams.team_id'))
    teams = relationship("Teams", backref = "Meetings")

    def __init__(self, date_time, has_reminder, notes, teams):
        self.date_time = date_time
        self.has_reminder = has_reminder
        self.notes = notes
        self.teams = teams

