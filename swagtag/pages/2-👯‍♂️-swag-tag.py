import streamlit as st

from config.load_config import load_dash_conf
from swagtag.st_utils.sidebar import sidebar
from swagtag.st_utils.st_annotation import st_annotation_box
from swagtag.st_utils.st_image import st_image_box
from swagtag.st_utils.st_report import st_report_box
from swagtag.st_utils.states_swag_tag import init_session_states


def app():
    st.set_page_config(
        page_title=load_dash_conf(default=True)['page_title'],
        layout="wide",
    )
    init_session_states()

    st.title(st.session_state.dash_conf['title'])

    c1, c2 = st.columns((1, 2))
    with c2:
        image_spot = st.container()
        # display images
        fig_spots = st_image_box(image_spot)
    with c1:
        st_report_box()
        st_annotation_box()

    # sidebar
    sb = sidebar(img_spots=fig_spots)


if __name__ == '__main__':
    app()
