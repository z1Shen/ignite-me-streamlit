import json
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from gpt_api import GPT_API
from sign_in_with_email_and_password import sign_in_with_email_and_password
from send_email_verification_link import send_email_verification_link


# Securely connect to Firebase
key_dict = json.loads(st.secrets["textkey"])
if not firebase_admin._apps:
    cred = credentials.Certificate(key_dict)
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
session_states = ['goal_input', 'message_input', "answer_input",
                  'gpt_coach', 'gpt_response',
                  'user_info', 'post', 'obstacle']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = ""

session_states = ['toggle_post', 'toggle_dialog',
                  'toggle_gpt', 'toggle_login', 'toggle_signup']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = False

# Define Components


def update_firebase(collection, data):
    doc_ref = db.collection(collection).document()
    doc_ref.set(data)


def stream_firebase(collection, limit=False):
    post_refs = db.collection(collection)
    if limit:
        post_refs = post_refs.limit(limit)
    docs = post_refs.stream()
    return docs


def signup():
    auth_info = st.session_state['user_info']
    try:
        user = auth.create_user(**auth_info)
        # send_email_verification_link(auth_info['email'])
        # st.info('Please check your email to verify your account.')
        user_ref = db.collection('users').document(user.uid)
        user_ref.set(auth_info)

        st.success('Welcome! ' + auth_info['display_name'])
        st.session_state['toggle_login'] = False
        st.session_state['toggle_signup'] = False
        if st.session_state['gpt_response']:
            submit_goal()
    except auth.EmailAlreadyExistsError:
        st.session_state['user_info'] = ''
        st.sidebar.error(
            'Email already exists. Please try a different email.')
    except Exception as e:
        st.session_state['user_info'] = ''
        st.sidebar.error(
            'Account creation failed. Please try again later.')
        st.write(e)


def login():
    auth_info = st.session_state['user_info']
    try:
        # user = auth.get_user_by_email(auth_info['email'])
        login_res = sign_in_with_email_and_password(**auth_info)
        if 'registered' in login_res.keys():
            user_ref = db.collection('users').document(login_res['localId'])
            auth_info = user_ref.get().to_dict()

            if 'user_name' in auth_info.keys():  # todo: remove this
                auth_info['display_name'] = auth_info['user_name']
            st.session_state['user_info']['display_name'] = auth_info['display_name']
            st.success('Welcome back! ' + auth_info['display_name'])
            st.session_state['toggle_login'] = False
            st.session_state['toggle_signup'] = False
            if st.session_state['gpt_response']:
                submit_goal()
        else:
            error_message = login_res['error']['message']
            st.session_state['user_info'] = ''
            if error_message == "INVALID_PASSWORD":
                st.error(login_res['error']['message'])
            else:
                st.session_state['toggle_signup'] = True
    except auth.UserNotFoundError:
        signup()


def logout():
    st.session_state['user_info'] = ""


def open_dialog():
    st.session_state['toggle_dialog'] = True
    st.session_state['goal_input'] = st.session_state['goal_input']


def initial_dialog(goal):
    st.session_state['toggle_gpt'] = True
    obs = [st.session_state[o] for o in ['obs_1', 'obs_2', 'obs_3']]

    if goal and obs[0]:
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
        user_input = f"My goal is: {goal}, but I can't because:{obs}"
        st.info(user_input)

        # Initialize GPT
        gpt_coach = GPT_API()
        st.session_state['gpt_coach'] = gpt_coach

        gpt_response = gpt_coach.chat(user_input + clarification)
        print(gpt_response)
        gpt_response = json.loads(gpt_response)
        st.session_state['gpt_response'] = gpt_response['response']

    else:
        st.warning("Please fill all the fields")


def follow_up_form():
    answer = st.session_state['answer_input']
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
            st.session_state['toggle_gpt'] = False

            if st.session_state['user_info']:
                submit_goal()
            else:
                st.session_state['toggle_login'] = True
        else:
            st.session_state['gpt_response'] = gpt_response['response']
            st.session_state['answer_input'] = ""

    else:
        st.warning("Please fill all the fields")


def submit_goal():
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


def submit_message(collection):
    if st.session_state['user_info']:
        data = {"content": st.session_state['message_input'],
                "user_info": st.session_state['user_info']}
        update_firebase(collection, data)
        st.session_state['message_input'] = ''
    else:
        st.session_state['toggle_login'] = True
        st.warning("Please Sign In First")


