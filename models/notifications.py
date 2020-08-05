from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy_utils import ArrowType

from models.base import Base


class Notifications(Base):
    __tablename__ = "Notifications"

    noti_id = Column(Integer, primary_key=True)
    noti_type = Column(Integer, nullable=False)
    meeting_id = Column(Integer, ForeignKey("Meetings.meeting_id"))
    chat_id = Column(Integer, nullable=False)
    datetime = Column(ArrowType, nullable=False)
    text = Column(String, nullable=False)
    doc_id = Column(String)
    doc_caption = Column(String)
