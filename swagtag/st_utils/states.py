import pandas as pd
import streamlit as st

from config.config import db_conf, sql_conf
from data_load.image_buffer import load_images_for_study
from data_load.report_load import load_report_for_study
from sql.db_utils import connect_to_db, read_table_to_df


def update_case(case_no: int):
    st.session_state['case_no'] = case_no
    st.session_state['cur_study_instance_uid'] = st.session_state['map_study_instance_uid_accession_number'][
        st.session_state['case_no']
    ]


def lookup_accession_number(df: pd.DataFrame, study_instance_uid: str):
    return df.loc[df['StudyInstanceUID'] == study_instance_uid, 'AccessionNumber']


def init_session_states():
    # connect to database
    if 'db_conn' not in st.session_state:
        st.session_state['db_conn'] = st.cache_resource(ttl=600)(connect_to_db(db_config=db_conf))

    # load cases
    if 'map_study_instance_uid_accession_number' not in st.session_state:
        st.session_state['map_study_instance_uid_accession_number'] = st.cache_data()(read_table_to_df(
            table_name=sql_conf['image_uris_table']['table_name'],
            cols_to_load=['StudyInstanceUID', 'AccessionNumber'],
            prim_key=sql_conf['image_uris_table']['prim_key'],
            conn=st.session_state['db_conn'],
        ).unique())

    # init case iterator
    if 'case_no' not in st.session_state:
        st.session_state['case_no'] = 0
    update_case(st.session_state['case_no'])

    # load images into case iterator
    if 'images' not in st.session_state:
        st.session_state['images'] = load_images_for_study(
            st.session_state['cur_study_instance_uid'], st.session_state['map_study_instance_uid_accession_number']
        )

    # load reports into case iterator
    if 'report' not in st.session_state:
        st.session_state['report'] = load_report_for_study(
            accession_number=lookup_accession_number(
                st.session_state['map_study_instance_uid_accession_number']
            ),
            conn=st.session_state['db_conn']
        )
