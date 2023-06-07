import json
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st
from streamlit_modal import Modal


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


# Pop up modal
def popup():
    modal.open()


# Navbar
navbar = st.container()
logo, empty1, input, empty2, login = navbar.columns(
    [1, 1, 3, 1, 1], gap="large")
logo.image("./public/logo.png", use_column_width=True)
empty1.empty()
goal = input.text_input("What do you want to achieve today?",
                        placeholder="I want to ...", max_chars=50, on_change=popup)
empty2.empty()
login.button("Login")

# Tabs of Categories
categories = ["Made for you", "Your Following", "Your Posts"]
grid_size = [4, 3]

tab_list = st.tabs(categories)
for tab, category in zip(tab_list, categories):
    grid = tab.container()
    # Grid of Card
    for i in range(grid_size[0]):
        col_list = grid.columns(grid_size[1])
        col_len = len(col_list)
        for col, n in zip(col_list, range(col_len)):
            card = col.container()
            card.write(category)
            card.write(str(n) + str(i))

modal = Modal("Start your dream today", key="modal")
if modal.is_open():
    with modal.container():
        st.write("Your goal is to")
        st.write(goal)

        st.write("What stops you from achieving your goal?")
        obstacles = st.text_area("Obstacles", placeholder="But...",
                                 label_visibility="collapsed")
