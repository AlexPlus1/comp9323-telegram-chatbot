# The database class
# aim to create the db and all the table
# provide all the functionalities of insert/delete/change records
import arrow

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import consts

from .meetings import Meetings
from .base import Base
from .teams import Teams
from .users import Users
from .tasks import Tasks
from .notifications import Notifications

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
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    # insert an object to db
    def insert(self, obj):
        self.session.add(obj)
        self.session.commit()

    def delete(self, obj):
        self.session.delete(obj)
        self.session.commit()

    def set_remind(self, meeting_id, chat_id):
        """Set meeting reminder

        Args:
            meeting_id (int): the meeting ID
            chat_id (int): the Telegram chat ID
        """
        meeting = (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meeting_id)
            .first()
        )
        meeting.has_reminder = True
        notis = self.get_remind_notis(meeting, chat_id)
        self.session.add_all(notis)
        self.session.commit()

    def get_remind_notis(self, meeting, chat_id):
        """Get and create meeting reminder notifications

        Args:
            meeting (Meeting): the meeting object
            chat_id (int): the Telegram chat ID

        Returns:
            list: list of notifications
        """
        now = arrow.utcnow()
        notis = []
        noti_hours = [(-12, "12 hours"), (-1, "an hour")]

        # Create notifications 12 hours and 1 hour before the meeting
        for hours, hours_str in noti_hours:
            datetime = meeting.datetime.shift(hours=hours)
            if datetime > now:
                notis.append(
                    Notifications(
                        noti_type=consts.NOTI_MEETING,
                        meeting_id=meeting.meeting_id,
                        chat_id=chat_id,
                        text=f"You have a scheduled meeting in {hours_str}.",
                        datetime=datetime,
                    )
                )

        # Create notification when meeting starts
        noti = self.get_meeting_start_noti(meeting, chat_id)
        if noti is not None:
            notis.append(noti)

        # Create notifications when meeting ends
        noti = self.get_meeting_end_noti(meeting, chat_id)
        if noti is not None:
            notis.append(noti)

        return notis

    def get_meeting_start_noti(self, meeting, chat_id):
        """Get and create meeting start notification

        Args:
            meeting (Meeting): the meeting object
            chat_id (int): the Telegram chat ID

        Returns:
            Notification: the meeting start notification
        """
        noti = None
        if meeting.datetime > arrow.utcnow():
            text = (
                "You have a meeting scheduled for "
                f"<b>{meeting.formatted_datetime()}</b>. "
                "Here are some suggestions for your meeting:\n\n"
                "1.  Take notes and upload any notes from the meeting\n"
                "2.  Create and assign new tasks\n"
                "3.  Update details for discussed tasks\n"
                "4.  Schedule a follow-up meeting"
            )
            caption = None
            if meeting.agenda is not None:
                caption = "And here's the meeting agenda that you uploaded earlier:"

            noti = Notifications(
                noti_type=consts.NOTI_MEETING,
                meeting_id=meeting.meeting_id,
                chat_id=chat_id,
                text=text,
                datetime=meeting.datetime,
                doc_id=meeting.agenda,
                doc_caption=caption,
            )

        return noti

    def get_meeting_end_noti(self, meeting, chat_id):
        """Get and create meeting end notification

        Args:
            meeting (Meeting): the meeting object
            chat_id (int): the Telegram chat ID

        Returns:
            Notification: the meeting end notification
        """
        noti = None
        datetime = meeting.datetime.shift(minutes=meeting.duration)

        if datetime > arrow.utcnow():
            noti = Notifications(
                noti_type=consts.NOTI_MEETING,
                meeting_id=meeting.meeting_id,
                chat_id=chat_id,
                text=(
                    "Looks like you've just had a meeting, "
                    "you can now upload any notes you have for the meeting."
                ),
                datetime=datetime,
            )

        return noti

    def cancel_remind(self, meeting_id, chat_id):
        """Cancel meeting reminder notifications

        Args:
            meeting_id (int): the meeting ID
            chat_id (int): the Telegram chat ID
        """
        meeting = (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meeting_id)
            .first()
        )
        meeting.has_reminder = False

        # Delete all meeting notifications associated to the given
        # meeting ID and chat ID
        self.session.query(Notifications).filter(
            Notifications.noti_type == consts.NOTI_MEETING,
            Notifications.meeting_id == meeting_id,
            Notifications.chat_id == chat_id,
        ).delete()
        self.session.commit()

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

    def get_meetings(self, team_id=None, before=None, after=None):
        """Get all meetings from the database with filtering options

        Args:
            team_id (int, optional): the team ID. Defaults to None.
            before (datetime, optional): only get meetings before this datetime.
                Defaults to None.
            after (datetime, optional): only get meetings after this datetime.
                Defaults to None.

        Returns:
            list: list of meetings
        """
        meetings = self.session.query(Meetings)
        if team_id is not None:
            meetings = meetings.filter(Meetings.teams_id == team_id)
        if before is not None:
            meetings = meetings.filter(Meetings.datetime < before)
        if after is not None:
            meetings = meetings.filter(Meetings.datetime > after)

        return meetings.order_by(Meetings.datetime).all()

    def get_meeting_by_id(self, meeting_id):
        return (
            self.session.query(Meetings)
            .filter(Meetings.meeting_id == meeting_id)
            .first()
        )

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

    def get_passed_notis(self):
        return (
            self.session.query(Notifications)
            .filter(Notifications.datetime < arrow.utcnow())
            .all()
        )
