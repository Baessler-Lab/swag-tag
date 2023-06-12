import typing
from copy import deepcopy
from functools import partial

import streamlit as st

from config.config import sql_conf
from config.load_config import load_dash_conf_meta, lookup_label_from_config_meta, store_configuration
from .case_selection import change_case_next, change_case_prev, change_case_submit
from .st_image import update_fig_window, get_max_slices, callback_window_border_slider
from .states import update_config


def sidebar(img_spots: typing.List[st.empty]):
    # Image Tool
    with st.sidebar:
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
            print(config_meta)
            cur_conf: typing.MutableMapping
            cur_conf['default_case_no'] = st.session_state['case_no']
            cur_conf['window_default_range'] = st.session_state['window_borders']
            with st.form('Save configuration'):
                conf_id = st.text_input(
                    'Name of your configuration',
                    value=cur_conf['config_id'],
                    key='conf_saving_name',
                )

                st.form_submit_button(
                    label='Save current configuration',
                    on_click=store_configuration,
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
