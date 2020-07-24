# Tasks Class
# M to 1 to Teams
# status = 'assigned' / 'unassigned'


from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Tasks(Base):
    __tablename__ = 'Tasks'

    task_id = Column(Integer, primary_key=True)
    name = Column(String)
    due_date = Column(Date)
    status = Column(String)
    summary = Column(String)
    teams_id = Column(Integer, ForeignKey('Teams.team_id'))
    teams = relationship("Teams", backref = "Tasks")

    def __init__(self, name, due_date, status, summary, teams):
        self.name = name
        self.due_date = due_date
        self.status = status
        self.summary = summary
        self.teams = teams

    def complete_suggestion(self, tasks = None):
        suggestion = None
        if self.teams.suggestions:
            suggestion = f"Please review and provide feedback for task: {self.name}\n"
            if tasks:
                suggestions += "Remaining assigned tasks:\n"
                for task in tasks:
                    suggestions += f"- {task}\n"
        return suggestion
