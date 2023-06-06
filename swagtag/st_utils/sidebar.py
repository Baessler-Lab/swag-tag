import streamlit as st

from config.config import dash_conf
from .st_image import update_fig_window


def sidebar():
    with st.sidebar:
        st.slider(
            label="Min/Max Values for Window?",
            value=dash_conf['default_time_range'],
            **dash_conf['default_min_max_time'],
            key='window_borders',
            on_change=update_fig_window,

        )
