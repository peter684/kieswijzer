import json

import streamlit as st
import streamlit_authenticator as stauth  # see  https://github.com/mkhorasani/Streamlit-Authenticator
from streamlit import session_state as state

import constants as cs


def load_user_settings():
    try:
        state[cs.config] = json.loads(state[cs.database].get_doc_data('system/config')['json'])
        return state[cs.config]
    except Exception as e:
        if type(e) is KeyError:
            st.error(f'Cannot find database in state: {e}')
        else:
            st.error(f'Error reading configuration in system/config: {e}')
        return None


def save_user_settings():
    try:
        state[cs.database].set_doc_data({'json': json.dumps(state[cs.config])}, 'system/config')
        return True
    except Exception as e:
        if e is KeyError:
            st.error(f'Cannot find database/config in state: {e}')
        else:
            st.error(f'Error saving configuration to system/config: {e}')
        return False


def authenticate():
    try:
        authenticator = stauth.Authenticate(
            state[cs.config]['credentials'],
            state[cs.config]['cookie']['name'],
            state[cs.config]['cookie']['key'],
            state[cs.config]['cookie']['expiry_days'],
            state[cs.config]['pre-authorized']
        )
        authenticator.login()
        return authenticator, state[cs.authentication_status]
    except Exception as e:
        if (type(e) is KeyError):
            st.error(f'Cannot access configuration in session state: {e}')
        else:
            st.error(f'Authentication error: {e}')
        return None, False
