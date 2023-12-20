import streamlit as st


def st_report_box():
    with st.container() as report_spot:
        report = st.session_state['report']
        report: dict
        for name in st.session_state.dash_conf['report_columns']:
            with st.expander(
                    name.upper(),
                    expanded=True if report[name] is not None else False
            ):
                st.write(report[name])
