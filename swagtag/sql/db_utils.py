import logging
import typing
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime

import pandas as pd
import psycopg2
from arviz import InferenceData
from arviz.data.base import _make_json_serializable
from psycopg2 import sql
from psycopg2._psycopg import connection
from psycopg2.extras import Json, execute_batch
from sqlalchemy import create_engine

from config.config import db_conf, sql_conf

log = logging.Logger(__name__)


def connect_to_db(db_config: db_conf) -> connection:
    conn = psycopg2.connect(**db_config)
    return conn


def drob_db(db_conf: Mapping):
    conn = connect_to_db(db_conf)
    cur = conn.cursor()
    conn.autocommit = True
    cur.execute(
        f"DROP DATABASE {db_conf['dbname']} WITH(FORCE);"
    )
    conn.close()


def force_drop_db(db_config: Mapping):
    """
    Drop all tables of database you given.
    """

    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(0)
    except Exception as exc:
        raise RuntimeError("Unable to connect to the database.") from exc

    try:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """SELECT table_schema,table_name FROM information_schema.tables
                     WHERE table_schema = 'public' ORDER BY table_schema,table_name"""
                )
            )
            rows = cur.fetchall()
            for row in rows:
                log.warning("dropping table: %s" % row[1])
                drop_stm = sql.SQL("DROP TABLE {tab_name} CASCADE;").format(tab_name=sql.Identifier(row[1]))
                cur.execute(drop_stm)


    except Exception as exc:
        raise RuntimeError("Error:") from exc
    finally:
        conn.close()


def create_db(db_conf: Mapping, sql_conf: Mapping):
    conn = connect_to_db(db_conf)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'CREATE DATABASE {db_conf["dbname"]}')

    finally:
        conn.close()

    create_table(db_conf, sql_conf, xtra_tags={"study_tags": "StudyDateTime"})


def create_table(
        db_conf: Mapping,
        sql_conf: Mapping,
        xtra_tags: typing.Mapping[str, typing.List[str] | str] = None
):
    conn = connect_to_db(db_conf)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # create a patient table

            table_name = "patient_tags"
            id = "PatientID"
            tag_definitions = sql.SQL(', ').join([sql.SQL("{tag} character varying(256)").format(
                tag=sql.Identifier(tag))
                for tag in sql_conf["patient_tags"]
                if tag not in sql_conf["id_levels"]])
            constraints = sql.SQL("PRIMARY KEY ({id})").format(id=sql.Identifier(id))

            create_cmd = sql.SQL(
                """
                CREATE TABLE {table_name} 
                                    (
                                        {tag_definitions},
                                        {constraints}

                                    )
                                    WITH (
                                        FILLFACTOR = 70
                                    )
                                    TABLESPACE pg_default;
                """).format(
                table_name=sql.Identifier(table_name),
                pk_id=sql.Identifier(f"PK_{id}"),
                tag_definitions=tag_definitions,
                constraints=constraints,
            )

            log.warning(create_cmd)
            cur.execute(create_cmd)

            # create a study table
            # TODO: mk yaml out of this
            study_spec = dict(
                table_name="study_tags",
                # id="StudyInstanceUID",
                prim_key=sql.Identifier("StudyInstanceUID"),
                foreign_id="PatientID",
                foreign_table="patient_tags",
            )
            series_spec = dict(
                table_name="series_tags",
                prim_key=sql.Identifier("SeriesInstanceUID"),
                foreign_id="StudyInstanceUID",
                foreign_table="study_tags",
            )
            instance_spec = dict(
                table_name="instance_tags",
                id="InstanceNumber",
                prim_key=sql.SQL(', ').join([
                    sql.Identifier("InstanceNumber"),
                    sql.Identifier("SeriesInstanceUID"),
                ]),
                foreign_id="SeriesInstanceUID",
                # foreign_id="StudyInstanceUID",
                foreign_table="series_tags",
            )
            table_specs = [
                study_spec,
                series_spec,
                instance_spec,
            ]

            for table_spec in table_specs:
                # add xtra_tags
                tab_name = table_spec["table_name"]
                cols_to_create = sql_conf[tab_name]

                try:
                    ts_tags_to_add = xtra_tags[tab_name]

                except KeyError:
                    # no tag for table_name
                    ts_tags_to_add = []
                    pass

                tag_definitions = sql.SQL(', ').join(
                    # [sql.SQL("{foreign_id} character varying(256)").format(
                    #     foreign_id=sql.Identifier(table_spec["foreign_id"])), ] +

                    [sql.SQL("{tag} character varying(256)").format(
                        tag=sql.Identifier(tag))
                        for tag in cols_to_create]
                    # add timestamp directly in appropriate format TODO: Consider Timestamp in UTC
                    + [sql.SQL("{tag} timestamp").format(tag=sql.Identifier(tag))
                       for tag in ts_tags_to_add]
                )
                constraints = sql.SQL(', ').join(
                    [sql.SQL("PRIMARY KEY ({prim_key})").format(prim_key=table_spec["prim_key"]),
                     sql.SQL("FOREIGN KEY ({foreign_id}) REFERENCES {foreign_table}").format(
                         foreign_id=sql.Identifier(table_spec["foreign_id"]),
                         foreign_table=sql.Identifier(table_spec["foreign_table"])
                     ),
                     ]
                )

                create_cmd = sql.SQL(
                    """
                    CREATE TABLE {table_name} 
                    (
                        {tag_definitions}, 
                        {constraints}
                    )
                    WITH (
                        FILLFACTOR = 70
                    )
                    TABLESPACE pg_default;
                    """).format(
                    table_name=sql.Identifier(table_spec["table_name"]),
                    # pk_id=sql.Identifier(f"PK_{id}"),
                    # id=sql.Identifier(id),
                    tag_definitions=tag_definitions,
                    constraints=constraints,
                )

                log.warning(create_cmd)
                cur.execute(create_cmd)

            # create a table with jsonb column
            cur.execute(
                "CREATE TABLE instance_tags_json (id serial PRIMARY KEY, data jsonb)"
            )
    finally:
        conn.close()


