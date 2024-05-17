import json
import smtplib
from email.mime.text import MIMEText
from time import sleep

import streamlit as st
from streamlit import session_state as state

import authenticate as auth
import constants as cs
import firestore_db


def send_mail(email_receiver, subject, email_body):
    try:
        msg = MIMEText(email_body)
        msg['From'] = 'kieswijzer@gmail.com'
        msg['To'] = email_receiver
        msg['Subject'] = subject

        email_sender = 'peter.ebus@gmail.com'
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["mail_user"], st.secrets["mail_password"])
        server.sendmail(email_sender, email_receiver, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email: {e}")


if cs.database not in state:
    state[cs.database] = firestore_db.Database()
if cs.config not in state:
    # load json string in database containing dict with hashed user passwords, emails etc
    state[cs.config] = json.loads(state[cs.database].get_doc_data('system/config')['json'])

config = state[cs.config]
db = state[cs.database]
st.set_page_config(page_title="Home", page_icon="🎓", layout="wide", menu_items={"About": "Kieswijzer 1.0 beta"})
c1, _ = st.columns([1, 4])
with c1:
    authenticator, authenticated = auth.authenticate()

if state[cs.authentication_status]:  # user is authenticated
    try:
        st.switch_page('pages/home.py')
    except Exception as e:
        print(e)
else:  # user has not logged in yet or provided wrong credentials
    if state[cs.authentication_status] == False:
        st.error('Incorrect credentials')
    # set up page & log in :
    c1, c2 = st.columns([3, 1])
    with c1:
        e1, e2, e3 = st.columns(3)
        with e1:
            with st.expander('Forgot password', expanded=False):
                try:
                    username_of_forgotten_password, email_of_forgotten_password, new_random_password = authenticator.forgot_password()
                    if username_of_forgotten_password:
                        st.success(f'New password will be sent to {email_of_forgotten_password}')
                        # save user configuration dict as json string to database
                        state[cs.database].set_doc_data({'json': json.dumps(state[cs.config])}, 'system/config')
                        body = f"""
                            Beste gebruiker,\n
                            Hierbij je nieuwe wachtwoord voor de BMT kieswijzer. Ga naar kieswijzer.streamlit.app en log in with met je gebruikersnaam en dit wachtwoord:\n
                            {new_random_password}.\n
                            Na inloggen kun je je wachtwoord veranderen in 'my account'.\n
                            \n
                            Veel kies succes, \n
                            \n
                            Mede namens de docenten van BMT,\n
                            Peter Ebus van Kieswijzer.
                            """

                        # The developer should securely transfer the new password to the user.
                        send_mail(email_receiver=email_of_forgotten_password, subject="Kieswijzer login details",
                                  email_body=body)
                    elif username_of_forgotten_password == False:
                        st.error('Username not found')
                except Exception as e:
                    st.error(e)
        with e2:
            with st.expander('Forgot username', expanded=False):
                try:
                    username_of_forgotten_username, email_of_forgotten_username = authenticator.forgot_username()
                    if username_of_forgotten_username:
                        st.success(f'E-mail with your user name has been sent to: {email_of_forgotten_username}')
                        body = f"""
                                Beste gebruiker,\n
                                Je hebt gevraagd om een mail met je gebruikersnaam voor de BMT kieswijzer.\n
                                Je gebruikersnaam is: {username_of_forgotten_username}.\n
                                Ga naar kieswijzer.streamlit.app en log in met deze gebruikersnaam en je wachtwoord.\n
                                \n
                                Vriendelijke groet,\n
                                \n
                                Mede namens de docenten van BMT,\n
                                Peter Ebus van Kieswijzer.
                                """
                        send_mail(email_receiver=email_of_forgotten_username, subject="Kieswijzer username",
                                  email_body=body)
                    elif email_of_forgotten_username == False:
                        st.error('Email not found')
                except Exception as e:
                    st.error(e)
        with e3:
            with st.expander('Sign up', expanded=False):
                try:
                    new_email, new_username, new_name = authenticator.register_user(
                        pre_authorization=False)
                    if new_email:
                        state[cs.config]['credentials']['usernames'][new_username]['access'] = 'user'
                        # save user configuration dict as json string to database
                        state[cs.database].set_doc_data({'json': json.dumps(state[cs.config])}, 'system/config')
                        msg = st.success('User registered successfully')
                        sleep(1)
                        msg.empty()
                except Exception as e:
                    st.error(e)
        # show login widget
        l1, _ = st.columns([2, 1])

    msg = ''' 
    Deze kieswijzer is ontwikkeld als hulpmiddel bij het samenstellen van een vakkenpakket. 
    Er kunnen geen rechten worden ontleend aan de informatie uit dit systeem. 
    Voor actuele informatie over vakken dien je Osiris te raadplegen (link aanwezig in deze app).
                
    Let op: tijdens registreren wordt gevraagd om persoonlijke gegevens (naam en e-mail adres). 
    Als je deze gegevens niet wil invoeren kan je de velden met pseudo-data invullen (bv. naam@site.nl). 
    Hou er wel rekening mee dat het systeem je dan niet kan mailen als je je username en/of password kwijtraakt. 
    '''
    st.write(msg)
