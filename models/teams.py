from sqlalchemy import Column, String, Integer, Date, Boolean
from models.base import Base


class Teams(Base):
    __tablename__ = "Teams"

    team_id = Column(Integer, primary_key=True)
    suggestions = Column(Boolean)

    def __init__(self, team_id):
        self.suggestions = True
        self.team_id = team_id

    def suggestions_off(self):
        response = "Suggestions have been turned off"
        if not self.suggestions:
            response = "Suggestions are already turned off"
        self.suggestions = False
        return response

    def suggestions_on(self):
        response = "Suggestions have been turned on"
        if self.suggestions:
            response = "Suggestions are already turned on"
        self.suggestions = False
        return response