def delete_table(table_name: str, db_config: Mapping = db_conf, ):
    try:
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(0)
    except Exception as exc:
        raise RuntimeError("Unable to connect to the database.") from exc

    try:
        with conn.cursor() as cur:
            log.warning("dropping table: %s" % table_name)
            drop_stm = sql.SQL("DROP TABLE {tab_name} CASCADE;").format(tab_name=sql.Identifier(table_name))
            cur.execute(drop_stm)

    except psycopg2.errors.UndefinedTable:
        pass

    except Exception as exc:
        raise RuntimeError("Error:") from exc
    finally:
        conn.close()


def post_to_db(db_conf, dicom_dicts: list[dict[str, str]]):
    conn = connect_to_db(db_conf)
    cur = conn.cursor()

    for dicom_dict in dicom_dicts:
        cur.execute(
            "INSERT INTO instance_tags_json (data) VALUES (%s)", (Json(dicom_dict),)
        )

    conn.commit()
    cur.close()
    conn.close()


def connect_or_take_connection(conn: connection = None, db_config: Mapping = None) -> connection:
    if conn is not None and conn.closed == 0:
        # assert isinstance(conn, connection)
        return conn
    else:
        try:
            conn = connect_to_db(db_config)
            assert conn.closed == 0
            return conn
        except AssertionError as exc:
            raise RuntimeError('Connection is not open') from exc
        except Exception as exc:
            raise RuntimeError('Failed to open a connection to the database') from exc


def create_jsonb_table(table_name: str,
                       prim_id: str = 'study_type',
                       json_data_key: str = 'data',
                       conn: connection = None,
                       db_conf: typing.Mapping = None,
                       ):
    tag_definitions = sql.SQL(', ').join([
        sql.SQL("{tag} jsonb").format(tag=sql.Identifier(json_data_key)),
        sql.SQL("{tag} character varying(256)").format(tag=sql.Identifier(prim_id))
    ])

    constraints = sql.SQL(', ').join(
        [sql.SQL("PRIMARY KEY ({prim_key})").format(prim_key=sql.Identifier(prim_id)),
         ]
    )

    create_cmd = sql.SQL(
        """
        CREATE TABLE {table_name} 
        (
            {tag_definitions}, 
            {constraints}
        )
        WITH (
            FILLFACTOR = 70
        )
        TABLESPACE pg_default;
        """).format(
        table_name=sql.Identifier(table_name),
        tag_definitions=tag_definitions,
        constraints=constraints,
    )

    conn = connect_or_take_connection(conn, db_conf)
    try:
        with conn.cursor() as cur:
            cur.execute(query=create_cmd)
            # data = cur.fetchall()
            #
            # cols = [col[0] for col in cur.description]
            #
            # return pd.DataFrame(data, columns=cols)
            conn.commit()
    finally:
        conn.close()


