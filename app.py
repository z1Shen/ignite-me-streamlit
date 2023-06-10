import json
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st
from streamlit_modal import Modal
from streamlit_card import card
from streamlit_chat import message
from gpt_api import GPT_API


# Securely connect to Firebase
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)
batch = db.batch()


# Set the default page config and load css
st.set_page_config(
    layout="wide",
    page_title='IgniteMe.app'
)

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Initialise session state variables
session_states = ['goal_value', 'goal', 'user_message', "user_answer",
                  'user_goal', 'content', 'gpt_coach', 'gpt_response',
                  'obstacles_1', 'obstacles_2', 'obstacles_3', 'dialog_type', 'post_id', 'user_input', 'user_name', 'obstacle_id', 'obstacle_value']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = ""

session_states = ['expand_post', 'toggle_dialog']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = False


# Define Components


def update_firebase(collection, data):
    doc_ref = db.collection(collection).document()
    doc_ref.set(data)


def stream_firebase(collection):
    post_refs = db.collection(collection)
    docs = post_refs.stream()
    return docs


def open_dialog():
    st.session_state['toggle_dialog'] = True
    st.session_state['goal_value'] = st.session_state['goal']


def initial_form():
    st.session_state['dialog_type'] = "follow-up"

    goal = st.session_state['goal_value']
    obstacles_1 = st.session_state['obstacles_1']
    obstacles_2 = st.session_state['obstacles_2']
    obstacles_3 = st.session_state['obstacles_3']

    if goal and obstacles_1:
        # st.success(
        #     f"You want to: {goal}, but: {obstacles_1}, {obstacles_2}, {obstacles_3}")

        # Talk with GPT
        clarification = """
        Do you think I'm clear enough about my goal and obstacles? 
        Ask questions if there's anything you think I need to think about further. 
        The goal is to help me structure my thoughts and be clear about the challenges I have. 
        Make sure the thought process is MECE (Mutually Exclusive, Collectively Exhaustive). 
        Ask one clarification question at a time.
        
        Response format (remove all spaces and indentations):
        ```json
        {
            "success": false, # it has to be false for this form
            "response": "put your questions or response here, in one sentence",
        }
        ```
        """

        user_input = "My goal is: {}, but I can't because:\n 1. {}\n 2.{}\n 3. {}".format(
            goal, obstacles_1, obstacles_2, obstacles_3)

        # Initialize GPT
        gpt_coach = GPT_API()
        gpt_response = gpt_coach.chat(user_input + clarification)
        st.session_state['gpt_coach'] = gpt_coach

        gpt_response = json.loads(gpt_response)
        print(gpt_response)
        st.session_state['gpt_response'] = gpt_response['response']

    else:
        st.warning("Please fill all the fields")


def follow_up_form():
    answer = st.session_state['user_answer']
    if answer:

        # GPT
        instructions = """
        If you've fully understood my goal and obstacles, show me the summary and ask me for confirmation.
        If I confirm, output the summary
        
        Response format (remove all spaces and indentations):
        ```json
        {
            "success": false, # use true after I confirm the summary,
            "response": "put your questions or response here"",
            "goal": 
                {"content: "goal"} # when success is true, output the summary of my goal"
            "obstacles": [
                {"content": "obstacles #1"}, # # when success is true, output the summary of obastacles in list
                {"content": "obstacles #2"}
                ...
            ]
        }
        ```
        """

        gpt_coach = st.session_state['gpt_coach']
        gpt_response = gpt_coach.chat(answer + instructions)
        st.session_state['gpt_coach'] = gpt_coach

        gpt_response = json.loads(gpt_response)
        print(gpt_response)

        if gpt_response['success']:
            st.session_state['toggle_dialog'] = False
            st.session_state['dialog_type'] = ""

            user_ref = db.collection('posts').document()
            gpt_response['goal']['user_name'] = st.session_state['user_name']
            batch.set(user_ref, gpt_response['goal'])
            for obstacle_value in gpt_response['obstacles']:
                subcollection_ref = user_ref.collection('obstacles').document()
                batch.set(subcollection_ref, obstacle_value)
            batch.commit()
        else:
            st.session_state['gpt_response'] = gpt_response['response']
            st.session_state['user_answer'] = ""

    else:
        st.warning("Please fill all the fields")


