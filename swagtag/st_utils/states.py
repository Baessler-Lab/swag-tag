from collections import defaultdict

import pandas as pd
import streamlit as st

from annotation.io import load_annotations
from config.config import db_conf, sql_conf
from config.load_config import load_dash_conf
from data_load.image_buffer import load_images_for_study
from data_load.report_load import load_report_for_study
from sql.db_utils import connect_to_db, read_table_to_df
from sql.init_db import create_or_check_db_and_tables


def update_case(case_no: int):
    st.session_state['case_no'] = case_no
    st.session_state['cur_study_instance_uid'] = st.session_state['map_study_instance_uid_accession_number'].iloc[
        st.session_state['case_no']
    ].loc['StudyInstanceUID']
    st.session_state['cur_accession_number'] = st.session_state['map_study_instance_uid_accession_number'].iloc[
        st.session_state['case_no']
    ].loc['AccessionNumber']


def update_images(inplace: bool = True):
    images = load_images_for_study(
        StudyInstanceUID=st.session_state['cur_study_instance_uid'],
        df=st.session_state['image_uris_dataframe']
    )
    if inplace:
        st.session_state['images'] = images
    else:
        return images


def update_report(inplace: bool = True):
    report = load_report_for_study(
        accession_number=lookup_accession_number(
            st.session_state['map_study_instance_uid_accession_number'],
            st.session_state['cur_study_instance_uid'],
        ),
        conn=st.session_state['db_conn']
    )
    if inplace:
        st.session_state['report'] = report
    else:
        return report


def update_annotation(inplace: bool = True, annotation_id: str = None) -> None | dict:
    """

    :param inplace: if true, the session_state 'current_annotation' is overwritten
    :param annotation_id: defaults to None, then the last annotation is returned/set
    :return: (only if not inplace) a dict containing the annotation info
    """
    annotations = load_annotations(
        study_instance_uid=st.session_state['cur_study_instance_uid'],
        conn=st.session_state['db_conn']
    )
    if len(annotations) == 0:
        # no stored annotation
        # set defaults
        annotation = {}
        for tag in st.session_state.dash_conf['annotation_tags']:
            annotation_meta = defaultdict(lambda: 0)
            # if tag in tag in st.session_state['tags']:
            for attribute in st.session_state.dash_conf['annotation_attributes']:
                def_val = st.session_state.dash_conf[f'default_annotation_{attribute}']
                annotation_meta[attribute] = [int(val) for val in def_val] \
                    if isinstance(def_val, list) else int(def_val)
                # annotation_meta.update({
                #     'probability': int(st.session_state.dash_conf[f'default_annotation_probability']),
                #     'severity': int(st.session_state.dash_conf[f'default_annotation_severity']),
                #     'urgency': int(st.session_state.dash_conf[f'default_annotation_urgency']),
                #     'side': int(st.session_state.dash_conf[f'default_annotation_side']),
                #     'left_height': st.session_state.dash_conf[f'default_annotation_left_height'],
                #     'right_height': st.session_state.dash_conf[f'default_annotation_right_height'],
                # })
            annotation[tag] = annotation_meta
    else:
        if annotation_id is not None:
            annotation = annotations[annotation_id][sql_conf['result_table']['json_col']]
        else:
            annotation = next(reversed(annotations.values()))[sql_conf['result_table']['json_col']]

    # identify non-zero tags (backward-compatibility):
    active_tags = []
    for tag in annotation.keys():
        for attribute in st.session_state.dash_conf['annotation_attributes']:

            try:
                att = annotation[tag][attribute]
                if attribute == 'probability':
                    if att > 0:
                        active_tags.append(tag)
                # type conversion to new integer based jsons
                non_def_val = annotation[tag][attribute]
                annotation[tag][attribute] = [int(val) for val in non_def_val] \
                    if isinstance(non_def_val, list) else int(non_def_val)
            except KeyError:
                # backward compatibility for empty annotation_tags
                # annotation[tag] = {
                #     'probability': int(st.session_state.dash_conf[f'default_annotation_probability']),
                #     'severity': int(st.session_state.dash_conf[f'default_annotation_severity']),
                #     'urgency': int(st.session_state.dash_conf[f'default_annotation_urgency']),
                #     'side': int(st.session_state.dash_conf[f'default_annotation_side']),
                #     'left_height': st.session_state.dash_conf[f'default_annotation_height'],
                #     'right_height': st.session_state.dash_conf[f'default_annotation_height'],
                # }
                def_val = st.session_state.dash_conf[f'default_annotation_{attribute}']
                annotation[tag][attribute] = [int(val) for val in def_val] \
                    if isinstance(def_val, list) else int(def_val)
            # pass

        # fill missing tag attributes

    annotation['tags'] = active_tags

    # reset widget 'tags'
    if f"tags_{st.session_state['cur_study_instance_uid']}" in st.session_state:
        del st.session_state[f"tags_{st.session_state['cur_study_instance_uid']}"]

    if inplace:
        st.session_state['current_annotations'] = annotations
        st.session_state['current_annotation'] = annotation
    else:
        return annotation


