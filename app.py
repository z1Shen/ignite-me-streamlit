import json
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st
# from streamlit_modal import Modal
from gpt_api import GPT_API
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore


# Securely connect to Firebase
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["textkey"])
    # creds = service_account.Credentials.from_service_account_info(key_dict)
    cred = credentials.Certificate("firestore-key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()
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
                  'obstacles_1', 'obstacles_2', 'obstacles_3', 'dialog_type', 'post_id', 'user_input', 'obstacle_id', 'obstacle_value', 'user_info', 'auth_info', 'gpt_response']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = ""

session_states = ['expand_post', 'toggle_dialog', 'authentication', 'post_id']
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


def signup():
    auth_info = st.session_state['auth_info']
    try:
        user = auth.create_user(email=auth_info['email'])

        user_info = {
            "user_email": auth_info['email'], "user_name": auth_info['user_name']}
        user_ref = db.collection('users').document(user.uid)
        user_ref.set(user_info)
        st.session_state['user_info'] = user_info
        st.success('Welcome! ' + user_info['user_name'])
        st.session_state['authentication'] = False
        if st.session_state['gpt_response']:
            post_goal()
    except auth.EmailAlreadyExistsError:
        st.sidebar.error(
            'Email already exists. Please try a different email.')
    except Exception as e:
        st.sidebar.error(
            'Account creation failed. Please try again later.')
        st.write(e)


def login():
    auth_info = st.session_state['auth_info']
    try:
        user = auth.get_user_by_email(auth_info['email'])
        user_ref = db.collection('users').document(user.uid)
        user_info = user_ref.get().to_dict()
        st.session_state['user_info'] = user_info
        st.session_state['user_name'] = user_info['user_name']
        st.success('Welcome back! ' + user_info['user_name'])
        st.session_state['authentication'] = False
        if st.session_state['gpt_response']:
            post_goal()
    except auth.UserNotFoundError:
        # st.sidebar.error('Invalid email or password. Please try again.')
        signup()


def logout():
    st.session_state['user_info'] = ""


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

        print(gpt_response)
        gpt_response = json.loads(gpt_response)
        st.session_state['gpt_response'] = gpt_response['response']

    else:
        st.warning("Please fill all the fields")


def post_goal():
    gpt_response = st.session_state['gpt_response']
    gpt_response['goal']['user_info'] = st.session_state['user_info']
    user_ref = db.collection('posts').document()
    batch.set(user_ref, gpt_response['goal'])
    for obstacle_value in gpt_response['obstacles']:
        subcollection_ref = user_ref.collection(
            'obstacles').document()
        batch.set(subcollection_ref, obstacle_value)
    batch.commit()
    st.session_state['gpt_response'] = ""


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

        print(gpt_response)
        gpt_response = json.loads(gpt_response)

        if gpt_response['success']:
            st.session_state['gpt_response'] = gpt_response
            st.session_state['toggle_dialog'] = False
            st.session_state['dialog_type'] = ''

            if st.session_state['user_info']:
                post_goal()
            else:
                st.session_state['authentication'] = True
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
            st.caption(post['user_info']["user_name"])
            clicked = st.button('View', key=i)
            if clicked:
                st.session_state['user_goal'] = post["content"]
                st.session_state['obstacle_value'] = ''
                st.session_state['post_id'] = post['id']
                st.session_state['expand_post'] = True
            st.divider()


def navbar():
    navbar = st.container()
    logo, left, center, right, button = navbar.columns([1, 1, 3, 1, 1])
    logo.image("./public/logo.png", use_column_width=True)
    left.empty()
    right.empty()

    with button:
        if not st.session_state['user_info']:
            if not st.session_state['authentication']:
                clicked = button.button('Account')
                if clicked:
                    st.session_state['authentication'] = True
            else:
                button.button('Sign in', on_click=login)
        else:
            button.button(
                st.session_state['user_info']['user_name'], on_click=logout)

    with center.container():
        if st.session_state['authentication']:
            authenticate()
        else:
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
                center.text_input("What is your goal today", placeholder="I want to ...",
                                  key="goal", max_chars=50, on_change=open_dialog)
    navbar.divider()


def submit_message():
    collection = "posts/{}/obstacles/{}/messages".format(
        st.session_state['post_id'], st.session_state['obstacle_id'])
    data = {"content": st.session_state['user_input'],
            "user_info": st.session_state['user_info']}
    update_firebase(collection, data)
    st.session_state['user_input'] = ""


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
                        name.write(data['user_info']['user_name'])
                        content.write(data['content'])
                        space.empty()

                    st.text_input(
                        "user_input", key="user_input", label_visibility="collapsed")
                    st.button("Submit", key="message_button",
                              on_click=submit_message)
                else:
                    st.empty()


def authenticate():
    left, right = st.columns(2)
    with left:
        user_name = st.text_input('Please input your user name')
    with right:
        email = st.text_input('Please enter your email address')
    st.session_state['auth_info'] = {'user_name': user_name, 'email': email}


navbar()
card_grid(3)
post_expander()


# # Tabs of Categories
# categories = ["For You", "Following", "Your Posts"]
# tab_list = st.tabs(categories)
# for tab, category in zip(tab_list, categories):