def card_grid(items_per_col):
    docs = stream_firebase("posts")
    col_list = st.columns(items_per_col)
    for doc, col, i in zip(docs, col_list, range(items_per_col)):
        with col:
            post = doc.to_dict()
            post['id'] = doc.id

            st.header(post["content"])
            st.caption(post["user_name"])
            clicked = st.button('View', key=i)
            if clicked:
                st.session_state['user_goal'] = post["content"]
                st.session_state['obstacle_value'] = ''
                st.session_state['post_id'] = post['id']
                st.session_state['expand_post'] = True
            st.divider()


def navbar():
    if len(st.session_state['user_message']) > 0:
        st.write(st.session_state['user_message'])
    navbar = st.container()
    logo, left, input, right, login = navbar.columns([1, 1, 3, 1, 1])
    logo.image("./public/logo.png", use_column_width=True)
    login.button("Login")
    left.empty()
    right.empty()

    with input.container():
        if st.session_state['toggle_dialog']:
            if st.session_state['dialog_type'] == "":
                st.write("What stops you from achieving your goal?")
                st.text_input("obstacles_1", key="obstacles_1", placeholder="But...",
                              label_visibility="collapsed")
                st.text_input("obstacles_2", key="obstacles_2", value="", placeholder="And also...",
                              label_visibility="collapsed")
                st.text_input("obstacles_3", key="obstacles_3", value="", placeholder="Here is one more...",
                              label_visibility="collapsed")
                st.button(
                    "Submit", on_click=initial_form)
            else:
                st.write(st.session_state['gpt_response'])
                st.text_input(
                    "answer", key="user_answer", label_visibility="collapsed")
                st.button("Submit", on_click=follow_up_form)
        else:
            input.text_input("What is your goal today", placeholder="I want to ...",

                             key="goal", max_chars=50, on_change=open_dialog)
    navbar.divider()


def submit_message():
    collection = "posts/{}/obstacles/{}/messages".format(
        st.session_state['post_id'], st.session_state['obstacle_id'])
    data = {"content": st.session_state['user_input'],
            "user": st.session_state['user_name']}
    update_firebase(collection, data)


def post_expander():
    if st.session_state['post_id']:
        with st.expander(st.session_state['user_goal'], expanded=st.session_state['expand_post']):
            left, right = st.columns(2)
            with left:
                collection = "posts/{}/obstacles".format(
                    st.session_state['post_id'])
                obstacles = stream_firebase(collection)
                for obstacle in obstacles:
                    data = obstacle.to_dict()
                    clicked = st.button(data['content'])
                    if clicked:
                        st.session_state['obstacle_value'] = data['content']
                        st.session_state['obstacle_id'] = obstacle.id

            with right:
                if st.session_state['obstacle_value']:
                    st.subheader(st.session_state['obstacle_value'])
                    st.divider()
                    collection = "posts/{}/obstacles/{}/messages".format(
                        st.session_state['post_id'], st.session_state['obstacle_id'])
                    docs = stream_firebase(collection)
                    for doc in docs:
                        data = doc.to_dict()

                        name, content, space = st.columns([2, 5, 2])
                        name.write(data['user'])
                        content.write(data['content'])
                        space.empty()

                    st.text_input(
                        "user_input", key="user_input", label_visibility="collapsed")
                    st.button("Submit", key="message_button",
                              on_click=submit_message)
                else:
                    st.empty()


login = False
if login:
    st.session_state['user_name'] = "123"
else:
    st.session_state['user_name'] = "Anonymous"

navbar()
card_grid(3)
post_expander()


# # Tabs of Categories
# categories = ["For You", "Following", "Your Posts"]
# tab_list = st.tabs(categories)
# for tab, category in zip(tab_list, categories):
