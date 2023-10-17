from collections import defaultdict

import pandas as pd
import streamlit as st

from annotation.io import load_annotations, get_last_user_annotation, get_default_annotation_and_meta
from config.config import db_conf, sql_conf
from config.load_config import load_dash_conf
from data_load.image_buffer import load_images_for_study
from data_load.report_load import load_report_for_study
from sql.db_utils import connect_to_db, read_table_to_df
from sql.init_db import create_or_check_db_and_tables
from user.manage import read_user_dicts


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
    annotations_meta = {
        aid: {
            key: val for key, val in ann.items() if key != sql_conf['result_table']['json_col']
        }
        for aid, ann in annotations.items()
    }

    if len(annotations) == 0:
        # no stored annotation
        # set defaults
        annotation, annotation_meta = get_default_annotation_and_meta(st.session_state.dash_conf)
    else:
        if annotation_id is not None:
            annotation = annotations[annotation_id][sql_conf['result_table']['json_col']]
            annotation_meta = annotations_meta[annotation_id]
        else:
            # annotation = next(reversed(annotations.values()))[sql_conf['result_table']['json_col']]
            annotation, annotation_meta = get_last_user_annotation(annotations_meta=annotations_meta,
                                                                   annotations=annotations,
                                                                   user=st.session_state.current_user,
                                                                   dash_conf=st.session_state.dash_conf)
            # user_annotations_meta = {
            #     key: val for key, val in
            #     annotations_meta.items() if val[sql_conf['result_table']['user_col']] == st.session_state.current_user
            # }
            # last_annotation_id = next(reversed(user_annotations_meta.keys()))
            # annotation = annotations[annotation_id][sql_conf['result_table']['json_col']]

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
        st.session_state['current_annotations_meta'] = annotations_meta
        st.session_state['current_annotation'] = annotation
        st.session_state['current_annotation_meta'] = annotation_meta
    else:
        return annotation


def update_users(inplace: bool = True):
    if inplace:
        st.session_state['users_dict'] = read_user_dicts(conn=st.session_state.db_conn)
        st.session_state['users'] = [user_dict[sql_conf['user_table']['user_col']] for user_dict in
                                     st.session_state['users_dict'].values()]
    else:
        return read_user_dicts(conn=st.session_state.db_conf), [user_dict[sql_conf['user_table']['user_col']] for
                                                                user_dict in
                                                                st.session_state['users_dict'].values()]


def update_user(user_name: str = None, user_id: int | str = None, inplace: bool = True):
    if user_name is None and user_id is None:
        cur_user = 'default'
    else:
        if user_name is not None:
            print(user_name, st.session_state['users'])
            assert user_name in st.session_state['users']
            cur_user = user_name
        else:
            cur_user = st.session_state['users_dict'][user_id][sql_conf['user_table']['user_col']]

    if inplace:
        st.session_state['current_user'] = cur_user
    else:
        return cur_user


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

    if 'users_dict' not in st.session_state or 'users' not in st.session_state:
        # st.session_state['users'] = read_user_dicts(conn=st.session_state.db_conf)
        update_users(inplace=True)

    # init user and user_dicts
    if 'current_user' not in st.session_state:
        update_user(user_name=None, user_id=None, inplace=True)

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
        # st.session_state['current_annotation'] =
        update_annotation(inplace=True)
