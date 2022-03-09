from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired


class AddUserForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired()])
    preview = FileField("Изображение")
    email = EmailField("Email")