def insert_inference_data_as_json_into_db(
        trace: InferenceData | typing.Mapping[str, InferenceData],
        table_name: str,
        id: str = None,
        prim_id: str = 'study_type',
        conn: connection = None,
        db_config: typing.Mapping = db_conf,
):
    #
    if isinstance(trace, Mapping):
        cols_to_insert = [prim_id, 'data']
        values = [{prim_id: key, 'data': Json(_make_json_serializable(val.to_dict()))} for key, val in trace.items()]

    elif isinstance(trace, InferenceData):
        if id is None:
            raise ValueError('You need to specify an id to store in the table')
        cols_to_insert = [prim_id, 'data']
        values = [{prim_id: id, 'data': Json(_make_json_serializable(trace.to_dict()))}]
    else:
        raise NotImplementedError('Please provide either a mapping or an InferenceData object together with id')

    conn = connect_or_take_connection(conn, db_config)
    query = sql.SQL(
        """INSERT INTO {tab_name} ({col_names}) VALUES ({vals}) 
        ON CONFLICT ({prim_key}) DO UPDATE SET ({col_names}) = ({exclude_names});"""
    ).format(
        tab_name=sql.Identifier(table_name),
        col_names=sql.SQL(', ').join(map(sql.Identifier, cols_to_insert)),
        vals=sql.SQL(', ').join(map(sql.Placeholder, cols_to_insert)),
        prim_key=sql.Identifier(prim_id),
        exclude_names=sql.SQL(', ').join(map(
            lambda x: sql.SQL("excluded.{col}").format(col=sql.Identifier(x)), cols_to_insert))
    )

    try:
        with conn.cursor() as cur:
            execute_batch(cur=cur, sql=query, argslist=values)
            conn.commit()
    finally:
        conn.close()


def query_inference_data_as_json_into_db(
        table_name: str,
        id: str | typing.Sequence[str] = None,
        prim_id: str = 'study_type',
        conn: connection = None,
        db_config: typing.Mapping = None,
) -> InferenceData | typing.Mapping[str, InferenceData]:
    #
    if isinstance(id, str):
        id = [id]

    if len(id) == 1:
        in_any_sql = sql.SQL("= '{ids}'").format(ids=sql.SQL(id[0]))
    elif id is None or len(id) == 0:
        id = []
        in_any_sql = sql.SQL("= '{ids}'").format(ids=sql.SQL(prim_id))
    else:
        in_any_sql = sql.SQL("IN ({ids})").format(ids=sql.SQL(',').join(id))

        raise NotImplementedError('We will consider the default case in future ')

    conn = connect_or_take_connection(conn, db_config)
    query = sql.SQL(
        "SELECT * FROM {tab_name} WHERE {prim_key} {in_any};").format(
        # col_names=sql.SQL(', ').join(map(sql.Identifier, [prim_id, "data"])),
        tab_name=sql.Identifier(table_name),
        prim_key=sql.Identifier(prim_id),
        in_any=in_any_sql,
    )
    # debug
    # query = sql.SQL(
    #     "SELECT * FROM {tab_name}").format(
    #     # col_names=sql.SQL(', ').join(map(sql.Identifier, [prim_id, "data"])),
    #     tab_name=sql.Identifier(table_name),
    #     prim_key=sql.Identifier(prim_id),
    #     in_any=in_any_sql,
    # )
    ret_mapping = defaultdict()
    try:
        with conn.cursor() as cur:
            cur.execute(query=query)
            conn.commit()
            data = cur.fetchall()
            # convert to InferenceData
            # ret = arviz.convert_to_dataset(dta_dict['data_vars'], coords=dta_dict['coords'], dims=dta_dict['dims'])  #, coords=coords, dims=dims)
            # ret_mapping = {id[0]: xarray.Dataset.from_dict(tpl[0]) for tpl in data}
            print(f"Key = {id[0]}, data_len = {len(data)}, conn= {conn} , query = {query}")
            for tpl in data:
                ret_mapping[tpl[1]] = tpl[0]
            # from matplotlib import pyplot as plt
            # for tpl in data:
            #     # arviz.from_dict()
            #     trace = arviz.from_dict(**tpl[0])
            #     # ppc_trace = pymc.sample_posterior_predictive(trace)
            #     arviz.plot_dist(trace.observed_data['pre_mix_likelihood'])
            #     plt.show()

            # return ret_mapping
    except Exception as exc:
        raise RuntimeError(f"Error while loading trace for {id}") from exc
    finally:
        return ret_mapping


