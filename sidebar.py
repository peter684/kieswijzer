import streamlit as st
from streamlit import session_state as state

import constants as cs
from coursecards import pills_legend


def compose_sidebar(show_choices=True, show_legend=True):
    def set_button_style(color='white', backcolor='red', width=200):
        button_css = f'''section[data-testid="stSidebar"] div.stButton button {{
                            background-color: {backcolor};
                            color: {color};
                            width: {width}px;
                        }}'''
        st.markdown(f"<style>{button_css}</style>", unsafe_allow_html=True)

    try:
        def stream_select():
            # force reload current dataframe & selection collections by deleting them from state
            del state[cs.df_current]
            del state[cs.current_selection]
            del state[cs.saved_selections]
            state[cs.study_stream] = state[cs.study_stream_select]

        def year_radio():
            state[cs.year] = state[cs.year_radio]

        is_admin = state[cs.config]['credentials']['usernames'][state[cs.username]]['access'] == 'admin'
        set_button_style()
        if show_choices:
            st.sidebar.selectbox(label="Select stream",
                                 options=["BBT", "MWT"],
                                 index=0 if state[cs.study_stream] == 'BBT' else 1,
                                 key=cs.study_stream_select,
                                 on_change=stream_select)
        if show_choices:
            st.sidebar.radio(label=cs.year,
                             options=["1", "2", "3"],
                             index=["1", "2", "3"].index(state[cs.year]),
                             horizontal=True,
                             key=cs.year_radio,
                             on_change=year_radio)
        if show_legend:
            with st.sidebar:
                pills_legend()
        st.sidebar.divider()
        st.sidebar.button("Home", key='btn_home')
        if state['btn_home']:
            st.switch_page('pages/home.py')
        st.sidebar.button("My account", key='btn_my_account')
        if state['btn_my_account']:
            st.switch_page('pages/account.py')
        if is_admin:
            st.sidebar.button("Users", key='btn_user_accounts')
            if state['btn_user_accounts']:
                st.switch_page('pages/users.py')
        st.sidebar.divider()
        btn_text = 'Osiris'
        btn_link = 'https://tue.osiris-student.nl/onderwijscatalogus/extern/start?taal=en'
        st.sidebar.markdown(
            f'''<a href="{btn_link}" style="
                display: inline-block; 
                padding: 6px 10px; 
                background-color: red; 
                color: white; 
                text-align: center; 
                text-decoration: none; 
                font-size: 16px; 
                border-radius: 8px;
                width: 200px;
                ">
                    {btn_text}
                </a>
                ''',
            unsafe_allow_html=True
        )
    except KeyError as e:
        st.error('Cannot read state values')
