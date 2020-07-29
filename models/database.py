# The database class
# aim to create the db and all the table
# provide all the functionalities of insert/delete/change records

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.meetings import Meetings
from models.base import Base
from models.teams import Teams
from models.users import Users

# create a database engine that stores data in the local directory's bot.db
# a SQLAlchemy Engine that will interact with our sqlite database
# a SQLAlchemy ORM session factory bound to this engine
# a base class for our classes definitions.
engine = create_engine("sqlite:///bot.db", connect_args={"check_same_thread": False})
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

    def set_remind(self, meating_id):
        info = (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meating_id)
            .first()
        )
        info.has_reminder = True

    def cancel_remind(self, meating_id):
        info = (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meating_id)
            .first()
        )
        info.has_reminder = False

    def reminder_state(self, meating_id):
        info = (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meating_id)
            .first()
        )

        return info.has_reminder

    def commit(self):
        self.session.commit()

    def get_team(self, team_id):
        team = self.session.query(Teams).filter(Teams.team_id == team_id).first()
        if team is None:
            team = Teams(team_id)
            self.insert(team)

        return team

    def get_user(self, user_id):
        return self.session.query(Users).filter(Users.user_id == user_id).first()

    # return all meeting objects given team_id
    def get_all_meetings(self, team_id):
        meetings = (
            self.session.query(Meetings).filter(Meetings.teams_id == team_id).all()
        )
        return meetings

    def get_all_my_meetings(self):
        meetings = self.session.query(Meetings).all()
        return meetings

    # return all meeting objects given team_id and meeting_datetime
    def get_meeting_by_time(self, team_id, meeting_datetime):
        meeting = (
            self.session.query(Meetings)
            .filter(Meetings.teams_id == team_id, Meetings.datetime == meeting_datetime)
            .first()
        )
        return meeting

    # return the closest meeting given team_id and meeting_datetime
    def get_closest_meeting(self, team_id, meeting_datetime):
        greater = (
            self.session.query(Meetings)
            .filter(Meetings.datetime > meeting_datetime)
            .limit(1)
            .all()
        )
        lesser = (
            self.session.query(Meetings)
            .filter(Meetings.datetime < meeting_datetime)
            .limit(1)
            .all()
        )

        if greater is None and lesser is not None:
            return lesser
        elif greater is not None and lesser is None:
            return greater
        else:
            diff_greater = abs(greater.datetime - meeting_datetime)
            diff_lesser = abs(lesser.datetime - meeting_datetime)

            if diff_greater < diff_lesser:
                return greater
            else:
                return lesser

    # return all task objects given team_id
    def get_all_tasks(self, team_id):
        tasks = self.session.query(Tasks).filter(Teams.team_id == team_id).all()
        return tasks

    # return assigned tasks given team_id
    def get_assigned_tasks(self, team_id):
        tasks = (
            self.session.query(Tasks)
            .filter(Tasks.teams_id == team_id, Tasks.status == "assigned")
            .all()
        )
        return tasks

