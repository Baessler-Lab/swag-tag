import typing
from copy import deepcopy
from functools import partial

import streamlit as st

from config.config import sql_conf
from config.load_config import load_dash_conf_meta, lookup_label_from_config_meta
from user.manage import add_new_user
from .case_selection import change_case_next, change_case_prev, change_case_submit, store_conf_submit
from .st_image import update_fig_window, get_max_slices, callback_window_border_slider
from .states_llm import update_config, update_users, update_user


def change_user():
    # sanity check if user in users
    selected_user = st.session_state.selected_user
    update_user(user_name=selected_user[sql_conf['user_table']['user_col']])


def add_user():
    new_user = st.session_state['new_user']
    new_user: typing.Dict[str, typing.Any]
    print(new_user)

    add_new_user(user_name=new_user, conn=st.session_state.db_conn)
    update_users(inplace=True)
    update_user(user_name=new_user)
    st.success(f"Successfully added a the new user '{new_user}'")


def st_user_selection():
    st.markdown(f"### Current user <{st.session_state.current_user}>")

    st.selectbox(
        label='Select new user',
        options=list(st.session_state.users_dict.values()),
        format_func=lambda x: x['user_name'],
        index=0,
        key='selected_user',
        on_change=change_user,
    )
    with st.expander(label='Add new user', expanded=False):
        with st.form('Add new user'):
            st.text_input(
                label='Username',
                key='new_user',
            )
            st.form_submit_button(
                label='Add user',
                on_click=add_user,
            )


def image_control(**kwargs):
    assert 'img_spots' in kwargs
    img_spots = kwargs['img_spots']
    st.slider(
        label="Min/Max Values for Window?",
        value=st.session_state.dash_conf['window_default_range'],
        **st.session_state.dash_conf['window_default_min_max'],
        key='window_border_slider',
        on_change=callback_window_border_slider,
        kwargs=dict(img_spots=img_spots)

    )
    st.slider(
        label="Slice number on z-axis",
        min_value=0,
        max_value=get_max_slices(),
        key='slice_no',
        on_change=update_fig_window,
        kwargs=dict(img_spots=img_spots)
    )


def sidebar(**kwargs):
    # Image Tool
    with st.sidebar:
        # user selection
        st_user_selection()
        if 'img_spots' in kwargs:
            image_control(**kwargs)

        # Case Iterator
        with st.expander('Case Iterator', expanded=True):
            cur_case_no = st.session_state['case_no']
            cur_case_id = st.session_state['cur_study_instance_uid']
            st.write(f'Current case: {cur_case_id}[No. {cur_case_no}]')

            # relative iteration
            c1, c2 = st.columns((1, 1))
            with c2:
                st.button('Next', key='next', on_click=change_case_next)
            with c1:
                st.button('Previous', key='prev', on_click=change_case_prev)

            # absolute case selection
            with st.form('Select case by number.'):
                st.number_input('Case_no',
                                value=st.session_state['case_no'],
                                min_value=0,
                                max_value=st.session_state['map_study_instance_uid_accession_number'].shape[0],
                                step=1,
                                key='case_number_form'
                                )
                st.form_submit_button('Switch to selected case.', on_click=change_case_submit, )

        # Config load/save
        with st.expander('Load/save configuration', expanded=True):
            cur_conf = deepcopy(st.session_state['dash_conf'])
            config_meta = load_dash_conf_meta(st.session_state['db_conn'])
            cur_conf: typing.MutableMapping
            cur_conf['default_case_no'] = st.session_state['case_no']
            with st.form('Save configuration'):
                conf_id = st.text_input(
                    'Name of your configuration',
                    value=cur_conf['config_id'],
                    key='conf_saving_name',
                )

                st.form_submit_button(
                    label='Save current configuration',
                    on_click=store_conf_submit,
                    kwargs=dict(
                        config_id=conf_id,
                        dashboard_configuration=cur_conf,
                        conn=st.session_state.db_conn
                    ),
                )

            # load configuration
            latest = st.checkbox('Latest',
                                 value=True,
                                 key='latest'
                                 )

            with st.form('Select configuration'):
                st.selectbox(
                    label='Configuration',
                    options=config_meta[sql_conf['config_table']['prim_key']],
                    format_func=partial(lookup_label_from_config_meta, config_meta=config_meta),
                    key='selected_config_id',
                    disabled=latest,
                )

                st.form_submit_button(
                    'Load selected configuration',
                    on_click=update_config,
                    kwargs=dict(
                        # config_id=st.session_state['selected_config_id'],
                        # conn=st.session_state['db_conn'],
                        # default=False,
                    )
                )
