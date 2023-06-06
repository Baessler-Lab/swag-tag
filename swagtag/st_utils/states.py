import streamlit as st

from config.config import db_conf
from io.img_load import load_images
from sql.db_utils import connect_to_db


def init_session_states():
    # init case iterator
    if 'case_no' not in st.session_state:
        st.session_state['case_no'] = 0

    # connect to database
    if 'db_conn' not in st.session_state:
        st.session_state['db_conn'] = st.cache_resource(ttl=600)(connect_to_db(db_config=db_conf))

    # load images into case iterator
    if 'images' not in st.session_state:
        st.session_state['images'] = load_images()
