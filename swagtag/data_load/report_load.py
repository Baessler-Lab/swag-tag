import pandas as pd
import streamlit as st
from psycopg2._psycopg import connection

from config.config import sql_conf
from sql.db_utils import read_table_to_df


def lookup_study_instance_uid_and_report(
        report_df: pd.DataFrame,
        accession_number: str,
) -> pd.Series:
    return report_df.loc[report_df['AccessionNumber'] == accession_number]


def load_report_for_study(
        accession_number: str,
        conn: connection,
) -> pd.Series:
    report_df = read_table_to_df(
        ids_to_load=[accession_number],
        cols_to_load=st.session_state['dash_conf']['report_columns'],  # None = all
        table_name=sql_conf['reports_table']['table_name'],
        prim_key=sql_conf['reports_table']['prim_key'],
        conn=conn,
    )
    report_series = report_df.squeeze()
    assert isinstance(report_series, pd.Series)
    return report_series
