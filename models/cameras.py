import sqlalchemy
from sqlalchemy_serializer import SerializerMixin
from models.db_session import SqlAlchemyBase

from datetime import datetime


class Camera(SqlAlchemyBase):
    __tablename__ = 'Cameras'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    device_id = sqlalchemy.Column(sqlalchemy.Integer)
    name = sqlalchemy.Column(sqlalchemy.String)
