from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class AddForm(FlaskForm):
    userid = StringField('userid', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('email', validators=[DataRequired(), Length(min=2, max=80)])
    password = StringField('password', validators=[DataRequired(), Length(min=2, max=25)])
    submit = SubmitField('Add User')

# class CompareFaces(FlaskForm):
class attendanceForm(FlaskForm):
    classid = StringField('classid', validators=[DataRequired(), Length(min=2, max=15)])
    date = StringField('date', validators=[DataRequired()])
    submit = SubmitField('submit')


