import json
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st
from streamlit_modal import Modal
from streamlit_card import card
from streamlit_chat import message


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

if 'goal_value' not in st.session_state:
    st.session_state['goal_value'] = ""

if 'goal' not in st.session_state:
    st.session_state['goal'] = ""

if 'user_message' not in st.session_state:
    st.session_state['user_message'] = ""

# st.success(f"goal_value: {st.session_state['goal_value']}")


def open_dialog():
    st.session_state['toggle_dialog'] = True
    st.session_state['goal_value'] = st.session_state['goal']


def initial_form():
    st.session_state['dialog_type'] = "follow-up"
    goal = st.session_state['goal_value']
    # print(goal, obstacles_1, obstacles_2, obstacles_3)
    if goal and obstacles_1 and obstacles_2 and obstacles_3:
        st.success(
            f"Your goal is: {goal} Your obstacles are: {obstacles_1}, {obstacles_2}, {obstacles_3}")
    else:
        st.warning("Please fill all the fields")


def follow_up_form():
    st.session_state['dialog_type'] = "initial"
    st.session_state['toggle_dialog'] = False
    if answer:
        st.success(f"answer: {answer}")
    else:
        st.warning("Please fill all the fields")


def card_popup():
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
            gpt_question = "I have a clarification question for you. What do you mean by ... "
            st.write(gpt_question)
            answer = st.text_input(
                "answer", label_visibility="collapsed")
            st.button("Submit", on_click=follow_up_form)
    else:
        input.text_input("What is your goal today", placeholder="I want to ...",

                         key="goal", max_chars=50, on_change=open_dialog)


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


user_goal = ["I want to make money", "I'm tired", "I'm hungry", "I'm sleepy"]


# Card Popup
modal = Modal(user_goal[0], key="card_modal")
if modal.is_open():
    with modal.container():
        left, right = st.columns([1, 2])
        with left:
            option = user_goal
            choice = st.radio("option_radio", option,
                              label_visibility="collapsed")
        with right:
            st.subheader(choice)
            st.divider()
            messages = [
                test for test in test_message if test['choice'] == choice][0]['data']
            with st.container():
                for data in messages:
                    name, message, space = st.columns([1, 5, 2])
                    name.write(data['user'])
                    message.write(data['message'])
                    space.empty()

                input_text = st.text_input(
                    "user_input", key="input", label_visibility="collapsed")


# Tabs of Categories
categories = ["For You", "Following", "Your Posts"]
grid_size = [2, 3]

tab_list = st.tabs(categories)
for tab, category in zip(tab_list, categories):

    # Grid of Card
    grid = tab.container()
    for i in range(grid_size[0]):
        col_list = grid.columns(grid_size[1])
        col_len = len(col_list)
        for col, n in zip(col_list, range(col_len)):
            with col:
                clicked_card = card(
                    title=category,
                    text=str(n) + str(i),
                    image="",
                )
                if clicked_card:
                    card_popup()


# # Once the user has submitted, upload it to the database
# if title and url and submit:
#     doc_ref = db.collection("posts").document(title)
#     doc_ref.set({
#         "title": title,
#         "url": url
#     })


# # And then render each post, using some light Markdown
# posts_ref = db.collection("posts")
# refs = posts_ref  # .where('title', '==', 'Apple')

# for doc in refs.stream():
#     post = doc.to_dict()
#     title = post["title"]
#     url = post["url"]

#     st.subheader(f"Post: {title}")
#     st.write(f":link: [{url}]({url})")
