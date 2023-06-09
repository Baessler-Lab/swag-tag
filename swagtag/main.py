import streamlit as st

from config.config import dash_conf
from .st_utils.sidebar import sidebar
from .st_utils.st_image import st_image_box
from .st_utils.states import init_session_states


def app():
    st.set_page_config(
        page_title=dash_conf['page_title'],
        layout="wide",
    )
    st.title(dash_conf['title'])

    init_session_states()

    sb = sidebar()
    image_spot = st.empty()

    # display images
    st_image_box(image_spot, image_id=0)
