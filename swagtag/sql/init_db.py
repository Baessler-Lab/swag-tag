import logging
import typing

from psycopg2.errors import DuplicateDatabase, DuplicateTable

from config.config import db_conf, sql_conf
from .db_utils import create_db, create_table, force_drop_tables, drop_db, delete_table, connect_to_db

log = logging.Logger(__name__)


def create_or_check_db_and_tables(
        replace_db: bool = False,
        replace_tables: bool = False,
        db_config: typing.Mapping = db_conf,
        sql_config: typing.Mapping = sql_conf,
):
    # check for existing database and replace if wanted
    try:
        create_db(db_config=db_config)
    except DuplicateDatabase:  # exists
        if replace_db:
            # delete old db
            force_drop_tables(db_config=db_config)
            drop_db(db_config=db_config)

            # build new db
            create_db(db_config=db_config)
        else:
            pass

    # connect to db
    conn = connect_to_db(db_config=db_config)
    try:
        # # DEBUG:
        # delete_table(table_name=sql_config['result_table']['table_name'], conn=conn)

        # create table if not there
        for table, table_conf in sql_config.items():
            try:
                create_table(conn=conn, table_conf=table_conf)
            except DuplicateTable:
                if replace_tables:
                    delete_table(table_name=table_conf['table_name'], conn=conn)
                    create_table(conn=conn, table_conf=table_conf)
    finally:
        conn.close()
