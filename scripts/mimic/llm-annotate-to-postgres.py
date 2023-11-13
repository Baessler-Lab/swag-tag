import datetime
import re
import typing
from collections import defaultdict
from pathlib import Path
import logging

import requests
from tqdm import tqdm

import config.config
from annotation.io import save_annotation
from config.config import path_conf, sql_conf, db_conf
from sql.db_utils import insert_into_db, connect_to_db, check_if_in_table
from sql.init_db import create_or_check_db_and_tables

log = logging.getLogger(__name__)


def validate_template(template_json):
    id_set = set()

    def check_unique_ids(node, id_set):
        if 'id' in node:
            assert node['id'] not in id_set, f"Duplicate ID found: {node['id']}"
            id_set.add(node['id'])
        if 'children' in node:
            for child in node['children']:
                check_unique_ids(child, id_set)

    check_unique_ids(template_json, id_set)


binary_activation_map = {
    "yes": True,
    "no": False,
}


def postprocess_llm_to_flat(node: dict, activation_dict, flat_report=None, activated_by_parent=False):
    if flat_report is None:
        flat_report = {}

    activation_id = f"answer_{node['id']}"

    # First part - get activation status of the node
    activated = False  # default value
    if "activatable" in node and node["activatable"]:

        if "single-selectable" in node and node["single-selectable"]:
            activated = activated_by_parent
        else:
            try:
                activated = binary_activation_map[activation_dict[activation_id]]
            except KeyError:
                raise ValueError(f"Unknown value in activation dict: {activation_dict[activation_id]}")

        # Update the flat report
        flat_report[str(node['id'])] = {'name': node['name'], 'activated': activated}

    # Second part - parse children
    if "single-select-from-children" in node and node["single-select-from-children"]:
        activated_child_name = activation_dict.get(activation_id)
        for child in node["children"]:
            child_activated = (child["name"] == activated_child_name)
            postprocess_llm_to_flat(child, activation_dict, flat_report=flat_report,
                                    activated_by_parent=child_activated)

    elif (not node.get('activatable', False)) or activated:
        if 'children' in node:
            for child in node["children"]:
                postprocess_llm_to_flat(child, activation_dict, flat_report=flat_report, activated_by_parent=False)

    return flat_report


def structurize_report(report: str, template: typing.Mapping, endpoint: str):
    response = requests.post(f"http://{endpoint}/predict", json={"report": report, "template": template})
    if not response.ok:
        log.error(response.text)
    result = response.json()

    return result


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


def structurize_report_llm(report_content: typing.Mapping[str, str]):
    # join report_content
    findings = report_content.get('findings', "").replace(r'\n', '')
    impression = report_content.get("impression", "").replace(r"\n", '')

    findings_impression = f"""
    FINDINGS: \n
    {findings} \n
    IMPRESSION: \n
    {impression} \n
    """

    result = structurize_report(
        report=findings_impression,
        template=config.config.DEFAULT_TEMPLATE,
        endpoint=config.config.ENDPOINT
    )
    llm_annotation = postprocess_llm_to_flat(
        node=config.config.DEFAULT_TEMPLATE,
        activation_dict=result.get('activation_dict', {}),
        activated_by_parent=False,
                            )
    # llm_annotation = result.get('result', {})
    return llm_annotation


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
                save_annotation(
                    annotation=structurize_report_llm(report_content),
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
