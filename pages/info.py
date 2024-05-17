import streamlit as st
from streamlit import session_state as state

import authenticate as auth
import constants as cs
import sidebar
from coursecards import pills_legend


def run_script():
    def save(course_dict, label, key):
        try:
            new_val = state[label]
            if type(new_val) is bool:
                new_val = "True" if new_val else "False"
            if course_dict[key] != new_val:
                doc_path = f'{cs.osiris}/{course_dict[cs.id]}'
                state[cs.database].update_doc_fields({key: new_val}, doc_path)
            st.info(f"Field '{key}' updated to: {new_val if len(new_val) < 50 else new_val[:50] + '...'}")
        except Exception as e:
            st.error(f'Error saving field to database: {e}')

    def my_text(course_dict, label, key):
        try:
            value = course[key]
        except KeyError:
            value = ""
        st.text_input(key='txt_input_' + label,
                      label=label,
                      value=value,
                      disabled=is_read_only,
                      on_change=save,
                      args=[course_dict, 'txt_input_' + label, key])

    def my_text_area(course_dict, label, key):
        try:
            value = course[key]
        except KeyError:
            value = ""
        st.text_area(key='txt_area_' + label,
                     label=label,
                     value=value,
                     disabled=is_read_only,
                     on_change=save,
                     label_visibility="hidden",
                     args=[course_dict, 'txt_area_' + label, key])

    def my_checkbox(course_dict, label, key):
        try:
            value = course[key]
        except KeyError:
            value = ""
        value = False if value == "False" else True
        st.checkbox(key='check_' + label,
                    label=label,
                    value=value,
                    on_change=save,
                    disabled=is_read_only,
                    args=[course_dict, 'check_' + label, key])

    def save_editor(course_dict, collection_name, editor_key, data):
        for row_nr, row_dict in state[editor_key]['edited_rows'].items():
            try:
                path = f'{cs.osiris}/{course_dict[cs.id]}/{collection_name}/{data[row_nr][cs.id]}'
                state[cs.database].update_doc_fields(edit_dict=row_dict, doc_path=path)
                state[cs.ctr] += 1
            except Exception as e:
                st.error(f'Error updating row: {e}')
        for row_nr in state[editor_key]['deleted_rows']:
            try:
                path = f'{cs.osiris}/{course_dict[cs.id]}/{collection_name}/{data[row_nr][cs.id]}'
                state[cs.database].delete(path)
                state[cs.ctr] += 1
            except Exception as e:
                st.error(f'Error deleting row: {e}')
        for row_dict in state[editor_key]['added_rows']:
            try:
                if len(row_dict):
                    path = f'{cs.osiris}/{course_dict[cs.id]}/{collection_name}'
                    state[cs.database].set_doc_data(doc_dict=row_dict, doc_path=path)
                state[cs.ctr] += 1
            except Exception as e:
                st.error(f'Error adding row: {e}')
        # for row_nr in state[editor_key]['edited_rows']:
        #
        # for row_nr in state[editor_key]['deleted_rows']:
        #     doc_id = doc_dict_list[row_nr][cs.id]
        #     path = f'{cs.osiris}/{course_dict[cs.id]}/{collection_name}/{doc_id}'
        #     state[cs.database].delete(path=path)
        # for row in state[editor_key]['added_rows']:
        #     edit_fields = row
        #     if len(row):
        #         path = f'{cs.osiris}/{course_dict[cs.id]}/{collection_name}'  # name will be auto-assigned by FS
        #         state[cs.database].set_doc_data(doc_dict=edit_fields, doc_path=path)

    def my_editor(course_dict, collection_name, column_fields, label=None):
        try:
            label = label if not None else collection_name
            editor_key = f'{label}{state[cs.ctr]}'
            st.markdown(f'**{label}**')
            data = state[cs.database].get_coll_doc_data(f'{cs.osiris}/{state[cs.current_course_id]}/{collection_name}')
            if is_read_only:
                st.data_editor(
                    key=editor_key,
                    data=data,
                    column_order=column_fields,
                    disabled=True)
            else:
                try:
                    cols = list(data[0].keys())
                    cols.remove(cs.id)
                    if 'opmerking:' in cols:
                        cols.remove('opmerking:')
                except:
                    cols = None
                with st.form(key='form_' + editor_key):
                    st.data_editor(
                        key=editor_key,
                        data=data,
                        column_order=cols,
                        num_rows="dynamic",
                        args=[course_dict, collection_name, editor_key, data],
                        disabled=False)
                    st.form_submit_button(
                        label='Commit changes',
                        on_click=save_editor,
                        args=[course_dict, collection_name, editor_key, data])

        except Exception as e:
            st.error(f'Encountered exception: {e}')

    sidebar.compose_sidebar(show_choices=False)
    # ----------------------main page ---------------------#
    try:
        db = state[cs.database]
        state[cs.previous_page] = 'info'
        course = db.get_doc_data(f'{cs.osiris}/{state[cs.current_course_id]}')  # get document fields as dict
        state[cs.ctr] += 1  # needed to refresh dataset for data_editor, see remarks in my_editor def
    except Exception as e:
        if (type(e) is KeyError):
            st.error(f'A session state parameter is not defined: {e}')
        else:
            st.error(f'Cannot access course, switching to home page: {e}')
        st.switch_page('pages/home.py')
    try:
        is_read_only = state[cs.config]['credentials']['usernames'][state[cs.username]]['access'] != 'admin'
    except Exception as e:
        st.error(f'cannot find user in session state: {e}')
        is_read_only = True

    st.header(f'info on course {course[cs.volledige_naam]}')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('**Course summary**')
        my_text(course, 'Name', cs.long_name)
        c1, c2, c3 = st.columns(3)
        with c1:
            my_text(course, 'Year', cs.year)
        with c2:
            my_text(course, 'Block', cs.block)
        with c3:
            my_text(course, 'ECs', cs.ec)
        c1, c2 = st.columns(2)
        with c1:
            my_checkbox(course, 'Optional for BBT', cs.bbt_optional)
        with c2:
            my_checkbox(course, 'Optional for MWT', cs.mwt_optional)

    with col2:
        st.markdown('**Description**')
        my_text_area(course, 'description', cs.contents_en)
    with col3:
        st.markdown('**Requirements**')
        my_text_area(course, 'requirements', cs.requirements)

        lls = course[cs.learninglines]
        ll_list = []
        if len(lls) > 0:
            st.markdown('**Fits with learning lines:**')
            for ll in lls.split(','):
                for learning_line in cs.learning_lines:
                    if learning_line['abbr'] == ll:
                        ll_list.append(learning_line)
        pills_legend(learning_lines=ll_list)

    doc_col, toets_col = st.columns([1, 2])
    with doc_col:
        my_editor(
            course_dict=course,
            label="Teachers",
            collection_name=cs.docenten,
            column_fields=[cs.docent_naam, cs.rol, cs.opmerking])
        my_editor(
            course_dict=course,
            label="Timeslots",
            collection_name=cs.timeslots,
            column_fields=[cs.timeslot, cs.omschrijving_docenten])

    with toets_col:
        my_editor(
            course_dict=course,
            label="Tests",
            collection_name=cs.toetsen,
            column_fields=[cs.gelegenheden, cs.min_cijfer, cs.omschrijving_toetsen, cs.verplicht, cs.weging,
                           cs.overig_toetsen])
        my_editor(
            course_dict=course, label="Work forms",
            collection_name=cs.werkvormen,
            column_fields=[cs.aantal_bijeenk, cs.frequentie, cs.aanw_plicht, cs.omschrijving_werkvormen,
                           cs.contactduur])


try:
    _, authenticated = auth.authenticate()
    if authenticated:
        run_script()
    else:
        st.switch_page('main.py')
except Exception as error:
    st.error("An exception occurred:", type(error).__name__)
