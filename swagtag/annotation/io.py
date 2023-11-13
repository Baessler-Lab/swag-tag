import typing
from collections import defaultdict
from datetime import datetime

from psycopg2._psycopg import connection

from config.config import sql_conf
from sql.db_utils import insert_into_db, read_jsons_to_list_of_dicts


# noinspection PyTypeChecker
def save_annotation(study_instance_uid: str,
                    accession_number: str,
                    annotation: typing.Mapping,
                    author: str,
                    conn: connection):
    # build dict for insertion as row into postgres
    vals_to_insert = defaultdict(lambda: None)
    vals_to_insert[sql_conf['result_table']['timestamp_col']] = datetime.utcnow()
    vals_to_insert[sql_conf['result_table']['prim_key']] = None  # is SERIAL
    vals_to_insert[sql_conf['result_table']['json_col']] = dict(**annotation)
    vals_to_insert[sql_conf['result_table']['user_col']] = author

    # set case id/ report id
    vals_to_insert['StudyInstanceUID'] = study_instance_uid
    vals_to_insert['AccessionNumber'] = accession_number

    insert_into_db(
        dicom_dicts=[vals_to_insert],
        conn=conn,
        table_conf=sql_conf['result_table'],
        upsert=True,
    )


# noinspection PyTypeChecker
def load_annotations(study_instance_uid: str,
                     conn: connection) -> typing.Dict[str, typing.Dict[str, dict]]:
    # read annotations from database
    annotations = read_jsons_to_list_of_dicts(
        table_name=sql_conf['result_table']['table_name'],
        acc_cols_to_load=[sql_conf['result_table']['prim_key'],
                          sql_conf['result_table']['timestamp_col'],
                          sql_conf['result_table']['user_col']],
        json_col=sql_conf['result_table']['json_col'],
        timestamp_col=sql_conf['result_table']['timestamp_col'],
        prim_key='StudyInstanceUID',
        ids_to_load=[study_instance_uid],
        conn=conn,
    )

    return {annotation[sql_conf['result_table']['prim_key']]: annotation for annotation in annotations}


def get_last_user_annotation(annotations_meta: typing.Mapping[str | int, typing.Mapping[str, typing.Any]],
                             annotations: typing.Mapping[str | int, typing.Mapping[str, typing.Any]],
                             user: str,
                             dash_conf: typing.Mapping[str, typing.Any],
                             ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, str | None]]:
    user_annotations_meta = {
        key: val for key, val in
        annotations_meta.items() if val[sql_conf['result_table']['user_col']] == user
    }
    try:
        last_annotation_id = next(reversed(user_annotations_meta.keys()))
        annotation = annotations[last_annotation_id][sql_conf['result_table']['json_col']]
        annotation_meta = user_annotations_meta[last_annotation_id]
    except StopIteration:
        # no annotation for this user left
        annotation, annotation_meta = get_default_annotation_and_meta(
            # llm_user=dash_conf.get("llm_user", "llama-2-70b-8bit")
        )
    return annotation, annotation_meta


def get_default_annotation_and_meta(
        llm_user: str = None
):
    # st.session_state.dash_conf['annotation_attributes']
    # annotation = defaultdict(lambda: None)
    # for tag in dash_conf['annotation_tags']:
    #     tag: str
    #     annotation_meta = defaultdict(lambda: 0)
    #     # if tag in tag in st.session_state['tags']:
    #     for attribute in dash_conf['annotation_attributes']:
    #         def_val = dash_conf[f'default_annotation_{attribute}']
    #         annotation_meta[attribute] = [int(val) for val in def_val] \
    #             if isinstance(def_val, list) else int(def_val)
    #     annotation[tag] = annotation_meta
    annotation = None
    annotation_meta = defaultdict(lambda: None)


    return annotation, annotation_meta




def llm_default_annotation_meta(node: typing.Dict[str, typing.Any]):
    res_node = {'id': node['id'], 'name': node['name']}


    if "single-select-from-children" in node:
        res_node["single-select-from-children"] = node["single-select-from-children"]
    if 'activatable' in node:
        res_node['activated'] = False
    if "single-selectable" in node:
        res_node["single-selectable"] = True
    if 'children' in node:
        children = node['children']
        res_node['children'] = [
            llm_default_annotation_meta(child)
            for child in children
        ]
    return res_node


def lookup_label_from_annotation_meta(
        annotation_id: str | None,
        annotations_meta: typing.Mapping[str, typing.Any],

) -> str:
    if annotation_id is None:
        return "empty"
    cur_meta = annotations_meta[annotation_id]
    ret_str = f"{cur_meta[sql_conf['result_table']['user_col']]}: {cur_meta[sql_conf['result_table']['timestamp_col']]}"

    return ret_str
