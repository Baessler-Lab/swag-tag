import streamlit as st

from config.config import dash_conf
from swagtag.st_utils.sidebar import sidebar
from swagtag.st_utils.st_image import st_image_box
from swagtag.st_utils.states import init_session_states


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
    st_image_box(image_spot)


if __name__ == '__main__':
    app()
