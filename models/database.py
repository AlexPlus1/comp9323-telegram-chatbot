# The database class
# aim to create the db and all the table
# provide all the functionalities of insert/delete/change records

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date

#from users import Users
#from feedback import Feedback
#from tasks import Tasks
#from teams import Teams
#from meetings import Meetings

# create a database engine that stores data in the local directory's comp9323.db
# a SQLAlchemy Engine that will interact with our sqlite database
# a SQLAlchemy ORM session factory bound to this engine
# a base class for our classes definitions.
engine = create_engine('sqlite:///comp9323.db')
DB_Session = sessionmaker(bind = engine)
Base = declarative_base()


class Database(object):
    def create_table(self):
        try:
            Base.metadata.create_all(engine)
        except:
            print("Table already there.")

    # insert an object to db
    def insert(self, object, session = DB_Session):
        # Bind the engine to the metadata of the Base class so that the
        # declaratives can be accessed through a DBSession instance
        # Create a DBsession() instance to establish all conversations with the database
        #DBSession = sessionmaker(bind=engine)
        session = session()
        session.add(object)
        session.commit()
        session.close()

    # return all meeting objects
    def get_all_meetings(self, session = DB_Session):
        session = session()
        meetings = session.query(Meetings).all()
        #for meeting in meetings:
        #    print (book.title)
        session.close()
        return meetings

    # return all task objects
    def get_all_tasks(self, session = DB_Session):
        session = session()
        tasks = session.query(Tasks).all()
        session.close()
        return tasks

    # return assigned tasks given team_id
    def get_assigned_tasks(self, session = DB_Session, team_id):
        session = session()
        tasks = session.query(Tasks).filter(Tasks.teams_id == team_id and Tasks.status == 'assigned').all()
        session.close()
        return tasks


