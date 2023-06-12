import datetime
import re
import typing
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from config.config import path_conf, sql_conf, db_conf
from sql.db_utils import insert_into_db, connect_to_db
from sql.init_db import create_or_check_db_and_tables


def parse_txt_reports(
        fpath_report: Path,
) -> typing.Dict:
    report_content = defaultdict(str)
    with fpath_report.open('r') as f:
        s = f.read()
        s: str
        matches = re.finditer(
            r'.*?(?P<keyword>[A-Z]+):(?P<item>.*?(?=[A-Z]+:|$))',
            s,
            flags=re.DOTALL
        )
        for match in matches:
            if match:
                report_content[match.group('keyword').lower()] = match.group('item')

    return report_content


def scrape_filetree_and_save_to_database():
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

            # DEBUG:
            if k >= 5:
                break

            patient_id = report_fpath.parent.parts[-1].__str__()
            study_instance_uid = report_fpath.stem
            report_uri = report_fpath.relative_to(path_conf.data_dir).__str__()
            # in our case the AccessionNumber is the same as the StudyInstanceUID
            accession_number = study_instance_uid

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
    scrape_filetree_and_save_to_database()