def update_config():
    if st.session_state.latest:
        config_id = None
    else:
        config_id = st.session_state['selected_config_id']
    st.session_state['dash_conf'] = load_dash_conf(
        conn=st.session_state.db_conn,
        config_id=config_id,
        default=False,
    )
    update_case(st.session_state['dash_conf']['default_case_no'])
    update_images(inplace=True)
    update_report(inplace=True)
    update_annotation(inplace=True)


@st.cache_data
def get_mapping_study_instance_uid_to_accession_number() -> pd.DataFrame:
    return read_table_to_df(
        table_name=sql_conf['image_uris_table']['table_name'],
        cols_to_load=['StudyInstanceUID', 'AccessionNumber'],
        prim_key=sql_conf['image_uris_table']['prim_key'],
        conn=st.session_state['db_conn'],
    ).drop_duplicates(subset=['StudyInstanceUID', 'AccessionNumber'], inplace=False)


@st.cache_data
def get_image_uris_dataframe() -> pd.DataFrame:
    return read_table_to_df(
        table_name=sql_conf['image_uris_table']['table_name'],
        cols_to_load=['StudyInstanceUID', 'SeriesInstanceUID', 'image_uri'],
        prim_key=sql_conf['image_uris_table']['prim_key'],
        conn=st.session_state['db_conn'],
    ).drop_duplicates(inplace=False)


def lookup_accession_number(df: pd.DataFrame, study_instance_uid: str) -> str:
    acc_no = df.drop_duplicates(subset='StudyInstanceUID', inplace=False).loc[
        df['StudyInstanceUID'] == study_instance_uid, 'AccessionNumber']
    assert len(acc_no) == 1
    return acc_no.squeeze()


def init_session_states():
    # init database
    if 'table_inited' not in st.session_state:
        st.session_state['table_inited'] = True
        create_or_check_db_and_tables(
            replace_db=False, replace_tables=False,
            db_config=db_conf,
            sql_config=sql_conf)

    # connect to database
    if 'db_conn' not in st.session_state:
        st.session_state['db_conn'] = connect_to_db(db_config=db_conf)

    # load dashboard config
    if 'dash_conf' not in st.session_state:
        st.session_state['dash_conf'] = load_dash_conf(
            conn=st.session_state.db_conn,
            config_id='default',
            default=True,
        )

    # load cases
    if 'map_study_instance_uid_accession_number' not in st.session_state:
        st.session_state['map_study_instance_uid_accession_number'] = \
            get_mapping_study_instance_uid_to_accession_number()
    if 'image_uris_dataframe' not in st.session_state:
        st.session_state['image_uris_dataframe'] = get_image_uris_dataframe()

    # init case iterator
    if 'case_no' not in st.session_state:
        st.session_state['case_no'] = st.session_state.dash_conf['default_case_no']
    update_case(st.session_state['case_no'])

    # load images into case iterator
    if 'images' not in st.session_state:
        st.session_state['images'] = update_images(inplace=False)

    # init slice_no
    if 'slice_no' not in st.session_state:
        st.session_state['slice_no'] = 0

    # init windowing for images
    if 'window_borders' not in st.session_state:
        st.session_state['window_borders'] = st.session_state.dash_conf['window_default_range']

    # load reports into case iterator
    if 'report' not in st.session_state:
        st.session_state['report'] = update_report(inplace=False)

    # load annotations for the case into case iterator
    if 'current_annotation' not in st.session_state:
        st.session_state['current_annotation'] = update_annotation(inplace=False)
