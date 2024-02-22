import datetime
import typing
from collections import defaultdict
import logging

from tqdm import tqdm

import config.config
from annotation.io import save_annotation
from config.config import path_conf, sql_conf, db_conf
from sql.db_utils import insert_into_db, connect_to_db, check_if_in_table
from sql.init_db import create_or_check_db_and_tables
from st_utils.st_annotation import parse_txt_reports, structurize_separate_findings_and_impression

log = logging.getLogger(__name__)


def scrape_filetree_and_save_to_database(use_llm: bool = False):
    create_or_check_db_and_tables(
        replace_db=False, replace_tables=False,
        db_config=db_conf,
        sql_config=sql_conf)
    conn = connect_to_db(db_config=db_conf)
    try:
        reports_uri_vals_to_insert = []
        image_uri_vals_to_insert = []

        for k, report_fpath in tqdm(enumerate(path_conf.data_dir.rglob('*.txt'))):
            """
            fpath have style: PatientID/StudyInstanceUID.txt
            imagepaths have style PatientID/StudyInstanceUID/SeriesInstanceUID.jpeg
            """

            # # DEBUG:
            # if k >= 5:
            #     break

            patient_id = report_fpath.parent.parts[-1].__str__()
            study_instance_uid = report_fpath.stem
            report_uri = report_fpath.relative_to(path_conf.data_dir).__str__()
            # in our case the AccessionNumber is the same as the StudyInstanceUID
            accession_number = study_instance_uid

            # check if there is already an annotation
            in_table = check_if_in_table(
                table_name=sql_conf['result_table'].get("table_name"),
                prim_key='StudyInstanceUID',
                ids_to_check=[study_instance_uid],
                any=True
            )

            for image_fpath in (report_fpath.parent / study_instance_uid).glob('*.jpg'):
                image_uri = image_fpath.relative_to(path_conf.data_dir).__str__()
                series_instance_uid = image_fpath.stem
                image_uri_mapping = defaultdict(lambda: None)
                image_uri_mapping.update(
                    {
                        'PatientID': patient_id,
                        'StudyInstanceUID': study_instance_uid,
                        'SeriesInstanceUID': series_instance_uid,
                        'image_uri': image_uri,
                        'AccessionNumber': accession_number,
                        'creation_time': datetime.datetime.utcnow()
                    }
                )
                image_uri_vals_to_insert.append(image_uri_mapping)

            report_uri_mapping = defaultdict(lambda: None)
            report_uri_mapping.update(
                {
                    'PatientID': patient_id,
                    'StudyInstanceUID': study_instance_uid,
                    'report_uri': report_uri,
                    'AccessionNumber': accession_number,
                    'creation_time': datetime.datetime.utcnow()
                }
            )
            report_content = parse_txt_reports(fpath_report=report_fpath)
            report_uri_mapping.update(report_content)

            reports_uri_vals_to_insert.append(report_uri_mapping)
            reports_uri_vals_to_insert: typing.MutableSequence[typing.Mapping[str, ...]]

            if k % 1 == 0:
                # bulk insert into DB
                insert_into_db(
                    dicom_dicts=reports_uri_vals_to_insert,
                    conn=conn,
                    table_conf=sql_conf['study_table'],
                    upsert=True,
                )
                insert_into_db(
                    dicom_dicts=reports_uri_vals_to_insert,
                    conn=conn,
                    table_conf=sql_conf['reports_table'],
                    upsert=True,
                )
                insert_into_db(
                    dicom_dicts=image_uri_vals_to_insert,
                    conn=conn,
                    table_conf=sql_conf['image_uris_table'],
                    upsert=True,
                )

                conn.commit()
            if use_llm and not in_table:
                structured_report, json_report = structurize_separate_findings_and_impression(report_content)
                save_annotation(
                    annotation=structured_report,
                    study_instance_uid=study_instance_uid,
                    accession_number=accession_number,
                    conn=conn,
                    author=config.config.DEFAULT_LLM,
                )

        # bulk insert into DB
        insert_into_db(
            dicom_dicts=reports_uri_vals_to_insert,
            conn=conn,
            table_conf=sql_conf['study_table'],
            upsert=True,
        )
        insert_into_db(
            dicom_dicts=reports_uri_vals_to_insert,
            conn=conn,
            table_conf=sql_conf['reports_table'],
            upsert=True,
        )
        insert_into_db(
            dicom_dicts=image_uri_vals_to_insert,
            conn=conn,
            table_conf=sql_conf['image_uris_table'],
            upsert=True,
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == '__main__':
    scrape_filetree_and_save_to_database(use_llm=True)
