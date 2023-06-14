import streamlit as st
from streamlit_modal import Modal


def post_modal():
    modal = Modal(st.session_state['user_goal'],
                  key=st.session_state['post_id'])
    if modal.is_open():
        with modal.container():
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
    return modal


def auth_modal():
    modal = Modal('Login', key='login')
    if modal.is_open():
        with modal.container():
            auth_choice = st.radio('Signup or Login', ('Login', 'Signup'))
            if auth_choice == 'Signup':
                user_name = st.text_input('Please input your user name')
                email = st.text_input('Please enter your email address')
                password = st.text_input(
                    'Please enter your password', type='password')
                st.session_state['user_info'] = {
                    'user_name': user_name, 'email': email, 'password': password}
            else:
                email = st.text_input('Please enter your email address')
                password = st.text_input(
                    'Please enter your password', type='password')
                st.session_state['user_info'] = {
                    'email': email, 'password': password}

            if auth_choice == 'Signup':
                st.button('Signup', on_click=signup())
            else:
                st.button('Login', on_click=login())
    return modal


# auth_modal = auth_modal()
# post_modal = post_modal()
