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


# Set the default page config
st.set_page_config(
    layout="wide",
    page_title='IgniteMe.app'
)

# Load css
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Initialise session state variables
if 'toggle_dialog' not in st.session_state:
    st.session_state['toggle_dialog'] = False

if 'dialog_type' not in st.session_state:
    st.session_state['dialog_type'] = "initial"

session_states = ['goal_value', 'goal', 'user_message', "user_answer",
                  'user_goal', 'content', 'gpt_coach', 'gpt_response']
for state in session_states:
    if state not in st.session_state:
        st.session_state[state] = ""


# st.success(f"goal_value: {st.session_state['goal_value']}")

def update_firebase(collection, post):
    doc_ref = db.collection(collection).document()
    doc_ref.set(post)


def open_dialog():
    st.session_state['toggle_dialog'] = True
    st.session_state['goal_value'] = st.session_state['goal']


def initial_form():
    st.session_state['dialog_type'] = "follow-up"

    goal = st.session_state['goal_value']
    if goal and obstacles_1:
        st.success(
            f"You want to: {goal}, but: {obstacles_1}, {obstacles_2}, {obstacles_3}")

        # Talk with GPT

        # Prompts
        clarification = """
        Do you think I'm clear enough about my goal and obstacles? 
        Ask questions if there's anything you think I need to think about further. 
        The goal is to help me structure my thoughts and be clear about the challenges I have. 
        Make sure the thought process is MECE (Mutually Exclusive, Collectively Exhaustive). 
        Ask one clarification question at a time.
        
        Response format (remove all spaces and indentations):
        ```json
        {
            "success": false,
            "response": "put your questions or response here"
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
            "output": {
                "goal": "summarize my goal",
                "obastacles": [summarize the list of obastacles in the way that is actionable]
            }
            
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
            st.session_state['dialog_type'] = "initial"
            update_firebase("posts", gpt_response['output'])
        else:
            st.session_state['gpt_response'] = gpt_response['response']

    else:
        st.warning("Please fill all the fields")


modal = Modal(st.session_state['user_goal'], key="card_modal")
if modal.is_open():
    with modal.container():
        left, right = st.columns(2)
        with left:
            choice = st.radio("option_radio", st.session_state['content'],
                              label_visibility="collapsed")
        with right:
            st.subheader(choice)
            st.divider()
            st.caption(
                "Here's what others have said about this obstacle. Coming Soon!")
            # messages = [
            #     test for test in test_message if test['choice'] == choice][0]['data']
            # with st.container():
            #     for data in messages:
            #         name, message, space = st.columns([1, 5, 2])
            #         name.write(data['user'])
            #         message.write(data['message'])
            #         space.empty()

            #     input_text = st.text_input(
            #         "user_input", key="input", label_visibility="collapsed")


def card_popup(post):
    print(post)
    st.session_state['user_goal'] = post["goal"]
    st.session_state['content'] = post["obstacles"]
    modal.open()


# Navbar
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
        if st.session_state['dialog_type'] == "initial":
            st.write("What stops you from achieving your goal?")
            obstacles_1 = st.text_input("obs_1", placeholder="But...",
                                        label_visibility="collapsed")
            obstacles_2 = st.text_input("obs_2", value="", placeholder="And also...",
                                        label_visibility="collapsed")
            obstacles_3 = st.text_input("obs_3", value="", placeholder="Here is one more...",
                                        label_visibility="collapsed")
            st.button(
                "Submit", on_click=initial_form)
        else:
            st.write(st.session_state['gpt_response'])
            answer = st.text_input(
                "answer", key="user_answer", label_visibility="collapsed")
            st.button("Submit", on_click=follow_up_form)
    else:
        input.text_input("What is your goal today", placeholder="I want to ...",

                         key="goal", max_chars=50, on_change=open_dialog)
navbar.divider()

# Chatbot
if 'generated' not in st.session_state:
    st.session_state['generated'] = []

if 'past' not in st.session_state:
    st.session_state['past'] = []

test_message = [
    {
        "choice": "I want to make money",
        "data": [
            {"user": "John", "message": "I have a great business idea"},
            {"user": "Ted", "message": "Count me in!"},
            {"user": "Eddie", "message": "Let's start a startup together"},
            {"user": "John", "message": "I'm excited about the potential"},
            {"user": "Ted", "message": "Me too, we can make it happen"},
            {"user": "Eddie", "message": "Absolutely, let's go for it"},
            {"user": "G", "message": "This is a long message to test the length of the message"},
        ]
    },
    {
        "choice": "I'm tired",
        "data": [
            {"user": "John", "message": "I need a good night's sleep"},
            {"user": "Ted", "message": "I'm exhausted too"},
            {"user": "Eddie", "message": "Let's take a break and recharge"},
            {"user": "John", "message": "I agree, we've been working non-stop"},
            {"user": "Ted", "message": "We deserve some rest"},
            {"user": "Eddie", "message": "Absolutely, let's relax for a while"},
            {"user": "G", "message": "This is a long message to test the length of the message"},

        ]
    },
    {
        "choice": "I'm hungry",
        "data": [
            {"user": "John", "message": "I'm craving pizza"},
            {"user": "Ted", "message": "Pizza sounds delicious"},
            {"user": "Eddie", "message": "Let's order some right away"},
            {"user": "John", "message": "I can't resist a good pizza"},
            {"user": "Ted", "message": "Me neither, let's satisfy our hunger"},
            {"user": "Eddie", "message": "Absolutely, pizza party it is!"},
            {"user": "G", "message": "This is a long message to test the length of the message"},
        ]
    },
    {
        "choice": "I'm sleepy",
        "data": [
            {"user": "John", "message": "I need a comfortable bed"},
            {"user": "Ted", "message": "Let's take a quick nap"},
            {"user": "Eddie", "message": "I wish I could sleep right now"},
            {"user": "John", "message": "I feel like a power nap would help"},
            {"user": "Ted", "message": "Agreed, a short rest can boost productivity"},
            {"user": "Eddie", "message": "I can barely keep my eyes open"},
            {"user": "G", "message": "This is a long message to test the length of the message"},
        ]
    }
]


# # Tabs of Categories
# categories = ["For You", "Following", "Your Posts"]
# tab_list = st.tabs(categories)
# for tab, category in zip(tab_list, categories):


# Grid of Card
items_per_col = 4
post_refs = db.collection("posts")
docs = post_refs.stream()

col_list = st.columns(items_per_col)
for doc, col, i in zip(docs, col_list, range(items_per_col)):
    with col:
        post = doc.to_dict()
        st.header(post["goal"])
        st.button('View', key=i, on_click=card_popup, args=(post,))
        st.divider()
