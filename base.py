from flask_socketio import emit, leave_room, join_room, send
from sqlalchemy import func, or_
from ext import db
from flask_migrate import Migrate
from flask import Flask, render_template, request, session, redirect, url_for, flash
from forms import LoginForm, SignupForm, CreateGroup, SuggestGroup, Question, Answer
from user import db, Users, Groups, Messages, Questions, Answers, Tags, Votes, Ansvotes
from datetime import datetime, timedelta, timezone
from flask import jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from ext import login_manager, socketio
from flask_login import login_user, login_required, current_user, logout_user
import redis
import pickle
import json

app = Flask(__name__)
# csrf.init_app(app)
migrate = Migrate(app, db)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


app.secret_key = "12345"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://postgres:mypasscode@localhost/User"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"


login_manager.init_app(app)
login_manager.login_view = "login"
db.init_app(app)
socketio.init_app(app)


@app.route("/home")
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


def update_streak(id):
    streak_user = db.session.get(Users, id)
    if streak_user:
        now = datetime.now(timezone.utc)

        # Ensure lastupdate is timezone-aware
        if streak_user.lastupdate is None or (
            streak_user.lastupdate.tzinfo is None and now -
                streak_user.lastupdate.replace(
                    tzinfo=timezone.utc) >= timedelta(hours=24)
        ) or (
            streak_user.lastupdate.tzinfo is not None and now -
                streak_user.lastupdate >= timedelta(hours=24)
        ):
            streak_user.streaks += 1
            streak_user.lastupdate = now
            flash(f"Streak {streak_user.streaks-1} -> {streak_user.streaks}")
            db.session.commit()


def serialize_groups(g):
    return {
        "group_id": g.group_id,
        "name": g.name,
        "datecreated": g.datecreated.strftime("%b,%d,%Y"),
        "groupdesc": g.groupdesc,
        "isapproved": g.isapproved,
        "message_count": len(g.messages),
        "question_count": len(g.questions)
    }


def serialize_questions(q, net_count, has_upvoted, has_downvoted):
    return {
        "qstid": q.qstid,
        "qsttime": q.qsttime.strftime("%b,%d,%Y"),
        "qsttitle": q.qsttitle,
        "qstcontent": q.qstcontent,
        "senderid": q.senderid,
        "groupid": q.groupid,
        "isaprroved": q.isapproved,
        "isdeleted": q.isdeleted,
        "deletedwhen": q.deletedwhen,
        "displayed_question": q.displayed_question,
        "displayed_question_title": q.
        displayed_question_title,
        "sender_name": q.sender.name,
        "net_count": net_count,
        "has_upvoted": has_upvoted,
        "has_downvoted": has_downvoted,
        "answer_length": len(q.answers),
        "group_name": q.group.name

    }


@app.route("/user")
def user():
    if current_user.is_authenticated == False:
        return redirect("login")
    session["username"] = current_user.name
    user = Users.query.get(current_user.id)
    return render_template(
        "user.html",
        user=user,
    )


