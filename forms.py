from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import EqualTo, Email, DataRequired, Length, Regexp, ValidationError
from user import Users, Groups


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(
        min=4, max=24, message='Username has to be between 4 and 24 characters'), Regexp(r'^\S*$', message='Name cannot contain spaces')])
    password = PasswordField('Password', validators=[DataRequired(), Length(
        min=7, max=50, message='Password has to be between 7 and 50 characters')])
    submit = SubmitField('Submit')

    def validate_username(self, username):
        user = Users.query.filter_by(name=username.data).first()
        if not user:
            raise ValidationError("User doesn't exists")


class SignupForm(FlaskForm):
    email = StringField('Email Account', validators=[DataRequired(), Email()])
    name = StringField('Username', validators=[DataRequired(), Length(
        min=4, max=24, message='Username has to be between 4 and 24 characters'), Regexp(r'^\S*$', message='Name cannot contain spaces')])
    password = PasswordField('Password', validators=[DataRequired(), Length(
        min=7, max=50, message='Password has to be between 7 and 50 characters')])
    confirm_password = PasswordField('Confirm Password', validators=[
                                     DataRequired(), EqualTo('password', message='must be Equal to Passowrd')])
    submit = SubmitField('Submit')

    def validate_username(self, username):

        user = Users.query.filter_by(name=username.data).first()
        if user:
            raise ValidationError("User already exists")


class CreateGroup(FlaskForm):
    groupname = StringField(validators=[DataRequired()])
    groupdesc = StringField(validators=[DataRequired(), Length(
        min=8, max=75, message='Group Descriptions Must be between 8 and 75 characters ')])
    submit = SubmitField('Submit')


class SuggestGroup(FlaskForm):
    groupname = StringField(validators=[DataRequired(), Length(min=2, max=75)])
    groupdesc = StringField(validators=[DataRequired(), Length(
        min=8, max=75, message='Group Descriptions Must be between 8 and 75 characters ')])
    submit = SubmitField('Submit')

    def validate_groupname(self, groupname):
        grp = Groups.query.filter_by(name=groupname.data).first()
        if grp and grp.isapproved:
            raise ValidationError('Group already exists')


class Question(FlaskForm):
    questiontitle = TextAreaField('Title', validators=[DataRequired()])
    questiondesc = TextAreaField('Description', validators=[DataRequired(), Length(
        min=6, max=500, message="Question descriptions must be between 6 and 500 Characters")])
    submit = SubmitField('Submit')


class Answer(FlaskForm):
    answerbody = TextAreaField('Description', validators=[DataRequired(), Length(
        min=6, max=500, message=" must be between 6 and 500 Characters")])
    submit = SubmitField('Submit')
