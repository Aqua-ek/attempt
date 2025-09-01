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


def serialize_questions(q):
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
        "answer_length": len(q.answers),
        "group_name": q.group.name

    }


def serialize_answers(a):
    return {
        "answid": a.answid,
        "anstime": a.anstime.strftime("%Y-%m-%d %H:%M:%S"),
        "anscontent": a.anscontent,
        "senderid": a.senderid,
        "groupid": a.groupid,
        "isaprroved": a.isapproved,
        "isdeleted": a.isdeleted,
        "deletedwhen": a.deletedwhen.strftime("%b,%d,%Y") if a.deletedwhen else "",
        "displayed_answer": a.displayed_answer,
        "sender_name": a.sender.name,
        "group_name": a.group.name

    }
