import streamlit as st
import streamlit.components.v1 as components
from pandas import DataFrame, concat
from streamlit import session_state as state

import authenticate as auth
import constants as cs
import firestore_db as fs
import sidebar
from coursecards import course_card_buttons, pill_html


def run_script():
    def del_course(course_id):
        df = state[cs.df_current]
        df = df.drop(df[df[cs.id] == course_id].index)
        state[cs.df_current] = df

    def info_course(course_id):
        state[cs.current_course_id] = course_id
        # we're not allowed to switch page & rerun from within a callback. 
        # Flag intent to switch page in state instead and switch page in main script

    def get_selection_docpath(selection_name):
        '''
        returns path to  selection and selection owner (either current user or system) if selection exists,
        None otherwise
        :param selection_name: Name of selection
        :return: database path to selection document containing course collection, owner of collection
        '''

        user_query = state[cs.database].query_coll(
            coll_path=f'{cs.coll_users}/{state[cs.username]}/{cs.coll_course_selections}',
            doc_fields=[cs.name, cs.created_by],
            where_conditions=[[cs.name, '==', selection_name]]
        )

        system_query = state[cs.database].query_coll(
            coll_path=f'{cs.coll_users}/{cs.user_system}/{cs.coll_course_selections}',
            # coll_path=f'users/system/course_selections',
            doc_fields=[cs.name, cs.created_by],
            where_conditions=[[cs.name, '==', selection_name]]
        )
        if len(user_query) == 0 and len(system_query) == 0:
            return None, None
        elif len(system_query) == 0:  # selection name is a user selection
            return f'{cs.coll_users}/{state[cs.username]}/{cs.coll_course_selections}/{user_query[0][cs.id]}', \
                user_query[0][cs.created_by]
        else:  # selection is standard system selection
            return f'{cs.coll_users}/{cs.system}/{cs.coll_course_selections}/{system_query[0][cs.id]}', \
                system_query[0][cs.created_by]

    def load_saved_selections(stream):
        selections_list = []
        # load default system selections
        course_selection_path = f'{cs.coll_users}/{cs.user_system}/{cs.coll_course_selections}'
        for d in state[cs.database].query_coll(coll_path=course_selection_path,
                                               include_id=True,
                                               doc_fields=[cs.name],
                                               where_conditions=[[cs.stream, '==', stream]]):
            selections_list.append(d[cs.name])
        # load any user selections
        course_selection_path = f'{cs.coll_users}/{state[cs.username]}/{cs.coll_course_selections}'
        for d in state[cs.database].query_coll(coll_path=course_selection_path,
                                               include_id=True,
                                               doc_fields=[cs.name],
                                               where_conditions=[[cs.stream, '==', stream]]):
            selections_list.append(d[cs.name])
        return selections_list

    def save_selection(stream, selection_name):
        selection_root_path = f'{cs.coll_users}/{state[cs.username]}/{cs.coll_course_selections}'
        db = state[cs.database]
        # try to find existing selections with this name
        docpath, owner = get_selection_docpath(selection_name)
        if owner is not None and owner != state[cs.username]:  # found system selection
            st.error('Cannot overwrite system selections')
            # technically we can but this would result in 2 selections with the same name in different locations
            return
        if docpath is None:
            # create document to hold collection of selected courses
            # assign document with auto ID by passing collection path instead of document path
            # created_by field is used to make sure users can only delete their own selections,
            # not system selections or other user's
            doc_id = db.set_doc_data(
                doc_dict={cs.name: selection_name, cs.created_by: state[cs.username], 'stream': stream},
                doc_path=selection_root_path
            )
            docpath = f'{selection_root_path}/{doc_id}'
            state[cs.saved_selections].append(selection_name)
        # add all coursepaths to this collection:
        for row_index, row in df_current.iterrows():  # overwrite existing selection
            selected_course_path = f'{docpath}/{cs.coll_courses}/{row[cs.id]}'
            db.set_doc_data({cs.path: row[cs.id], cs.year: row[cs.year]}, selected_course_path)

    def load_selection(selection_name):
        docpath, owner = get_selection_docpath(selection_name)
        # get list of dicts; dicts contain id & path (essentially the same info)
        paths = state[cs.database].get_coll_doc_data(f'{docpath}/{cs.coll_courses}')
        course_ids = [course_dict[cs.id] for course_dict in paths]
        course_years = [course_dict[cs.year] for course_dict in paths]
        osiris = state[cs.df_osiris]
        df = osiris[osiris[cs.id].isin(course_ids)].copy()
        df.loc[df.index, cs.year] = course_years
        return df

    def rename_selection(old_name, new_name):
        docpath, owner = get_selection_docpath(old_name)
        if owner is not None and owner != state[cs.username]:
            st.error('Cannot rename system selections')
            return False
        state[cs.database].update_doc_fields({cs.name: new_name}, docpath)
        state[cs.saved_selections] = [state[cs.rename_text_value]
                                      if el == state[cs.current_selection] else el for el in
                                      state[cs.saved_selections]
                                      ]
        state[cs.current_selection] = new_name
        return True

    def delete_selection(selection_name):
        db = state[cs.database]
        docpath, owner = get_selection_docpath(selection_name)
        # path = get_selection_docpath(state[cs.username], selection_name)
        # db.delete(path)
        if owner is not None and owner != state[cs.username]:
            st.error('Cannot delete system selections')
            return False
        if docpath is not None:
            db.delete(docpath)
        return True

    # --------------------- state  ---------------------------#
    if cs.database not in state:
        state[cs.database] = fs.Database()
    if cs.df_osiris not in state:
        state[cs.df_osiris] = DataFrame(state[cs.database].get_coll_doc_data(cs.osiris))
    if cs.user_path not in state:
        user_path = f'{cs.coll_users}/{state[cs.username]}'
        query = state[cs.database].query_coll(coll_path=cs.coll_users,
                                              where_conditions=[[cs.username, "==", state[cs.username]]])
        if len(query) == 0:
            state[cs.database].set_doc_data({cs.username: state[cs.username]}, user_path)
        state[cs.user_path] = user_path
    if cs.study_stream not in state:
        state[cs.study_stream] = 'BBT'
    if cs.saved_selections not in state:
        state[cs.saved_selections] = load_saved_selections(state[cs.study_stream])
    if cs.year not in state:
        state[cs.year] = '1'
    if cs.ctr not in state:
        state[cs.ctr] = 0  # need ctr to assign unique key to optional courses data_editor so it will repaint
    if cs.df_current not in state:
        # load standard mandatory curriculum
        col_name = cs.bbt_optional if state[cs.study_stream] == 'BBT' else cs.mwt_optional
        state[cs.df_current] = state[cs.df_osiris].loc[
            state[cs.df_osiris][col_name] == "False"
            ].copy()
    if cs.current_selection not in state:
        state[cs.current_selection] = ''
    if cs.current_course_id not in state:
        state[cs.current_course_id] = None
    if cs.previous_page not in state:
        state[cs.previous_page] = ""
    # change some style settings, such as remove padding at top of page and fonts
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 3rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)

    # reset course ID if we just came back from page 'info'
    if state[cs.previous_page] != 'home':
        state[cs.current_course_id] = None
        state[cs.previous_page] = 'home'
    # if user clicked 'info' on this page, switch to page 'info' & open course with current_course_ID there:
    if state[cs.current_course_id] is not None:
        state[cs.previous_page] = 'home'
        st.switch_page('pages/info.py')

    df_osiris = state[cs.df_osiris]
    df_current = state[cs.df_current]
    saved_selections = state[cs.saved_selections]
    study_stream = state[cs.study_stream]
    year = state[cs.year]
    sidebar.compose_sidebar()
    st.write(f'Welcome {state[cs.name]}')

    # selections management
    sel_col1, sel_col2, sel_col3 = st.columns([2, 1, 2])
    with (sel_col1):
        st.selectbox(label='current curriculum selection:',
                     options=saved_selections,
                     index=len(saved_selections) - 1,
                     key=cs.current_selection_selectbox)
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            def btn_delete_selection():
                try:
                    del_selection_name = state[cs.current_selection_selectbox]
                    if delete_selection(del_selection_name):
                        state[cs.saved_selections].remove(del_selection_name)
                        st.info(f'selection {del_selection_name} has been deleted.')
                except Exception as e:
                    st.error(e)

            st.button('delete', key="delete_selection_btn", on_click=btn_delete_selection)
        with sc2:
            if cs.rename_expanded not in state:
                state[cs.rename_expanded] = False

            def handle_rename():
                state[cs.rename_text_value] = state[cs.rename_selection_text]
                state[cs.rename_selection_text] = ''
                state[cs.rename_expanded] = False
                old_text = state[cs.current_selection_selectbox]
                new_text = state[cs.rename_text_value]
                if new_text in state[cs.saved_selections]:
                    st.error(f'selection list with name {state[cs.rename_text_value]} already exists.')
                elif new_text == '':
                    st.error("Name cannot be empty")
                elif rename_selection(old_text, new_text):
                    st.info(f'Selection {old_text} has been renamed to {state[cs.rename_text_value]}.')

            with st.expander('rename', expanded=state[cs.rename_expanded]):
                st.text_input(label=f'rename {state[cs.current_selection_selectbox]} to:',
                              key=cs.rename_selection_text,
                              )
                st.button('rename', on_click=handle_rename)
        with sc3:
            if cs.add_expanded not in state:
                state[cs.add_expanded] = False

            def handle_save():
                save_to_name = state[cs.add_selection_text]
                state[cs.add_expanded] = False
                if save_to_name == "":
                    st.error('Name cannot be empty')
                else:
                    state[cs.add_text_value] = save_to_name
                    state[cs.add_selection_text] = ''
                    if save_selection(stream=state[cs.study_stream],
                                      selection_name=save_to_name):  # overwrite without additional user warning!
                        # state[cs.current_selection_selectbox] = save_to_name
                        state[cs.current_selection] = save_to_name
                        st.info(f'selection has been saved as {save_to_name}')
                        state[cs.add_expanded] = False

            with st.expander('save', expanded=state[cs.add_expanded]):
                st.text_input(label="save selection as:",
                              key=cs.add_selection_text,
                              value=state[cs.current_selection_selectbox],
                              )
                st.button('save', on_click=handle_save)

    if (state[cs.current_selection_selectbox] is not None and
            state[cs.current_selection_selectbox] != state[cs.current_selection]):
        state[cs.df_current] = load_selection(state[cs.current_selection_selectbox])
        state[cs.current_selection] = state[cs.current_selection_selectbox]

    st.toggle(key=cs.tgl_show_hide_options, label='show optional courses')
    # optional courses
    if state[cs.tgl_show_hide_options]:
        # show pills & selection boxes
        opt_col1, opt_col2 = st.columns([1, 1])  # use 1/3of screen width
        with opt_col2:
            lls = cs.learning_lines
            for ll in lls:
                oc1, oc2, _ = st.columns([1, 3, 3])
                label = 'Any' if ll[cs.abbr] == 'B' else ll[cs.name]
                # color= '#C0C0C0' if label == 'B' else ll['color']
                color = ll['color']
                with oc1:
                    components.html(pill_html(color), height=22)
                with oc2:
                    st.checkbox(label=label, value=True, key=f'filteroption_{ll[cs.abbr]}')
        fld = cs.bbt_optional if study_stream == 'BBT' else cs.mwt_optional
        df_opt = df_osiris.loc[
            (df_osiris[fld] != 'False') &
            ((df_osiris[cs.year] == year) | (df_osiris[cs.year] == ''))
            ]
        # do not show courses already selected for another year to avoid user selecting the same course
        # twice in different years
        sel_other_year = df_opt.loc[(df_opt[cs.id].isin(df_current[cs.id])) &
                                    (df_current[cs.year] != year)]
        df_opt = df_opt.drop(sel_other_year.index)

        # drop any items based on checked learning_line checkboxes
        drop_rows = []
        for rownr, row in df_opt.iterrows():
            # include courses if they correspond to checked options for learning lines
            selections = dict([(ll[cs.abbr], state[f'filteroption_{ll[cs.abbr]}']) for ll in cs.learning_lines])
            if selections['B']:
                continue  # checkbox 'any' is checked,include row
            course_lls = row[cs.learninglines].split(',')
            drop_row = True
            for ll in course_lls:
                if len(ll) > 0 and selections[ll]:
                    drop_row = False
            if drop_row:
                if rownr not in drop_rows:
                    drop_rows.append(rownr)
        df_opt = df_opt.drop(drop_rows)

        df_opt.insert(0, "select", False)
        # mark as checked if already in current df
        df_opt.loc[df_opt[cs.id].isin(df_current[cs.id]), 'select'] = True
        state[cs.ctr] += 1

        # data editor (and dataframe) do not re-read the dataframe passed when constructing the widget
        # and keep it in the session state.
        # Although this makes sense for large dataframes, we want to update the database
        # after every cell change, and then reload the data into data editor (i.e. for every rerun of the page).
        # This is achieved by assigning a new key using the state ctr property that is
        # updated at the start of the script, and reconstructs the widget with a fresh dataset

        def editor_changed(key):
            # called after user has either selected or unselected the check box in the data editor
            # (other cells must be read-only or this will fail if user changes another cell!)
            sel_cell = state[key]['edited_rows']  # returns {row_nr:{column: value}}
            df_curr = state[cs.df_current]
            editor_rownr = list(sel_cell.keys())[0]
            is_selected = sel_cell[editor_rownr]['select']
            selected_row = df_opt.iloc[editor_rownr]
            df_row = selected_row.drop('select').to_frame().T
            total_ecs_currently = 0
            if is_selected:
                try:
                    extra_ecs = float(selected_row[cs.ec])
                    block = selected_row[cs.block]
                    # add selected row if ECs not exceeded
                    df_row[cs.year] = year
                    current_ecs_in_block = df_curr[cs.ec].loc[
                        (df_curr[cs.year] == year) &
                        (df_curr[cs.block] == block)
                        ].to_list()
                    for e in current_ecs_in_block:
                        total_ecs_currently += float(e)
                    if extra_ecs + total_ecs_currently <= 15:
                        df_curr = concat([df_curr, df_row])
                    else:
                        st.warning('Cannot add course, would exceed 15 EC this block')
                except:
                    st.error('Cannot read ECs or block of selected course(s).')
            else:
                df_curr = df_curr.drop((df_curr[df_curr[cs.id] == selected_row[cs.id]]).index)
            state[cs.df_current] = df_curr

        key = f'optional_editor{state[cs.ctr]}'  # paint new editor by providing new key, will keep original data otherwise
        with opt_col1:
            st.data_editor(
                data=df_opt,
                key=key,
                hide_index=True,
                column_config={'select': st.column_config.CheckboxColumn(required=True),
                               cs.code: st.column_config.Column(disabled=True),
                               cs.volledige_naam: st.column_config.Column(disabled=True),
                               cs.year: st.column_config.Column(disabled=True),
                               cs.block: st.column_config.Column(disabled=True)
                               },
                column_order=['select', cs.code, cs.volledige_naam, cs.year, cs.block],
                on_change=editor_changed,
                args=[key]
            )

    # show course cards for df_current
    df_current = state[cs.df_current]
    for block_index, col in enumerate(st.columns(4)):
        with (col):
            df_year = df_current[df_current[cs.year] == year]
            df_block = df_year[df_year[cs.block] == f'{block_index + 1}']
            for row_index, row in df_block.iterrows():
                pill_colors = []
                buttons = [{"label": "Info", "func": info_course}]
                theme = "free"
                applies_to_ll = row[cs.learninglines]
                if len(applies_to_ll) > 0:
                    for ll in applies_to_ll.split(','):
                        for ll_dict in cs.learning_lines:
                            if ll_dict[cs.abbr] == ll:
                                pill_colors.append(ll_dict["color"])
                if ((study_stream == 'BBT' and row[cs.bbt_optional] == 'False') or
                        (study_stream == 'MWT' and row[cs.mwt_optional] == 'False')):
                    theme = "fixed"
                if theme != "fixed":
                    buttons.append({"label": "Remove", "func": del_course})
                label = f'<b>{row[cs.code]}</b><br>{row[cs.long_name]}<br><em>{row[cs.lecturer]}</em>'
                course_card_buttons(
                    pill_colors=pill_colors,
                    label=label,
                    theme=cs.themes[theme],
                    width=300,
                    course_id=row[cs.id],
                    buttons=buttons
                )


try:
    _, authenticated = auth.authenticate()
    if authenticated:
        run_script()
    else:
        st.switch_page('main.py')
except Exception as error:
    st.error("An exception occurred:", type(error).__name__)
