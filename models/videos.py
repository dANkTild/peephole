import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from models.db_session import SqlAlchemyBase

from datetime import datetime


class Video(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'Videos'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    file = sqlalchemy.Column(sqlalchemy.String,
                             default="{}.mp4".format(datetime.now().timestamp()))
    preview = sqlalchemy.Column(sqlalchemy.String,
                                default="{}_preview.jpg".format(datetime.now().timestamp()))
    name = sqlalchemy.Column(sqlalchemy.String, default=datetime.now())
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())

    def generate(self):
        now = datetime.now()
        self.file = "{}.mp4".format(now.timestamp())
        self.preview = "{}_preview.jpg".format(now.timestamp())
        self.name = now
        self.date = now
