import logging
import typing
from collections import defaultdict
from datetime import datetime

import pandas as pd
from psycopg2._psycopg import connection

from config.config import dash_conf, sql_conf
from sql.db_utils import read_jsons_to_list_of_dicts, insert_into_db

log = logging.getLogger(__name__)


def load_dash_conf(
        conn: connection = None,
        config_id: str | typing.List[str] = None,
        default: bool = True,
) -> dict:
    if default:
        return dash_conf
    else:
        try:
            if conn is None:
                raise ValueError('You need to provice a Connection to retrieve a config from Postgres.')

            if isinstance(config_id, str):
                config_id = [config_id]

            configs_list = read_jsons_to_list_of_dicts(
                table_name=sql_conf['config_table']['table_name'],
                acc_cols_to_load=list(sql_conf['config_table']['columns'].keys()),
                ids_to_load=config_id,
                timestamp_col=sql_conf['config_table']['timestamp_col'],
                json_col=sql_conf['config_table']['json_col'],
                prim_key=sql_conf['config_table']['prim_key'],
                conn=conn,
            )
            latest_dashboard_config = configs_list[-1][sql_conf['config_table']['json_col']]
            return latest_dashboard_config
        except Exception as exc:
            log.exception('Error loading the config from the database. Default config is returned instead.')
            return dash_conf


def load_dash_conf_meta(
        conn: connection = None,
) -> pd.DataFrame:
    if conn is None:
        raise ValueError('You need to provice a Connection to retrieve a config from Postgres.')

    configs_list = read_jsons_to_list_of_dicts(
        table_name=sql_conf['config_table']['table_name'],
        acc_cols_to_load=[key for key in sql_conf['config_table']['columns'].keys() if
                          key != sql_conf['config_table']['json_col']],
        timestamp_col=sql_conf['config_table']['timestamp_col'],
        ids_to_load=None,
        json_col=None,
        prim_key=sql_conf['config_table']['prim_key'],
        conn=conn,
    )
    config_meta = pd.DataFrame(configs_list)
    return config_meta


def lookup_label_from_config_meta(
        config_id: str,
        config_meta: pd.DataFrame,

):
    return ' '.join(config_meta.loc[
                        config_meta[sql_conf['config_table']['prim_key']] == config_id,
                        [sql_conf['config_table']['prim_key'], sql_conf['config_table']['timestamp_col']]
                    ].squeeze().apply(lambda x: str(x)).values)


def store_configuration(config_id: str, dashboard_configuration: typing.MutableMapping, conn: connection):
    vals_to_insert = defaultdict(lambda: None)
    vals_to_insert[sql_conf['config_table']['timestamp_col']] = datetime.utcnow()
    vals_to_insert[sql_conf['config_table']['prim_key']] = config_id
    dashboard_configuration['config_id'] = config_id
    vals_to_insert[sql_conf['config_table']['json_col']] = dashboard_configuration

    insert_into_db(
        dicom_dicts=[vals_to_insert],
        conn=conn,
        table_conf=sql_conf['config_table'],
        upsert=True,
    )
