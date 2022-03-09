import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from models.db_session import SqlAlchemyBase

from datetime import datetime


class Photo(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'Photos'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    file = sqlalchemy.Column(sqlalchemy.String,
                             default="{}.jpg".format(datetime.now().timestamp()))
    name = sqlalchemy.Column(sqlalchemy.String, default=datetime.now())
    date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())

    def generate(self):
        self.file = "{}.jpg".format(datetime.now().timestamp())
        self.name = datetime.now()
        self.date = datetime.now()
