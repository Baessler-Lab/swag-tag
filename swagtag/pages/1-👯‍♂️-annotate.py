import streamlit as st


if not 'page' in st.session_state:
    st.session_state['page'] = 'swag-tag'

from config.load_config import load_dash_conf
from swagtag.st_utils.sidebar import settings, image_sidebar
from swagtag.st_utils.st_annotation import st_annotation_box
from swagtag.st_utils.st_image import st_image_box
from swagtag.st_utils.st_report import st_report_box
from swagtag.st_utils.states_swag_tag import init_session_states


def app():
    st.set_page_config(
        page_title=load_dash_conf(default=True)['page_title'],
        layout="wide",
    )
    init_session_states(page="annotate")

    st.title(st.session_state.dash_conf['title'])


    # with c1:
    #     st_report_box()
    #     st_annotation_box()

    tab_main, tab_settings = st.tabs(
        [
            "Reports & images",
            "Settings"
        ]
    )

    # sidebar
    with tab_main:
        with st.sidebar:
            image_sidebar()
            st_report_box()
        c1, c2 = st.columns([st.session_state["frac_img"], 100 - st.session_state["frac_img"]])
        with c1:
            tabs = st.tabs([
                f"Image {im_no}" for im_no in
                range(st.session_state['images'].__len__())
            ])
            fig_spots = st_image_box(tabs)
        st_annotation_box()
        # for tab in tabs
        # with c2:
        #     image_spot = st.container()
        # display images

    with tab_settings:
        settings()


if __name__ == '__main__':
    app()
