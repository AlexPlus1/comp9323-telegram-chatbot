# Users class 
# M to M to Teams and Tasks

from sqlalchemy import Column, String, Integer, Date, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

users_teams_association = Table(
    'users_teams', Base.metadata,
    Column('users_id', Integer, ForeignKey('Users.user_id')),
    Column('teams_id', Integer, ForeignKey('Teams.team_id'))
)

users_tasks_association = Table(
    'users_tasks', Base.metadata,
    Column('users_id', Integer, ForeignKey('Users.user_id')),
    Column('tasks_id', Integer, ForeignKey('Tasks.task_id'))

)


class Users(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True)
    name = Column(String)
    teams = relationship("Teams", secondary = users_teams_association)
    tasks = relationship("Tasks", secondary = users_tasks_association)

    def __init__(self, name):
        self.name = name
