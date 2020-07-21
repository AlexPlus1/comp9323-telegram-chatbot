from sqlalchemy import Column, String, Integer, Date
from models.base import Base


class Teams(Base):
    __tablename__ = "Teams"

    team_id = Column(Integer, primary_key=True)

