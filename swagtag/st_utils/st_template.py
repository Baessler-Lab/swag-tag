import json
import typing
from pathlib import Path

import streamlit as st


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


@st.cache_resource(ttl=10000)
def load_templates(
        template_dir,
) -> typing.Tuple[typing.List[dict], typing.List[str]]:
    template_fpaths = [f for f in Path(template_dir).glob("*.json")]
    template_options = [f.stem for f in template_fpaths]
    templates = []
    # try:
    #     template_options.remove("default_template"),
    # template_options.insert(0, "default_template")
    for fpath in template_fpaths:
        with fpath.open("r") as f:
            templates.append(json.load(f))

    return templates, template_options

    # if 'template_loaded' not in st.session_state:
    #     st.session_state.template_loaded = False
    #
    # if not st.session_state.template_loaded:
    #     template_name = st.selectbox("Template", options=template_options, key=widget_key)
    #     if st.button("Load template", use_container_width=True, key=f"{widget_key}_button"):
    #         st.session_state.template_loaded = True
    #
    #         return template
    # else:
    #     st.write("Template already loaded.")
    #     return None
