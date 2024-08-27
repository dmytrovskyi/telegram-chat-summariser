from typing import List
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from telegram import Message
from google.cloud.firestore_v1.base_document import DocumentSnapshot

cred = credentials.Certificate("bich-f39db-firebase-adminsdk-ks0du-527cd9a2d6.json")
firebase_admin.initialize_app(cred)

db = firestore.client()


def convert_reply_message(message: Message):
    return {
        "from": message.from_user.to_dict(),
        "text": message.text,
    }


def save_message(message: Message):
    s_message = {
        "date": message.date,
        "from": message.from_user.to_dict(),
        "reply_to_message": convert_reply_message(message.reply_to_message) if message.reply_to_message is not None else '',
        "text": message.text,
    }
    db.collection("messages").add(s_message)


def get_last_messages(limit) -> List:
    snapshots = (
        db.collection("messages")
        .order_by("date", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    return list(map(lambda snap:snap.to_dict(), snapshots))
