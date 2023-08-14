from collections import defaultdict
from datetime import datetime

from psycopg2._psycopg import connection

from config.config import sql_conf
from sql.db_utils import insert_into_db, read_jsons_to_list_of_dicts


# noinspection PyTypeChecker
def add_new_user(user_name: str, conn: connection):
    user_table_conf = sql_conf['user_table']

    vals_to_insert = defaultdict(lambda: None)
    vals_to_insert[user_table_conf['timestamp_col']] = datetime.utcnow()
    vals_to_insert[user_table_conf['user_col']] = user_name

    insert_into_db(
        dicom_dicts=[vals_to_insert],
        conn=conn,
        table_conf=user_table_conf,
        upsert=True,
    )


# noinspection PyTypeChecker
def read_user_dicts(conn: connection, order_by_name: bool = True):
    user_table_conf = sql_conf['user_table']

    if order_by_name:
        order_col = user_table_conf['user_col']
    else:
        order_col = user_table_conf['timestamp_col']

    list_of_user_dicts = read_jsons_to_list_of_dicts(
        table_name=user_table_conf['table_name'],
        acc_cols_to_load=list(user_table_conf['columns'].keys()),
        ids_to_load=None,
        timestamp_col=order_col,
        prim_key=user_table_conf['prim_key'],
        json_col=None,
        conn=conn,
    )
    return {val[user_table_conf['prim_key']]: val for val in list_of_user_dicts}

    #                 table_name=sql_conf['config_table']['table_name'],
    #                 acc_cols_to_load=list(sql_conf['config_table']['columns'].keys()),
    #                 ids_to_load=config_id,
    #                 timestamp_col=sql_conf['config_table']['timestamp_col'],
    #                 json_col=sql_conf['config_table']['json_col'],
    #                 prim_key=sql_conf['config_table']['prim_key'],
    #                 conn=conn,
