import json
from time import sleep

import streamlit as st
from streamlit import session_state as state

import authenticate as auth
import constants as cs
import sidebar


def reset_password(authenticator):
    try:
        if authenticator.reset_password(state[cs.username]):
            # save user configuration dict as json string to database
            state[cs.database].set_doc_data({'json': json.dumps(state[cs.config])}, 'system/config')
            msg = st.success('Password reset successfully')
            sleep(1)
            msg.empty()
    except Exception as e:
        st.error(e)


def logout():
    del state[cs.username]
    del state[cs.user_path]
    del state[cs.study_stream]
    del state[cs.saved_selections]
    del state[cs.year]
    del state[cs.df_current]
    del state[cs.current_selection]
    del state[cs.current_course_id]
    del state[cs.previous_page]
    del state[cs.authentication_status]
    st.switch_page('main.py')


def run_script(authenticator):
    sidebar.compose_sidebar(show_choices=False, show_legend=False)
    name = state[cs.config]['credentials']['usernames'][state[cs.username]]['name']
    st.header(f'Account details for {name}')

    c1, c2 = st.columns([2, 5])
    with c1:
        with st.expander('Change password', expanded=False):
            try:
                hashed_old_pw = state[cs.config]['credentials']['usernames'][state[cs.username]]['password']
                if authenticator.reset_password(username=state[cs.username], clear_on_submit=True):
                    if auth.save_user_settings():
                        msg = st.success('Password modified successfully')
                        sleep(2)
                        msg.empty()
                    else:
                        # authenticator already changed the password but saving it to db failed; rollback
                        state[cs.config]['credentials']['usernames'][state[cs.username]]['password'] = hashed_old_pw
                        st.error('Could not save settings; password not reset')

            except Exception as e:
                st.error(f'Error updating password: {e}')
        with st.expander('Update user details', expanded=False):
            try:
                if authenticator.update_user_details(username=state[cs.username], clear_on_submit=True):
                    # save user configuration dict as json string to database
                    if auth.save_user_settings():
                        msg = st.success('Entries updated successfully')
                        sleep(2)
                        msg.empty()
                    else:
                        st.error('Could not save settings')
                    sleep(1)
            except Exception as e:
                st.error(f'Error updating details: {e}')
        with st.expander('Log out', expanded=False):
            if st.button('Log out'):
                logout()


try:
    authenticator, authenticated = auth.authenticate()
    if authenticated:
        run_script(authenticator)
    else:
        st.switch_page('main.py')
except Exception as error:
    st.error("An exception occurred:", type(error).__name__)
