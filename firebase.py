#!./.venv/bin/python

from typing import List
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from telegram import Message
from google.cloud.firestore_v1.base_document import DocumentSnapshot

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def convert_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }


def convert_reply_message(message: Message):
    return {"from": convert_user(message.from_user), "text": message.text}


def save_message(message: Message, image_description: str):
    if message == None:
        return
    
    message_text = (
        message.text
        if message.text != None
        else message.caption if message.caption != None else image_description
    )
    s_message = {
        "message_id": message.message_id,
        "date": message.date,
        "from": convert_user(message.from_user),
        "reply_to_message": (
            convert_reply_message(message.reply_to_message)
            if message.reply_to_message is not None
            else ""
        ),
        "text": message_text,
    }

    if image_description != None and len(image_description) > 0:
        s_message["attachment_description"] = image_description

    db.collection(str(message.chat.id)).add(s_message)


def get_last_messages(chat_id, limit) -> List:
    snapshots = (
        db.collection(chat_id)
        .order_by("date", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    result = list(map(lambda snap: snap.to_dict(), snapshots))
    result.reverse()
    return result
