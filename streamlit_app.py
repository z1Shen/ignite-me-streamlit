import json
import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account


# Securely connect to Firebase
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)


# Streamlit widgets to let a user create a new post
title = st.text_input("Post title")
url = st.text_input("Post url")
submit = st.button("Submit new post")


# Once the user has submitted, upload it to the database
if title and url and submit:
    doc_ref = db.collection("posts").document(title)
    doc_ref.set({
        "title": title,
        "url": url
    })


# And then render each post, using some light Markdown
posts_ref = db.collection("posts")
refs = posts_ref  # .where('title', '==', 'Apple')

for doc in refs.stream():
    post = doc.to_dict()
    title = post["title"]
    url = post["url"]

    st.subheader(f"Post: {title}")
    st.write(f":link: [{url}]({url})")
