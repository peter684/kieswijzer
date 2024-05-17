from time import sleep

import streamlit as st
from pandas import DataFrame
from streamlit import session_state as state

import authenticate as auth
import constants as cs
import sidebar


def run_script():
    sidebar.compose_sidebar(show_legend=False, show_choices=False)
    users = state[cs.config]['credentials']['usernames']
    df_credentials = DataFrame(users).transpose()
    st.header('***Edit user information***')
    with st.form(key='users_form',
                 border=True):
        curr_editor_key = f'users_editor{state[cs.ctr]}'
        st.data_editor(key=curr_editor_key,
                       data=df_credentials,
                       num_rows='dynamic'
                       )
        submitted = st.form_submit_button("Commit changes")
        if submitted:
            for row_nr, row in state[curr_editor_key]['edited_rows'].items():
                try:
                    for k, v in row.items():
                        username = df_credentials.index[row_nr]
                        user_dict = state[cs.config]['credentials']['usernames'][username]
                        if k != '_index':
                            user_dict[k] = v
                        state[cs.config]['credentials']['usernames'][username] = user_dict
                    state[cs.ctr] += 1  # assigns new key to data editor and thus forces re-load of config dataframe
                    msg = st.info("user data updated")
                    sleep(1)
                    msg.empty()
                    auth.save_user_settings()
                except Exception as e:
                    st.error(f'Error updating user: {e}')
            for row_nr in state[curr_editor_key]['deleted_rows']:
                try:
                    deleted_user = df_credentials.index[row_nr]
                    del state[cs.config]['credentials']['usernames'][deleted_user]
                    msg = st.info("user deleted")
                    sleep(1)
                    msg.empty()
                    state[cs.ctr] += 1  # assigns new key to data editor and thus forces re-load of config dataframe
                    auth.save_user_settings()
                except Exception as e:
                    st.error(f'Error deleting user: {e}')
            for row_dict in state[curr_editor_key]['added_rows']:
                try:
                    username = row_dict['_index']
                    access = row_dict['access']
                    email = row_dict['email']
                    name = row_dict['name']
                    password = row_dict['password']
                    new_user = {'access': access, 'email': email, 'logged_in': False, 'failed_login_attempts': 0,
                                'name': name,
                                'password': password}
                    state[cs.config]['credentials']['usernames'][username] = new_user
                    msg = st.info("user added")
                    sleep(1)
                    msg.empty()
                    state[cs.ctr] += 1  # assigns new key to data editor and thus forces re-load of config dataframe
                    auth.save_user_settings()
                except KeyError as e:
                    st.error('Not all mandatory fields completed')

    st.button('Cancel', key='btn_cancel_edit_users')
    if state['btn_cancel_edit_users']:
        state[cs.ctr] += 1


try:
    _, authenticated = auth.authenticate()
    if authenticated:
        run_script()
    else:
        st.switch_page('main.py')
except Exception as error:
    st.error("An exception occurred:", type(error).__name__)
