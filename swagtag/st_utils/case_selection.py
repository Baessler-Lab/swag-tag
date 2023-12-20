import streamlit as st

from config.load_config import store_configuration
match st.session_state['page']:
    case 'llm':
        from .states_llm import update_case, update_all
    case 'swag-tag':
        from .states_swag_tag import update_case, update_all
    case _:
        raise ValueError("'page' needs to be defined in st.session_state")

def change_case_prev():
    cur_case_no = st.session_state['case_no']
    if cur_case_no >= 1:
        select_case(case_no=cur_case_no - 1)
    else:
        pass


def change_case_next():
    cur_case_no = st.session_state['case_no']
    if cur_case_no < st.session_state['map_study_instance_uid_accession_number'].shape[0]:
        select_case(case_no=cur_case_no + 1)
    else:
        pass


def change_case_submit():
    new_case_no = st.session_state['case_number_form']
    if st.session_state['map_study_instance_uid_accession_number'].shape[0] > new_case_no >= 0:
        select_case(new_case_no)
    else:
        st.warning(f'There is no case with no {new_case_no}.')


def store_conf_submit(**kwargs):
    store_configuration(**kwargs)
    st.success(f"Successfully stored the current configuration as {kwargs['config_id']}.")


def select_case(case_no):
    update_case(case_no=case_no)
    update_all()