def card_grid(n_cols, n_rows=10):
    docs = stream_firebase("posts")

    rows = [st.container() for _ in range(n_rows)]
    cols_per_row = [r.columns(n_cols) for r in rows]
    cols = [column for row in cols_per_row for column in row]

    for i, doc in enumerate(docs):
        with cols[i].container():
            post = doc.to_dict()
            post['id'] = doc.id

            st.header(post["content"])
            if 'user_name' in post['user_info'].keys():  # todo: remove this
                post['user_info']['display_name'] = post['user_info']['user_name']
            st.caption(post['user_info']["display_name"])
            clicked = st.button('View', key=i)
            if clicked:
                st.session_state['post'] = post
                st.session_state['toggle_post'] = True
            st.divider()


def navbar():
    navbar = st.container()
    logo, left, center, right, button = navbar.columns([1, 1, 3, 1, 1])
    logo.image("./public/logo.png", use_column_width=True)
    left.empty()
    right.empty()

    with button:
        user_info = st.session_state['user_info']
        if user_info and 'display_name' in user_info.keys():
            col1, col2 = button.columns([1, 1])
            col1.header(st.session_state['user_info']['display_name'])
            col2.button(
                'Logout', on_click=logout)
        else:
            if st.session_state['toggle_signup']:
                button.button('Signup', on_click=signup)
            elif st.session_state['toggle_login']:
                button.button('Login', on_click=login)
            else:
                clicked = button.button('Login')  # default button
                if clicked:
                    st.session_state['toggle_login'] = True

    with center.container():
        if st.session_state['toggle_login']:
            auth_form()
        else:
            if st.session_state['toggle_dialog']:
                if not st.session_state['toggle_gpt']:
                    initial_form()
                elif st.session_state['gpt_response']:
                    st.write(st.session_state['gpt_response'])
                    st.text_input(
                        "answer", key="answer_input", label_visibility="collapsed")
                    st.button("Submit", on_click=follow_up_form)
                else:
                    pass
            else:
                center.text_input("What is your goal today", placeholder="I want to ...",
                                  key="goal_input", max_chars=50, on_change=open_dialog)
    navbar.divider()


def post_expander():
    left, right = st.columns(2)
    post = st.session_state['post']
    with left:
        collection = f"posts/{post['id']}/obstacles"
        obstacles = stream_firebase(collection)
        st.header(post['content'])
        for obstacle in obstacles:
            data = obstacle.to_dict()
            data['id'] = obstacle.id
            clicked_obstacle = st.button(data['content'])
            if clicked_obstacle:
                st.session_state['obstacle'] = data

    with right:
        if st.session_state['obstacle']:
            obstacle = st.session_state['obstacle']
            st.subheader(obstacle['content'])
            st.divider()
            collection = f"posts/{post['id']}/obstacles/{obstacle['id']}/messages"
            docs = stream_firebase(collection)
            for doc in docs:
                post = doc.to_dict()
                name, content, space = st.columns([2, 5, 2])
                if 'user_name' in post['user_info'].keys():  # todo: remove this
                    post['user_info']['display_name'] = post['user_info']['user_name']
                name.write(post['user_info']['display_name'])
                content.write(post['content'])
                space.empty()

            st.text_input(
                "message_input", key="message_input", label_visibility="collapsed")
            st.button("Submit", key="message_button",
                      on_click=submit_message, args=(collection, ))
        else:
            st.empty()
    st.divider()
    clicked_close = st.button("Close", type='primary')
    if clicked_close:
        st.session_state['toggle_post'] = False
        st.session_state['post'] = ''
        st.session_state['obstacle'] = ''


def auth_form():
    left, right = st.columns(2)
    with left:
        email = st.text_input('Please enter your email address')
    with right:
        password = st.text_input('Please input your password', type='password')
    st.session_state['user_info'] = {'email': email, 'password': password}
    if st.session_state['toggle_signup']:
        display_name = st.text_input('Please enter your user name')
        st.session_state['user_info']['display_name'] = display_name


def initial_form():
    goal = st.session_state['goal_input']
    with st.form(key="initial_form"):
        st.write("What stops you from achieving your goal?")
        st.text_input("obs_1", key="obs_1", placeholder="But...",
                      label_visibility="collapsed")
        st.text_input("obs2", key="obs_2", placeholder="And also...",
                      label_visibility="collapsed")
        st.text_input("obs3", key="obs_3", placeholder="Here is one more...",
                      label_visibility="collapsed")
        st.form_submit_button(
            "Submit", on_click=initial_dialog, args=(goal, ))


navbar()
if st.session_state['toggle_post']:
    post_expander()
else:
    card_grid(3)


# # Tabs of Categories
# categories = ["For You", "Following", "Your Posts"]
# tab_list = st.tabs(categories)
# for tab, category in zip(tab_list, categories):
