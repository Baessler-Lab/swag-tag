import typing
from collections import defaultdict
from datetime import datetime

from psycopg2._psycopg import connection

from config.config import sql_conf
from sql.db_utils import insert_into_db


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
