from flask_wtf import FlaskForm
from wtforms.fields import IntegerField
from wtforms.validators import DataRequired


class AddCameraForm(FlaskForm):
    device_id = IntegerField("ID Устройства", validators=[])