@app.route("/check/<user_name>", methods=["POST", "GET"])
def other_status(user_name):
    # if current_user.is_authenticated == False:
    #     return redirect("login")
    # session["username"] = current_user.name
    user = Users.query.filter_by(name=user_name).first()

    return render_template(
        "check_else.html",
        user=user,
    )


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        verify = Users.query.filter_by(name=username).first()
        if check_password_hash(verify.password, password):

            login_user(verify, remember=True)
            session["email"] = current_user.email
            session["username"] = current_user.name

            return redirect(url_for("user"))
        else:
            flash("Wrong Password", "error")
            return redirect(url_for("login"))
    if current_user.is_authenticated:
        if request.method == "GET":
            verify = Users.query.filter_by(name=current_user.name).first()
            form.username.data = current_user.name

    return render_template("login.html", form=form)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data
        password = form.password.data
        email = form.email.data
        hashed_password = generate_password_hash(
            password, method="pbkdf2:sha256")
        new_user = Users(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        session["email"] = email
        session["username"] = name

        flash("Account Created", "success")
        return redirect(url_for("login"))

    return render_template("signup.html", form=form)


@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/create_course", methods=["POST", "GET"])
def create():
    type = "Create a Group"
    form = CreateGroup()
    if current_user.is_authenticated and current_user.name == "Aquaderue":
        form = CreateGroup()
        if request.method == "POST" and form.validate_on_submit():
            grpname = form.groupname.data
            grpdesc = form.groupdesc.data
            session["grpname"] = grpname
            session["grpdesc"] = grpdesc
            if Groups.query.filter_by(name=grpname).first():
                flash("Group Exists")
                return render_template("create_group.html", form=form)
            else:
                new_group = Groups(
                    name=grpname, groupdesc=grpdesc, isapproved=True)
                db.session.add(new_group)
                db.session.commit()
                flash("Group created", "success")
                return redirect(url_for("add_tags_page", groupid=new_group.group_id))
    else:
        flash("Not authorized", "error")
        return redirect(url_for("home"))

    return render_template("create_group.html", form=form, type=type)


@app.route("/groups")
def show_groups():
    all_group_cache = "all_groups"
    all_g_cached = r.get(all_group_cache)
    if current_user.is_authenticated:
        group_cache_keys = f"displayed_groups_for_users:{current_user.id}"

        cached = r.get(group_cache_keys)
        print("cached info")
        if cached:
            groups = json.loads(cached)
        else:
            groups = Groups.query.filter_by(isapproved=True).all()
            m_group = current_user.groups
            group = set(groups).difference(set(m_group))
            user_group = list(group)
            queried_group = [serialize_groups(g) for g in user_group]
            groups = queried_group
            print('failed')
            r.setex(group_cache_keys, 300, json.dumps(groups))
            for g in [serialize_groups(g) for g in Groups.query.all()]:
                r.hset(f"group_name_by_id", g["group_id"], g["name"])
                r.hset(f"group_id_by_name", g["name"], g["group_id"])

    else:
        if all_g_cached:
            groups = json.loads(all_g_cached)
            print('from_cache')
        else:
            groups = [serialize_groups(g) for g in Groups.query.all()]
            print("not from")
            r.setex(all_group_cache, 600, json.dumps(groups))

    return render_template("groups.html", groups=groups)


@app.route("/join_group/<int:group_id>", methods=["POST", "GET"])
def join(group_id):
    if current_user.is_authenticated == False:
        flash("You are not logged in", "warning")
        return redirect(url_for("login"))
    group = Groups.query.filter_by(group_id=group_id, isapproved=True).first()

    if group not in user.groups:
        flash("Successfully Joined", "success")
        current_user.groups.append(group)
        db.session.commit()
    else:
        flash("Already a member", "error")
    return redirect(url_for("show_groups"))


@app.route("/suggest_group", methods=["GET", "POST"])
def suggest():
    type = "Suggest a Group"
    form = SuggestGroup()
    if current_user.is_authenticated == False:
        flash("Please log in First")
        return redirect(url_for("home"))
    form = SuggestGroup()

    if form.validate_on_submit():
        grpname = form.groupname.data
        grpdesc = form.groupdesc.data
        new_group = Groups(name=grpname, groupdesc=grpdesc)
        db.session.add(new_group)
        db.session.commit()
        flash("Group Suggested to Admins", "success")
        return redirect(url_for("add_tags_page", groupid=new_group.group_id))

    return render_template(
        "create_group.html", form=form, type=type, tags=Tags.query.all()
    )


@app.route("/pending_groups", methods=["POST", "GET"])
def show_pending_groups():

    if current_user.is_authenticated and current_user.name == "Aquaderue":
        groups = Groups.query.all()

    else:
        flash("Not Authorized", "error")
        return redirect(url_for("home"))
    return render_template("approve.html", groups=groups)


@app.route("/approve/<int:group_id>", methods=["POST", "GET"])
def approve(group_id):
    if current_user.is_authenticated and current_user.name == "Aquaderue":
        group = db.session.get(Groups, group_id)
        if group:
            group.isapproved = True

        db.session.commit()
        flash("Group Approved", "success")
        return redirect(url_for("home"))
    return redirect(url_for("show_pending_groups"))


@app.route("/my_groups")
def my_group():
    if current_user.is_authenticated:
        mygroup_cache_key = f"{current_user.id}_groups"
        cached = r.get(mygroup_cache_key)
        if cached:
            groups = json.loads(cached)
            print('from cache')
        else:
            groups = current_user.groups
            pers_groups = [serialize_groups(g) for g in groups]
            groups = pers_groups
            r.setex(mygroup_cache_key, 300, json.dumps(groups))
            print("Not")

        return render_template("my_group.html", groups=groups)
    else:
        flash("Please Log In", "warning")
        return redirect(url_for("home"))


@app.route("/chat/<group_name>")
def chat(group_name):

    group = Groups.query.filter_by(name=group_name).first()
    if not group or not group.isapproved:
        flash("Group does not exist")
        return redirect(url_for("home"))
    if current_user.is_authenticated:
        user_groups = current_user.groups[:5]
    else:
        user_groups = []

    display_name = current_user.name if current_user.is_authenticated else "Anonymous"

    past_msg = (
        Messages.query.filter_by(groupid=group.group_id)
        .order_by(Messages.msgtime.asc())
        .limit(50)
        .all()
    )
    return render_template(
        "chat.html",
        group=group,
        history=past_msg,
        current_user_groups=user_groups,
        display_name=display_name
    )


@socketio.on("join")
def join_place(data):
    room = data["room"]
    join_room(room)
    emit("room_joined", {"message": "Room joined successfully"}, room=room)


@socketio.on("leave")
def exit_room(data):
    room = data["room"]
    leave_room(room)
    emit("room_left", {"message": "Room exited successfully"}, room=room)


@socketio.on("typing")
def typing(data):
    room = data["room"]
    username = Users.query.filter_by(name=data["username"]).first()
    username = username.name
    emit(
        "handle_typing",
        {"room": room, "username": username},
        room=room,
        include_self=False,
    )


@socketio.on("send_message")
def handle_sent_message(data):

    group = Groups.query.filter_by(name=data["group"]).first()
    new_msg = Messages(
        content=data["message"], senderid=current_user.id, groupid=group.group_id
    )
    db.session.add(new_msg)
    db.session.commit()

    emit(
        "receive_message",
        {
            "username": current_user.name,
            "group": group.name,
            "message": new_msg.content,
            "time": new_msg.msgtime.strftime("%H:%M"),
        },
        to=data["group"],
        broadcast=True,
    )


@app.route("/question/<group_name>", methods=["GET", "POST"])
def question(group_name):
    if current_user.is_authenticated:
        form = Question()
        group = Groups.query.filter_by(isapproved=True).all()

        questedgroup = r.hget("group_id_by_name", group_name)
        print(questedgroup)

        if questedgroup:
            print("Achieved")
        if not questedgroup:
            "had to hit the db"
            questedgroup = Groups.query.filter_by(
                name=group_name, isapproved=True).first()
        if form.validate_on_submit():

            title = form.questiontitle.data
            description = form.questiondesc.data

            newqst = Questions(
                qsttitle=title,
                qstcontent=description,
                senderid=current_user.id,
                groupid=questedgroup.group_id,
            )
            db.session.add(newqst)
            db.session.commit()
            flash("Question Sent", "success")
            return redirect(url_for('group_questions', group_name=group_name))
    else:
        flash("Please Login")
    return render_template("askquestion.html", form=form, available_groups=group)


@app.route("/showquestions/<group_name>", methods=["GET", "POST"])
def group_questions(group_name):
    questedgroup = Groups.query.filter_by(
        name=group_name).first()
    if not questedgroup:
        flash("Group Does Not Exist")
        return redirect(url_for("home"))
    question_cache_key = f"group_question{questedgroup.name}"
    cached = r.get(question_cache_key)
    if cached:
        questions_with_votes = json.loads(cached)
        print("from_cache")
    else:

        # Get all questions for this group with vote counts
        group_questions = (
            db.session.query(
                Questions, func.coalesce(
                    func.sum(Votes.value), 0).label("net_count")
            )
            .outerjoin(Votes, Votes.questid == Questions.qstid)
            .filter(Questions.groupid == questedgroup.group_id, or_(Questions.isdeleted.is_(False), Questions.isdeleted.is_(None)))
            .group_by(Questions.qstid)
            .order_by(Questions.qsttime.desc())  # Optional: newest first
            .all()
        )
        print(group_questions)
        if not group_questions:
            questions_with_votes = []

    # Fetch approved groups for sidebar/menu
        user_groups = current_user.groups if current_user.is_authenticated else None

        # Prepare data with user's vote status
        questions_votes = []
        for question, net_count in group_questions:
            user_vote = None
            if current_user.is_authenticated:
                vote = Votes.query.filter_by(
                    questid=question.qstid, userid=current_user.id
                ).first()
                user_vote = vote.value if vote else None

            questions_votes.append(
                {
                    "question": question,
                    "net_count": net_count,
                    "has_upvoted": user_vote == 1,
                    "has_downvoted": user_vote == -1,
                }
            )
            questions_with_votes = [serialize_questions(
                q["question"], q["net_count"], q["has_upvoted"], q['has_downvoted']) for q in questions_votes]
            r.setex(question_cache_key, 300, json.dumps(questions_with_votes))
            print("not from")

    return render_template(
        "question_display.html",
        group=questedgroup,
        user_groups=current_user.groups if current_user.is_authenticated else [],
        questions_with_votes=questions_with_votes,
    )


@app.route("/answerquestions/<int:qstid>", methods=["POST", "GET"])
def question_answers(qstid):
    question = Questions.query.get_or_404(qstid)

    question_vote_count = (
        db.session.query(func.sum(Votes.value)).filter_by(
            questid=qstid).scalar() or 0
    )

    prior_quest = Questions.query.filter_by(qstid=qstid).first()
    print(prior_quest)
    group = question.groupid

    form = Answer()
    if not question:
        flash("Question Does Not Exist")
        return redirect(url_for("home"))
    if form.validate_on_submit():

        answer = form.answerbody.data
        new_answer = Answers(
            anscontent=answer, senderid=current_user.id, groupid=group, qstid=qstid
        )
        db.session.add(new_answer)
        db.session.commit()
        return redirect(url_for("question_answers", qstid=qstid))

    question_has_upvoted = False
    question_has_downvoted = False
    if current_user.is_authenticated:
        user_vote = Votes.query.filter_by(
            questid=qstid, userid=current_user.id).first()
        if user_vote:
            question_has_upvoted = user_vote.value == 1
            question_has_downvoted = user_vote.value == -1

    answers = (
        Answers.query.filter_by(qstid=question.qstid)
        .order_by(Answers.anstime.desc())
        .all()
    )
    answer_hold = []
    answ_count = (
        db.session.query(
            Answers, func.coalesce(
                func.sum(Ansvotes.value), 0).label("net_count")
        )
        .outerjoin(Ansvotes, Ansvotes.answid == Answers.answid)
        .filter(Answers.qstid == question.qstid)
        .group_by(Answers.answid)
        .order_by(Answers.anstime.desc())  # Optional: newest first
        .all()
    )
    for answer, net_count in answ_count:
        user_vote = None
        if current_user.is_authenticated:
            vote = Ansvotes.query.filter_by(
                answid=answer.answid, userid=current_user.id
            ).first()
            user_vote = vote.value if vote else None
        answer_hold.append(
            {
                "answer": answer,
                "net_count": net_count,
                "has_upvoted": user_vote == 1,
                "has_downvoted": user_vote == -1,
            }
        )

    return render_template(
        "add_answer.html",
        question=question,
        question_vote_count=question_vote_count,
        question_has_upvoted=question_has_upvoted,
        question_has_downvoted=question_has_downvoted,
        answers=answers,
        form=form,
        answer_hold=answer_hold,
    )


@app.route("/upvote/<questid>", methods=["POST"])
def upvote(questid):
    qst = db.session.get(Questions, qstid=questid)
    new_vote = Votes.query.filter_by(
        userid=current_user.id, questid=questid).first()

    if new_vote:
        if new_vote.value == 1:
            db.session.delete(new_vote)
            has_upvoted = False
            has_downvoted = False
            qst.sender.points -= 1
        elif new_vote.value == -1:
            new_vote.value = 1
            has_upvoted = True
            has_downvoted = False
            qst.sender.points += 1

    else:
        db.session.add(Votes(value=1, userid=current_user.id, questid=questid))
        has_upvoted = True
        has_downvoted = False
        qst.sender.points += 1

    db.session.commit()

    net_count = (
        db.session.query(db.func.sum(Votes.value)).filter_by(
            questid=questid).scalar()
        or 0
    )

    return jsonify(
        {
            "net_count": net_count,
            "has_upvoted": has_upvoted,
            "has_downvoted": has_downvoted,
        }
    )


@app.route("/downvote/<questid>", methods=["POST"])
def downvote(questid):
    qst = Questions.query.filter_by(qstid=questid).first_or_404()
    new_vote = Votes.query.filter_by(
        userid=current_user.id, questid=questid).first()

    if new_vote:
        if new_vote.value == -1:
            db.session.delete(new_vote)
            has_upvoted = False
            has_downvoted = False
            qst.sender.points += 1
        elif new_vote.value == 1:
            new_vote.value = -1
            has_upvoted = False
            has_downvoted = True
            qst.sender.points -= 1
    else:
        db.session.add(
            Votes(value=-1, userid=current_user.id, questid=questid))
        has_upvoted = False
        has_downvoted = True
        qst.sender.points -= 1

    db.session.commit()

    net_count = (
        db.session.query(db.func.sum(Votes.value)).filter_by(
            questid=questid).scalar()
        or 0
    )

    return jsonify(
        {
            "net_count": net_count,
            "has_downvoted": has_downvoted,
            "has_upvoted": has_upvoted,
        }
    )


@app.route("/upvote/<questid>/<ansid>", methods=["POST"])
def upvoteanswer(questid, ansid):
    ans = Answers.query.filter_by(answid=ansid).first_or_404()
    new_vote = Ansvotes.query.filter_by(
        userid=current_user.id, answid=ansid).first()
    qst = db.session.query(Questions).get(questid)

    if new_vote:
        if new_vote.value == 1:
            db.session.delete(new_vote)
            has_upvoted = False
            has_downvoted = False
            ans.sender.points -= 1
        elif new_vote.value == -1:
            new_vote.value = 1
            has_upvoted = True
            has_downvoted = False
            ans.sender.points += 2

    else:
        db.session.add(
            Ansvotes(value=1, userid=current_user.id,
                     questid=qst.qstid, answid=ansid)
        )
        has_upvoted = True
        has_downvoted = False
        ans.sender.points += 2

    db.session.commit()

    net_count = (
        db.session.query(db.func.sum(Ansvotes.value)
                         ).filter_by(answid=ansid).scalar()
        or 0
    )
    time_diff = datetime.now() - qst.qsttime

    if (
        net_count >= 2
        and time_diff <= timedelta(hours=24)
    ):
        update_streak(qst.sender.id)
        qst.sender.points += 2
        db.session.commit()

    return jsonify(
        {
            "net_count": net_count,
            "has_upvoted": has_upvoted,
            "has_downvoted": has_downvoted,
        }
    )


@app.route("/downvote/<questid>/<ansid>", methods=["POST"])
def downvoteanswer(questid, ansid):

    ans = Answers.query.filter_by(answid=ansid).first_or_404()
    new_vote = Ansvotes.query.filter_by(
        userid=current_user.id, answid=ansid).first()
    qst = db.session.query(Questions).get(questid)

    if new_vote:
        if new_vote.value == -1:
            db.session.delete(new_vote)
            has_upvoted = False
            has_downvoted = False
            ans.sender.points += 1
        elif new_vote.value == 1:
            new_vote.value = -1
            has_upvoted = False
            has_downvoted = True
            ans.sender.points -= 1
    else:
        db.session.add(
            Ansvotes(value=-1, userid=current_user.id,
                     questid=qst.qstid, answid=ansid)
        )
        has_upvoted = False
        has_downvoted = True
        ans.sender.points -= 1

    db.session.commit()

    net_count = (
        db.session.query(db.func.sum(Ansvotes.value)
                         ).filter_by(answid=ansid).scalar()
        or 0
    )

    return jsonify(
        {
            "net_count": net_count,
            "has_downvoted": has_downvoted,
            "has_upvoted": has_upvoted,
        }
    )


@app.route("/add_tags/<int:groupid>")
def add_tags_page(groupid):
    cache_keys = "all_tags"
    cached = r.get(cache_keys)

    if cached:
        tags = json.loads(cached)
        print("Ts was cached")
    else:
        tags = Tags.query.all()
        tags = [{"tagid": t.tagid, "tag_name": t.tag_name} for t in tags]
        r.setex(cache_keys, 3000, json.dumps(tags))
    group = db.session.get(Groups, groupid)
    if not group:
        return "Group not found", 404

    # Fetch all tags for display

    return render_template("add_tags.html", group=group, tags=tags)


@app.route("/delete/<type>/<int:id>", methods=['POST'])
def delete(type, id):
    target = None
    qtid = None
    if type == 'qst':
        prev = db.session.query(Questions).get(id)
        prev.isdeleted = True
        prev.deletedwhen = datetime.now(timezone.utc)
        qtid = prev.qstid
    elif type == 'ans':
        prev = db.session.query(Answers).get(id)
        prev.isdeleted = True
        prev.deletedwhen = datetime.now(timezone.utc)
        qtid = prev.qstid

    else:
        flash("Page Does Not Exist")
        return redirect(url_for('home'))
    db.session.commit()
    return redirect(url_for('question_answers', qstid=qtid))


@app.route("/add_tag/<int:groupid>/<int:tagid>", methods=["POST"])
def addtag(groupid, tagid):

    group = db.session.get(Groups, groupid)
    tag = db.session.get(Tags, tagid)

    if not group or not tag:
        return {
            "status": "error",
            "action": "failed",
            "message": "Group or Tag not found",
        }, 404

    if tag in group.tags:
        group.tags.remove(tag)
        action = "removed"
    else:
        group.tags.append(tag)
        action = "added"

    db.session.commit()

    return {"status": "success", "action": action, "tag_name": tag.tag_name}


@app.route('/approve_answer/<int:answid>', methods=['POST'])
def approve_answer(answid):
    answer = db.session.get(Answers, answid)
    if answer:
        if answer.isapproved:
            answer.isapproved = False
            answer.sender.points -= 3
        else:
            answer.isapproved = True
            answer.sender.points += 3
            update_streak(answer.sender.id)
        db.session.commit()
    return redirect(url_for('question_answers', qstid=answer.qstid))


# Handle new messages
if __name__ == "__main__":
    with app.app_context():

        db.create_all()
    socketio.run(app, debug=True)
