import json
import toml

import streamlit as st
import yaml

if not 'page' in st.session_state:
    st.session_state['page'] = 'swag-tag'

from config.load_config import load_dash_conf
from st_utils.sidebar import settings, image_sidebar
from st_utils.st_annotation import st_annotation_box, render_report_nested_dict
from st_utils.st_image import st_image_box
from st_utils.st_report import st_report_box
from st_utils.st_annotation import structurize_report_llm
from st_utils.states_swag_tag import init_session_states


def app():
    st.set_page_config(
        page_title=load_dash_conf(default=True)['page_title'],
        layout="wide",
    )
    init_session_states(page="structurize")
    st.title(st.session_state.dash_conf['title'])
    # reset annotation
    st.session_state["current_annotation"] = {}
    # Divide page into tabs
    tab_main, tab_report, tab_settings = st.tabs(
        [
            "Images",
            "Report",
            "Settings"
        ]
    )
    with tab_main:
        with st.sidebar:
            image_sidebar()
        c1, c2 = st.columns([st.session_state["frac_img"], 100 - st.session_state["frac_img"]])
        with c1:
            tabs = st.tabs([
                f"Image {im_no}" for im_no in
                range(st.session_state['images'].__len__())
            ])
            fig_spots = st_image_box(tabs)
        if st.session_state["dash_conf"].get("use_separate_boxes", False):
            findings = st.sidebar.text_area(
                "Findings",
                value='',
                help="Type your findings here!. We recommend to give all the information needed to fill your structured template.",
                height=400,
                max_chars=None,
                key=None
            )
            impression = st.sidebar.text_area(
                "Impression",
                value='',
                help="Type your impression here!. We recommend to give all the information needed to fill your structured template.",
                height=400,
                max_chars=None,
                key=None
            )
            report = f"""
                FINDINGS: \n
                {findings} \n
                IMPRESSION: \n
                {impression} \n
                """
        else:
            report = st.sidebar.text_area(
                "Report",
                value='',
                help="Type your report here!. We recommend to give all the information needed to fill your structured template.",
                height=400,
                max_chars=None,
                key=None
            )

    if 'template' not in st.session_state:
        st.stop()
    with tab_report:

        infer_button = st.sidebar.button("Structurize the report", use_container_width=True, type="primary")

        if infer_button:
            with st.spinner("The large Llama is currently chewing and thinking..."):
                structured_report = structurize_report_llm(
                    report=report,
                    template=st.session_state.template,
                )
                nested_dict_report = render_report_nested_dict(
                    template_node=st.session_state.template,
                    report=structured_report,
                    level=-1,
                    disabled=False,
                    hide_inactivated_downstream_nodes=True,
                )
                st.session_state["current_annotation"] = structured_report
                st.session_state["activation_dict"] = nested_dict_report

        tab2, tab1 = st.tabs(
            tabs=["Structured Report", "Template"],
        )

        with tab1:
            markup_lang_templ = st.selectbox(
                label="Choose a markup language",
                options=['yaml', 'toml', 'json'],
                index=0,
                key="markup_lang_templ",
            )
            match markup_lang_templ:
                case 'yaml':
                    yaml_template = yaml.dump(
                        st.session_state.template,
                        sort_keys=False,
                        default_flow_style=False
                    )
                    st.code(
                        yaml_template,
                        language="yaml"
                    )
                    st.download_button(
                        label="Download template",
                        data=yaml_template,
                        file_name="template.yaml",
                        mime="application/yaml",
                    )
                case 'json':
                    json_report = json.dumps(
                        st.session_state.template,
                        indent=4
                    )
                    st.code(
                        json_report,
                        language="json"
                    )
                    st.download_button(
                        label="Download structured report as json",
                        data=json_report,
                        file_name="structured_report.json",
                        mime="application/json",
                    )
                case 'toml':
                    toml_report = toml.dumps(
                        st.session_state.template,
                    )
                    st.code(
                        toml_report,
                        language="json"
                    )
                    st.download_button(
                        label="Download structured report as toml",
                        data=toml_report,
                        file_name="structured_report.toml",
                        mime="application/toml",
                    )
        with tab2:
            dict_report = render_report_nested_dict(
                template_node=st.session_state.template,
                report=st.session_state["current_annotation"],
                level=-1,
                disabled=False,
                hide_inactivated_downstream_nodes=True,
            )
            markup_lang = st.selectbox(
                label="Choose a markup language",
                options=['yaml', 'toml', 'json'],
                index=0,
                key="markup_lang"
            )
            st.markdown("## current annotation")
            st.code(
                st.session_state["current_annotation"],
            )
            st.markdown("## current activation dict")
            st.code(
                st.session_state.get("activation_dict", {}),
            )
            match markup_lang:
                case 'yaml':

                    yaml_report = yaml.dump(
                        dict_report,
                        sort_keys=False,
                        default_flow_style=False
                    )
                    st.code(
                        yaml_report,
                        language="yaml"
                    )
                    st.download_button(
                        label="Download structured report as yaml",
                        data=yaml_template,
                        file_name="template.yaml",
                        mime="application/yaml",
                    )
                case 'json':
                    json_report = json.dumps(
                        dict_report,
                        indent=4
                    )
                    st.code(
                        json_report,
                        language="json"
                    )
                    st.download_button(
                        label="Download structured report as json",
                        data=json_report,
                        file_name="structured_report.json",
                        mime="application/json",
                    )
                case 'toml':
                    toml_report = toml.dumps(
                        dict_report,
                    )
                    st.code(
                        toml_report,
                        language="json"
                    )
                    st.download_button(
                        label="Download structured report as toml",
                        data=toml_report,
                        file_name="structured_report.toml",
                        mime="application/toml",
                    )

        st_annotation_box()
    with tab_settings:
        settings()


if __name__ == '__main__':
    app()
