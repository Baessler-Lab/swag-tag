import typing

import streamlit as st

from .case_selection import change_case_next, change_case_prev, change_case_submit
from .st_image import update_fig_window, get_max_slices


def sidebar(img_spots: typing.List[st.empty]):
    # Image Tool
    with st.sidebar:
        st.slider(
            label="Min/Max Values for Window?",
            # value=st.session_state.dash_conf['window_default_range'],
            **st.session_state.dash_conf['window_default_min_max'],
            key='window_borders',
            on_change=update_fig_window,
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
