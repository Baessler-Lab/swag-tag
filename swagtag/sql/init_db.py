import logging

from psycopg2.errors import DuplicateDatabase, DuplicateTable

from config.config import db_conf, sql_conf
from .db_utils import create_db, create_table, force_drop_tables, drop_db, delete_table, connect_to_db

log = logging.Logger(__name__)


def create_or_check_db_and_tables(
        replace_db: bool = False,
        replace_tables: bool = False,
):
    # check for existing database and replace if wanted
    try:
        create_db(db_config=db_conf)
    except DuplicateDatabase:  # exists
        if replace_db:
            # delete old db
            force_drop_tables(db_config=db_conf)
            drop_db(db_config=db_conf)

            # build new db
            create_db(db_config=db_conf)
        else:
            pass

    # connect to db
    conn = connect_to_db(db_config=db_conf)

    # create table if not there
    for table, table_conf in sql_conf:
        try:
            create_table(conn=conn, table_conf=sql_conf)
        except DuplicateTable:
            if replace_tables:
                delete_table(table_name=table_conf['table_name'], conn=conn)
                create_table(conn=conn, table_conf=sql_conf)
