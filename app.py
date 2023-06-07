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

# load css
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


if 'dialog_expanded' not in st.session_state:
    st.session_state['dialog_expanded'] = False

if 'form_type' not in st.session_state:
    st.session_state['form_type'] = "inital"


def open_dialog():
    st.session_state['dialog_expanded'] = True


def clear_answer():
    st.session_state.answer = ""


# Navbar
navbar = st.container()
logo, empty1, input, empty2, login = navbar.columns(
    [1, 1, 3, 1, 1], gap="large")
logo.image("./public/logo.png", use_column_width=True)
empty1.empty()
goal = input.text_input("What is your goal today",
                        placeholder="I want to ...", key="goal", max_chars=50, on_change=open_dialog)
empty2.empty()
login.button("Login")

# Tabs of Categories
categories = ["Made for you", "Your Following", "Your Posts"]
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
                    st.write("clicked")


# Open Dialog
# goal_setting_modal = Modal(goal+" today!", key="goal-setting-modal")


with st.expander('dialog_expander', expanded=st.session_state['dialog_expanded']):
    if form_type == "inital":
        st.write("What stops you from achieving your goal?")
        obstacles_1 = st.text_input("Obstacles_1", placeholder="But...",
                                    label_visibility="collapsed")
        obstacles_2 = st.text_input("Obstacles_2", placeholder="And also...",
                                    label_visibility="collapsed")
        obstacles_3 = st.text_input("Obstacles_3", placeholder="Here is one more...",
                                    label_visibility="collapsed")

        # Every form must have a submit button.
        submitted = st.button("Submit")
        if submitted:
            st.write("goal: ", goal, "obstacles_1: ", obstacles_1,
                     "obstacles_2: ", obstacles_2, "obstacles_3: ", obstacles_3)
            form_type = "Submitted"
    else:
        gpt_question = "hello"
        st.write(gpt_question)
        answer = st.text_input(
            "answer", label_visibility="collapsed")
        submitted = st.button("Submit")


# if goal_setting_modal.is_open():
#     with goal_setting_modal.container():
#         if form_type == "inital":
#             st.write("What stops you from achieving your goal?")
#             obstacles_1 = st.text_input("Obstacles_1", placeholder="But...",
#                                         label_visibility="collapsed")
#             obstacles_2 = st.text_input("Obstacles_2", placeholder="And also...",
#                                         label_visibility="collapsed")
#             obstacles_3 = st.text_input("Obstacles_3", placeholder="Here is one more...",
#                                         label_visibility="collapsed")

#             # Every form must have a submit button.
#             submitted = st.button("Submit")
#             if submitted:
#                 st.write("goal: ", goal, "obstacles_1: ", obstacles_1,
#                          "obstacles_2: ", obstacles_2, "obstacles_3: ", obstacles_3)
#                 form_type = "Submitted"
#         else:
#             gpt_question = "hello"
#             st.write(gpt_question)
#             answer = st.text_input(
#                 "answer", label_visibility="collapsed")
#             submitted = st.button("Submit")