def insert_into_db(
        db_conf, dicom_dicts: list[dict[str, str]],
        sql_conf: Mapping,
        xtra_tags: typing.Mapping[str, typing.Sequence[str]] = None,
        upsert: bool = True,
):
    conn = connect_to_db(db_conf)
    try:
        with conn.cursor() as cur:
            conn.autocommit = True

            for name in sql_conf["table_names"]:
                # add xtra_tags
                cols_to_insert = sql_conf[name].copy()
                if xtra_tags is not None:
                    try:
                        if isinstance(xtra_tags[name], list):
                            cols_to_insert += xtra_tags[name]
                        elif isinstance(xtra_tags[name], str):
                            cols_to_insert.append(xtra_tags[name])
                        else:
                            raise NotImplementedError("Not yet considered. Provide list or string!")
                    except KeyError:
                        # no tag for table_name
                        pass

                prim_keys = sql_conf["id_levels"][name]
                if not isinstance(prim_keys, list):
                    prim_keys = [prim_keys, ]

                # build insert statement
                if not upsert:
                    query = sql.SQL(
                        "INSERT INTO {tab_name} ({col_names}) VALUES ({vals}) ON CONFLICT ({prim_key}) DO NOTHING;").format(
                        tab_name=sql.Identifier(name),
                        col_names=sql.SQL(', ').join(map(sql.Identifier, cols_to_insert)),
                        vals=sql.SQL(', ').join(map(sql.Placeholder, cols_to_insert)),
                        prim_key=sql.SQL(', ').join([sql.Identifier(prim_id) for prim_id in prim_keys])
                    )
                else:
                    exclude_names = sql.SQL(', ').join(map(
                        lambda x: sql.SQL("excluded.{col}").format(col=sql.Identifier(x)), cols_to_insert))
                    query = sql.SQL(
                        """INSERT INTO {tab_name} ({col_names}) VALUES ({vals})
                         ON CONFLICT ({prim_key}) DO UPDATE SET ({col_names}) = ({ex_names});""").format(
                        tab_name=sql.Identifier(name),
                        col_names=sql.SQL(', ').join(map(sql.Identifier, cols_to_insert)),
                        ex_names=exclude_names,
                        vals=sql.SQL(', ').join(map(sql.Placeholder, cols_to_insert)),
                        prim_key=sql.SQL(', ').join([sql.Identifier(prim_id) for prim_id in prim_keys])
                    )

                execute_batch(cur=cur, sql=query, argslist=dicom_dicts, page_size=1000)
    finally:
        conn.close()


def read_data_single(
        db_conf: typing.Mapping = db_conf,
        conn: connection = None,
        sql_conf: typing.Mapping = sql_conf,
        table_name: str = 'dashboard_data',
        dt_interval: typing.Tuple[datetime, datetime] = None,
):
    # time selection
    if dt_interval is not None:
        query = sql.SQL(
            """SELECT * FROM {table_name} 
            WHERE {dt_lvl}.{dt_key} >= {lower_stamp} AND {dt_lvl}.{dt_key} < {upper_stamp}"""
        ).format(table_name=sql.Identifier(table_name),
                 lower_stamp=dt_interval[0],
                 upper_stamp=dt_interval[1],
                 dt_key=sql.Identifier("StudyDateTime"),
                 dt_lvl=sql.Identifier("study_tags")
                 ),

    else:
        query = sql.SQL("SELECT * FROM {table_name}").format(table_name=sql.Identifier(table_name))

    # connect to db
    conn = connect_or_take_connection(db_config=db_conf, conn=conn)
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            data = cur.fetchall()

            cols = [col[0] for col in cur.description]

            return pd.DataFrame(data, columns=cols)
    finally:
        pass
        # conn.close()


