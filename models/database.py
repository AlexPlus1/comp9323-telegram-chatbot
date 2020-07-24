# The database class
# aim to create the db and all the table
# provide all the functionalities of insert/delete/change records

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date

# from users import Users
# from feedback import Feedback
# from tasks import Tasks
# from teams import Teams
# from meetings import Meetings
from models.base import Base
from models.teams import Teams

# create a database engine that stores data in the local directory's comp9323.db
# a SQLAlchemy Engine that will interact with our sqlite database
# a SQLAlchemy ORM session factory bound to this engine
# a base class for our classes definitions.
engine = create_engine("sqlite:///bot.db")
DB_Session = sessionmaker(bind=engine)


class Database(object):
    def __init__(self):
        self.session = DB_Session()

    def create_table(self):
        try:
            Base.metadata.create_all(engine)
        except:
            print("Table already there.")

    # insert an object to db
    def insert(self, object):
        # Bind the engine to the metadata of the Base class so that the
        # declaratives can be accessed through a DBSession instance
        # Create a DBsession() instance to establish all conversations with the database
        # DBSession = sessionmaker(bind=engine)
        self.session.add(object)
        self.session.commit()

    def get_team(self, team_id):
        team = self.session.query(Teams).filter(Teams.team_id == team_id).first()

        return team

    # return all meeting objects  given team_id
    def get_all_meetings(self, team_id):
        meetings = self.session.query(Meetings).filter(Teams.team_id == team_id).all()
        return meetings

    # return all task objects given team_id
    def get_all_tasks(self, team_id):
        tasks = self.session.query(Tasks).filter(Teams.team_id == team_id).all()
        return tasks

    # return assigned tasks given team_id
    def get_assigned_tasks(self, team_id):
        tasks = (
            self.session.query(Tasks)
            .filter(Tasks.teams_id == team_id and Tasks.status == "assigned")
            .all()
        )
        return tasks

