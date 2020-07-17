from database import Base, Database

from datetime import date

from Users import Users
from Feedback import Feedback
from Tasks import Tasks
from Teams import Teams
from Meetings import Meetings

# examples
db = Database()
db.create_table()

user = Users('Alex')
team = Teams()
task = Tasks('database model', date(2020,7,15),'doing','lol',team)
user.tasks = [task]
user.teams = [team] 
feedback = Feedback('lmao', user, task)
meeting = Meetings(date(2020,7,17), False, 'nothing notes', team)

db.insert(user)
db.insert(team)
db.insert(task)
db.insert(feedback)
db.insert(meeting)