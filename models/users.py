# Users class
# M to M to Teams and Tasks

from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

users_teams_association = Table(
    "users_teams",
    Base.metadata,
    Column("users_id", Integer, ForeignKey("Users.user_id")),
    Column("teams_id", Integer, ForeignKey("Teams.team_id")),
)

users_tasks_association = Table(
    "users_tasks",
    Base.metadata,
    Column("users_id", Integer, ForeignKey("Users.user_id")),
    Column("tasks_id", Integer, ForeignKey("Tasks.task_id")),
)


class Users(Base):
    __tablename__ = "Users"

    # Attributes
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    username = Column(String)

    # Relationships
    teams = relationship("Teams", secondary=users_teams_association)
    tasks = relationship("Tasks", secondary=users_tasks_association)

    @property
    def name(self):
        if self.username is not None:
            name = f"@{self.username}"
        else:
            name = self.first_name

        return name
