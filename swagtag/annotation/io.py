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
                    conn: connection):
    # build dict for insertion as row into postgres
    vals_to_insert = defaultdict(lambda: None)
    vals_to_insert[sql_conf['result_table']['timestamp_col']] = datetime.utcnow()
    vals_to_insert[sql_conf['result_table']['prim_key']] = None  # is SERIAL
    vals_to_insert[sql_conf['result_table']['json_col']] = dict(**annotation)

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
        acc_cols_to_load=[sql_conf['result_table']['prim_key'], sql_conf['result_table']['timestamp_col']],
        json_col=sql_conf['result_table']['json_col'],
        timestamp_col=sql_conf['result_table']['timestamp_col'],
        prim_key='StudyInstanceUID',
        ids_to_load=[study_instance_uid],
        conn=conn,
    )

    return {annotation[sql_conf['result_table']['prim_key']]: annotation for annotation in annotations}
