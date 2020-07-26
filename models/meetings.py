# Meetints class
# M to 1 Teams

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy_utils import ArrowType
from models.base import Base


class Meetings(Base):
    __tablename__ = "Meetings"

    meeting_id = Column(Integer, primary_key=True)
    # changed datetime, added duration
    datetime = Column(ArrowType)
    duration = Column(Integer)
    has_reminder = Column(Boolean)
    notes = Column(String)
    teams_id = Column(Integer, ForeignKey("Teams.team_id"))
    teams = relationship("Teams", backref="Meetings")

    def __init__(self, datetime, duration, has_reminder, notes, teams):
        self.datetime = datetime
        self.duration = duration
        self.has_reminder = has_reminder
        self.notes = notes
        self.teams = teams

    def meeting_suggestion(self):
        suggestion = None
        if self.teams.suggestions:
            suggestion = f"""
                You have a meeting scheduled for {self.datetime}
                Here are suggestions for your meeting:
                1.  Take notes and upload any notes from the meeting
                2.  Create and assign new tasks
                3.  Update details for discussed tasks
                4.  Schedule a follow-up meeting
            """
        return suggestion
