import json
import typing
from functools import partial
from pathlib import Path

import streamlit as st

from annotation.io import save_annotation, get_last_user_annotation, lookup_label_from_annotation_meta
from st_utils.states_swag_tag import update_annotation


def handle_single_selection(node, report, unique_key, disabled):
    option_ids = [child["id"] for child in node["children"]]
    selected_ids = [id_ for id_ in option_ids if report.get(str(id_), {}).get('activated', False)]
    assert len(selected_ids) <= 1, "Maximally one child can be selected"
    if not selected_ids:
        selected_id = option_ids[0]
    else:
        selected_id = selected_ids[0]
    default_index = option_ids.index(selected_id)
    option_names = [child["name"] for child in node["children"]]
    selected_name = st.radio(
        node['name'],
        option_names,
        index=default_index,
        key=f"{unique_key}_annotation_radio_{st.session_state['cur_study_instance_uid']}",
        disabled=disabled)

    return selected_name


def handle_yes_no(node, report, unique_key, disabled):
    activated_by_report = report.get(str(node["id"]), {}).get('activated', False)
    activated = st.checkbox(
        node['name'],
        value=activated_by_report,
        key=f"{unique_key}_annotation_checkbox_{st.session_state['cur_study_instance_uid']}",
        disabled=disabled
    )

    return activated


def render_report(template_node, report=None, level=-1, state=None, disabled=False):
    node_id = str(template_node['id'])
    node = template_node.copy()

    if report is None:
        report = {}

    if state is None:
        state = {}

    if node.get('single-selectable', False):
        if state.get(node_id, {}).get("activated", False):
            activated = True
        else:
            activated = False
    else:
        cols = st.columns([1] * level + [4])

        with cols[-1]:
            if "single-select-from-children" in node and node["single-select-from-children"]:
                selected_name = handle_single_selection(node, report, node_id, disabled=disabled)
                single_select_activated = False
                if not disabled:
                    for child in node['children']:
                        child_id = str(child['id'])
                        if child['name'] == selected_name:
                            state[child_id] = {'name': child["name"], 'activated': True}
                            single_select_activated = True
                        else:
                            state[child_id] = {'name': child["name"], 'activated': False}


            elif 'activatable' in node and node['activatable']:
                activated = handle_yes_no(node, report, node_id, disabled=disabled)
                if not disabled:
                    state[node_id] = {'name': node["name"], 'activated': activated}

            else:
                st.markdown(node['name'])

    children = node.get('children', [])

    if not node.get("activatable"):
        child_disabled = disabled or False
    else:
        try:
            child_disabled = disabled or not activated or not single_select_activated
        except UnboundLocalError:
            child_disabled = disabled or False
    for child in children:
        render_report(child, report, level=level + 1, state=state, disabled=child_disabled)

    return state

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


def st_annotation_select():
    cur_anns_meta = st.session_state.current_annotations_meta

    if len(cur_anns_meta) > 0:
        # get last annotation for current user
        last_annotation, last_annotation_meta = get_last_user_annotation(
            annotations_meta=st.session_state.current_annotations_meta,
            annotations=st.session_state.current_annotations,
            user=st.session_state.dash_conf.get("llm_user", "llama-2-70b-8bit"),
            dash_conf=st.session_state.dash_conf,
        )
        annotation_options = list(st.session_state.current_annotations.keys()) + [None, ]

        use_llm = st.checkbox(
            "use LLM for default",
            value=True
        )


        if len(last_annotation_meta) > 0:
            last_annotation_index = list(st.session_state.current_annotations.keys()). \
                index(last_annotation_meta['annotation_id'])
        else:
            if use_llm:
                try:
                    last_annotation, last_annotation_meta = get_last_user_annotation(
                        annotations_meta=st.session_state.current_annotations_meta,
                        annotations=st.session_state.current_annotations,
                        user=st.session_state.dash_conf.get("llm_user", "llama-2-70b-8bit"),
                        dash_conf=st.session_state.dash_conf,
                    )
                    assert len(last_annotation_meta) > 0, "No llm generated annotation available for this report."
                    last_annotation_index = list(st.session_state.current_annotations.keys()). \
                        index(last_annotation_meta['annotation_id'])

                except AssertionError:
                    last_annotation_index = annotation_options.__len__() - 1


            else:
                last_annotation_index = annotation_options.__len__() - 1

        ann_id = st.selectbox(
            label='Stored annotations',
            options=list(st.session_state.current_annotations.keys()) + [None, ],
            format_func=partial(lookup_label_from_annotation_meta, annotations_meta=cur_anns_meta),
            index=last_annotation_index,
            key=f'selected_annotation_id',
        )


        update_annotation(annotation_id=ann_id)


# noinspection DuplicatedCode
def st_annotation_box():
    st.markdown('## Annotation ##')

    # select annotations
    st_annotation_select()

    current_report = render_report(
        template_node=st.session_state["template"],
        report=st.session_state["current_annotation"]
    )
    st.session_state['current_report'] = current_report

    st.button(
        label="Submit annotation",
        on_click=store_annotation_callback,
    )


def load_annotation_callback():
    ...


def store_annotation_callback():
    save_annotation(
        study_instance_uid=st.session_state['cur_study_instance_uid'],
        accession_number=st.session_state['cur_accession_number'],
        annotation=st.session_state['current_report'],
        author=st.session_state.current_user,
        conn=st.session_state['db_conn']
    )
    st.success('Successfully stored your annotation.')
