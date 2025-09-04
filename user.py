from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin
from ext import db
from ext import login_manager


user_groups = db.Table("user_group", db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                       db.Column("group_id", db.Integer, db.ForeignKey('groups.group_id')))
group_tags = db.Table("group_tag", db.Column('group_id', db.Integer, db.ForeignKey('groups.group_id')),
                      db.Column("tag_id", db.Integer, db.ForeignKey('tags.tagid')))


class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100), nullable=False, unique=True)
    email = db.Column('mail', db.String(100), nullable=False)
    password = db.Column('Password', db.String(260), nullable=False)
    time = db.Column('timecreated', db.DateTime,
                     default=lambda: datetime.now(timezone.utc))
    points = db.Column('points', db.Integer, default=0)
    streaks = db.Column('streak', db.Integer, default=0)
    level = db.Column('level', db.Integer, default=1)
    lastupdate = db.Column('last_streak_value',
                           db.DateTime, nullable=True, default=None)
    bio = db.Column('bio', db.String(100), default='No Bio Yet')
    groups = db.relationship(
        'Groups', secondary=user_groups, backref='members')


class Groups(db.Model):
    __tablename__ = 'groups'
    group_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    datecreated = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    groupdesc = db.Column(db.String(75), nullable=False)
    isapproved = db.Column(db.Boolean, default=False)
    isprivate = db.Column(db.Boolean, default=False, nullable=True)
    private_key = db.Column(db.String(255), nullable=True)


class Messages(db.Model):
    __tablename__ = 'messages'
    msgid = db.Column(db.Integer, primary_key=True)
    msgtime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    content = db.Column(db.Text(), nullable=False)
    senderid = db.Column('sender_id', db.ForeignKey(
        'users.id'), nullable=False)
    groupid = db.Column('grp_id', db.ForeignKey(
        'groups.group_id'), nullable=False)
    sender = db.relationship('Users', backref='messages')
    group = db.relationship('Groups', backref='messages')


class Questions(db.Model):
    __tablename__ = 'questions'
    qstid = db.Column(db.Integer, primary_key=True)
    qsttime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    qsttitle = db.Column(db.Text(), nullable=False)
    qstcontent = db.Column(db.Text(), nullable=False)
    senderid = db.Column('sender_id', db.ForeignKey(
        'users.id'), nullable=False)
    groupid = db.Column('grp_id', db.ForeignKey(
        'groups.group_id'), nullable=False)
    isapproved = db.Column('is_approved', db.Boolean, default=False)
    isdeleted = db.Column('is_deleted', db.Boolean, default=False)
    deletedwhen = db.Column('last_delete', db.DateTime,
                            nullable=True, default=None)
    sender = db.relationship('Users', backref='questions')
    group = db.relationship('Groups', backref='questions')

    @property
    def displayed_question(self):
        if self.isdeleted == True:
            return "[deleted]"
        else:
            return self.qstcontent

    @property
    def displayed_question_title(self):
        if self.isdeleted == True:
            return "[deleted]"
        else:
            return self.qsttitle


class Answers(db.Model):
    __tablename__ = 'answers'
    answid = db.Column(db.Integer, primary_key=True)
    anstime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    anscontent = db.Column(db.Text(), nullable=False)
    senderid = db.Column('sender_id', db.ForeignKey(
        'users.id'), nullable=False)
    groupid = db.Column('grp_id', db.ForeignKey(
        'groups.group_id'), nullable=False)
    qstid = db.Column(db.Integer, db.ForeignKey('questions.qstid'))
    isdeleted = db.Column('is_deleted', db.Boolean, default=False)
    isapproved = db.Column('is_approved', db.Boolean, default=False)
    deletedwhen = db.Column('last_delete', db.DateTime,
                            nullable=True, default=None)
    isdeleted = db.Column('is_deleted', db.Boolean, default=False)

    sender = db.relationship('Users', backref='answers')
    group = db.relationship('Groups', backref='answers')
    question = db.relationship('Questions', backref='answers')

    @property
    def displayed_answer(self):
        if self.isdeleted == True:
            return "[deleted]"
        else:
            return self.anscontent


class Tags(db.Model):
    __tablename__ = 'tags'
    tagid = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(30), nullable=False)
    group = db.relationship('Groups', secondary=group_tags, backref='tags')


class Votes(db.Model):
    __tablename__ = 'votes'
    voteid = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, default=0)
    userid = db.Column('user_id', db.ForeignKey('users.id'))
    questid = db.Column('quest_id', db.ForeignKey('questions.qstid'))
    votetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('Users', backref='Votes')
    question = db.relationship('Questions', backref='votes')
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='unique_user_vote'),
    )


class Ansvotes(db.Model):
    __tablename__ = 'answervotes'
    voteid = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, default=0)
    userid = db.Column('user_id', db.ForeignKey('users.id'))
    questid = db.Column('quest_id', db.ForeignKey('questions.qstid'))
    answid = db.Column('answ_id', db.ForeignKey('answers.answid'))
    votetime = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship('Users', backref='Answvotes')
    question = db.relationship('Questions', backref='Answvotes')
    answers = db.relationship('Answers', backref='Answovotes')
    __table_args__ = (
        db.UniqueConstraint('user_id', 'answ_id', name='answer_unique_vote'),
    )


class Groupmedia(db.Model):
    fileid = db.Column("media_id", db.Integer, primary_key=True)
    file_defname = db.Column(
        "file_default_name", db.String(255), nullable=False)
    file_storedname = db.Column(
        "stored_file_bucket_name", db.String(255), nullable=False)
    group_id = db.Column('group_id', db.ForeignKey("groups.group_id"))
    user_id = db.Column(db.ForeignKey("users.id"))
    upload_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    group = db.relationship("Groups", backref="files")
    user = db.relationship("Users", backref="files")


@login_manager.user_loader
def load_user(users_id):
    return Users.query.get(int(users_id))