def read_data_separate(
        db_conf: typing.Mapping = db_conf,
        sql_conf: typing.Mapping = sql_conf,
        levels: typing.List[str] = None  # ['instance_tags', 'series_tags', 'study_tags', 'patient_tags']
):
    # connect to db
    conn = connect_to_db(db_conf=db_conf)
    try:
        df_dict = {}
        for table_name in levels:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT * FROM {table_name}").format(table_name=sql.Identifier(table_name))
                )
                data = cur.fetchall()

                cols = [col[0] for col in cur.description]

            df_dict[table_name] = pd.DataFrame(data, columns=cols)
        return df_dict
    finally:
        conn.close()


def read_data_join(
        db_conf: typing.Mapping = db_conf,
        sql_conf: typing.Mapping = sql_conf,
        levels: list = ['instance_tags', 'series_tags', 'study_tags', 'patient_tags'],
        dt_interval: typing.Tuple[datetime, datetime] = None,
) -> pd.DataFrame:
    # connect to db
    conn = connect_to_db(db_conf=db_conf)
    tables_dict = sql_conf['join_keys']
    foreign_dict = {key: val for key, val in sql_conf['foreign_mapping'].items() if key in levels}
    joins = sql.SQL(' ').join(
        [sql.SQL("INNER JOIN {right_name} ON {left_name}.{left_key} = {right_name}.{left_key}").format(
            right_name=sql.Identifier(right),
            left_key=sql.Identifier(tables_dict[left]),
            left_name=sql.Identifier(left),
        )
            for right, left in foreign_dict.items()]
    )

    # time selection
    if dt_interval is not None:
        query = sql.SQL(
            """SELECT * FROM {left} {joins}
            WHERE {dt_lvl}.{dt_key} >= {lower_stamp} AND {dt_lvl}.{dt_key} < {upper_stamp}"""
        ).format(joins=joins,
                 left=sql.Identifier("patient_tags"),
                 lower_stamp=sql.Placeholder(),
                 upper_stamp=sql.Placeholder(),
                 dt_key=sql.Identifier("StudyDateTime"),
                 dt_lvl=sql.Identifier("study_tags")
                 )
        values = dt_interval
    else:
        query = sql.SQL("SELECT * FROM {left} {joins} ").format(
            joins=joins,
            left=sql.Identifier("patient_tags")
        )
        values = None

    try:
        with conn.cursor() as cur:
            cur.execute(query=query, vars=values)
            data = cur.fetchall()

            cols = [col[0] for col in cur.description]

            df = pd.DataFrame(data, columns=cols)
            df = df.loc[:, ~df.columns.duplicated()].copy()
            return df
    finally:
        conn.close()


def store_df_to_table(df: pd.DataFrame, if_exists='append', name: str = 'dashboard_table'):
    # connect to db
    url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}".format(**db_conf)
    conn = create_engine(url)

    # clean datetime from df
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if len(datetime_cols) > 0:
        df[datetime_cols] = df[datetime_cols].applymap(lambda x: x.isoformat()).astype(str)
    timedelta_cols = df.select_dtypes(include=['timedelta64']).columns.tolist()
    if len(timedelta_cols) > 0:
        df[timedelta_cols] = df[timedelta_cols].apply(lambda x: x.dt.total_minutes(), axis=1)
    str_cols = df.select_dtypes(include=[object]).columns.tolist()
    if len(str_cols) > 0:
        df[str_cols] = df[str_cols].apply(lambda x: x.str.replace(r"\[\]", ".", regex=True), axis=1)

    # store data to SQL
    df.to_sql(
        name=name,
        con=conn, schema=None,
        if_exists=if_exists,
        index=True,
        index_label=None,
        chunksize=None,
        dtype=None,
        method=None
    )