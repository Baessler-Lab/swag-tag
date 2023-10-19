import streamlit as st

if not 'page' in st.session_state:
    st.session_state['page'] = 'llm'

from config.load_config import load_dash_conf
from swagtag.st_utils.sidebar_llm import sidebar
from swagtag.st_utils.st_annotation_llm import st_annotation_box
from swagtag.st_utils.st_report import st_report_box
from swagtag.st_utils.states_llm import init_session_states


def app():
    st.set_page_config(
        page_title=load_dash_conf(default=True)['page_title'],
        layout="wide",
    )
    init_session_states(page='llm')

    st.title(st.session_state.dash_conf['title'])
    c1, c2 = st.columns((0.5, 0.7))
    with c1:
        st_report_box()
    with c2:
        st_annotation_box()

    # sidebar
    sb = sidebar()


if __name__ == '__main__':
    app()
