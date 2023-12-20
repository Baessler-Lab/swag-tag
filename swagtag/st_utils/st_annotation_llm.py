import json
import typing
from collections import defaultdict
from functools import partial
from itertools import chain

import streamlit as st

from annotation.io import save_annotation, get_last_user_annotation, lookup_label_from_annotation_meta
from st_utils.states_llm import update_annotation


def st_annotation_select():
    cur_anns_meta = st.session_state.current_annotations_meta

    if len(cur_anns_meta) > 0:
        # get last annotation for current user
        last_annotation, last_annotation_meta = get_last_user_annotation(
            annotations_meta=st.session_state.current_annotations_meta,
            annotations=st.session_state.current_annotations,
            user=st.session_state['current_user'],
            dash_conf=st.session_state.dash_conf,
        )
        annotation_options = list(st.session_state.current_annotations.keys()) + [None, ]
        if len(last_annotation_meta) > 0:
            last_annotation_index = list(st.session_state.current_annotations.keys()). \
                index(last_annotation_meta['annotation_id'])
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


# def recurse_template_and_annotation_tree(
#         node: typing.Mapping,
#         annotation_node: typing.Mapping,
# ):
#     if


def recurse_template(
        node: typing.Mapping,
        annotation_node: typing.Mapping,
        upstream_activated: bool = True,
        an_form: st.form = None,
        headline_level: int = 2,
        column_step: int = 2,
        columns_step_size: float = 0.02,

):
    # generate form if missing
    if an_form is None:
        an_form = st.form('annotation_form', clear_on_submit=True)

    try:
        single_select_from_children = node['single-select-from-children']
    except KeyError:
        single_select_from_children = False
    try:
        activatable = node['activatable']
    except KeyError:
        activatable = False

    # if activatable:
    #     downstream_activated = annotation_node['activated']
    # else:
    #     # pass upstream activation if node is not activatable
    #     downstream_activated = upstream_activated



    # return sub tree
    ret_node = {
        'id': node['id'],
        'name': node['name'],
        'activatable': activatable,
    }
    ret_ann_node = {
        'id': node['id'],
        'name': node['name'],
    }

    if 'children' in node and 'children' in annotation_node:  # not a bottom node

        # activatable children
        children = [child for child in node['children'] if child.get('activatable', False)]
        ann_children = [child[1] for child in zip(node['children'], annotation_node['children']) if
                        child[0].get('activatable', False)]

        non_activatable_children = [child[0] for child in zip(node['children'], annotation_node['children']) if
                                    not child[0].get('activatable', False)]
        non_activatable_ann_children = [child[1] for child in zip(node['children'], annotation_node['children']) if
                                        not child[0].get('activatable', False)]
        # print(f'all childs activatable: {bool_children_activatable}')
        # st.write({key: val for key, val in node.items() if key != 'children'})
        # if upstream_activated:
        # bool_children_activatable = [child[0].get('activatable', False) for child in returned_children]
        if f"node_{node['id']}_enabled" not in st.session_state:
            st.session_state[f"node_{node['id']}_enabled"] = upstream_activated

        if f"node_{node['id']}_enabled" not in st.session_state:
            st.session_state[f"node_{node['id']}_enabled"] = upstream_activated
        # indent results
        # with an_form:
        first_width = column_step * columns_step_size + 1e-4
        second_width = 1 - first_width
        c1, c2 = st.columns((first_width, second_width))
        if st.session_state[f"node_{node['id']}_enabled"]:
            with c2:
                if st.session_state[f"node_{node['id']}_enabled"]:
                    st.markdown(f"{'#' * headline_level} {node['name']}")
                placeholder = st.empty()

            # st.write(bool_children_activatable)
        # assert children > 0 and ann_children > 0
        # st.write(children)
        # st.write(non_activatable_children)
        if len(children) > 0:
            # import json
            # pretty = json.dumps(st.session_state.current_annotation, indent=4)
            # print(pretty)
            # TODO: a future streamlit release will support None as default index currently we need to hack this...
            # an option would be to add a default tag and make it invisible using CSS or 'Select!'.
            import json
            # print(json.dumps(ann_children, indent=4))
            activated_children = [
                ann_child for child, ann_child in zip(children, ann_children)
                # may be rendundand
                if ann_child.get('activated', False) and child[0].get('activatable', False)
            ]
            if st.session_state[f"node_{node['id']}_enabled"]:
                if single_select_from_children:
                    assert len(activated_children) <= 1
                    # get_activated_child_index
                    try:
                        activated_child_id = activated_children[0]['id']
                    except IndexError:
                        activated_child_id = None
                    def_node = {'id': 'default', 'name': 'Select!', }
                    children_ids = [def_node['id'], ] + [child['id'] for child in children]
                    default_index = children_ids.index(activated_child_id) if activated_child_id is not None else 0

                    with placeholder:
                        activated_child_id = st.radio(
                            label=node['name'],
                            options=children_ids,
                            format_func=lambda child_id: children[children_ids.index(child_id) - 1]['name']
                            if child_id != 'default' else def_node['name'],
                            horizontal=True,
                            index=default_index,
                            label_visibility='collapsed',
                            # on_change=update_downstream_nodes(),
                            # kwargs=dict(ann_children=ann_children),
                            # disabled=not st.session_state[f"node_{node['id']}_enabled"],
                            key=f"single_select_{node['id']}_{st.session_state['cur_study_instance_uid']}"
                        )
                        activated_children_ids = [
                            st.session_state[
                                f"single_select_{node['id']}_{st.session_state['cur_study_instance_uid']}"
                            ]
                        ]

                        # # activate children
                        # for child, ann_child in zip(children, ann_children):
                        #     assert child['activatable']
                        #
                        #     if ann_child['id'] == activated_child_id and st.session_state[f"node_{node['id']}_enabled"]:
                        #         ann_child['activated'] = True
                        #         st.session_state[f"node_{ann_child['id']}_activated"] = True
                        #     else:
                        #         ann_child['activated'] = False
                        #         st.session_state[f"node_{ann_child['id']}_activated"] = False

                else:
                    with placeholder:
                        children_ids = [child['id'] for child in children]
                        activated_child_nodes = st.multiselect(
                            label=node['name'],
                            options=children,
                            default=activated_children,
                            format_func=lambda child: child['name'],
                            key=f"multiselect_{node['id']}_{st.session_state['cur_study_instance_uid']}",
                            label_visibility='collapsed',
                            # disabled=st.session_state[f"node_{node['id']}_enabled"],
                            # on_change=st.experimental_rerun(),
                            # id needed for clearing widget on case switch
                        )

                    activated_children_ids = [
                        child['id']
                        for child in
                        st.session_state[f"multiselect_{node['id']}_{st.session_state['cur_study_instance_uid']}"]
                    ]
            else:
                activated_children_ids = []

        # with placeholder:
        #     st.write(ann_children)
        returned_children = [
            recurse_template(
                sub_node,
                sub_ann_node,
                upstream_activated=sub_ann_node.get('activated', upstream_activated),
                headline_level=headline_level + 1,
                column_step=column_step + 1,
                columns_step_size=columns_step_size,
                an_form=an_form
            ) for sub_node, sub_ann_node in zip(
                chain(children, non_activatable_children),
                chain(ann_children, non_activatable_ann_children)
            )
        ]
        returned_node_children = [child[0] for child in returned_children]
        returned_annotated_children = [child[1] for child in returned_children]

        assert 'children' in annotation_node
        ret_node['children'] = returned_node_children + non_activatable_children
        ret_ann_node['children'] = returned_annotated_children + non_activatable_ann_children

    if activatable:
        # assert f"node_{node['id']}_activated" in st.session_state
        ret_ann_node['activated'] = st.session_state[f"node_{node['id']}_activated"]

    # # experimental:
    # annotation_node = ret_ann_node
    # node = ret_node

    return ret_node, ret_ann_node


# def update_downstream_nodes(upstream_node_key: str, upstream_node_enabled, ann_children: typing.Dict[str, typing.Any]):
#     activated_children_ids = st.session_state
#     # activate children
#     for ann_child in ann_children:
#         # assert child['activatable']
#         if ann_child['id'] in activated_children_ids and st.session_state[f"node_{node['id']}_enabled"]:
#             ann_child['activated'] = True
#             st.session_state[f"node_{ann_child['id']}_activated"] = True
#         else:
#             ann_child['activated'] = False
#             st.session_state[f"node_{ann_child['id']}_activated"] = False

# noinspection DuplicatedCode
def st_annotation_box():
    st.markdown('## Annotation ##')

    # select annotations
    st_annotation_select()

    # st.multiselect(
    #     label='Tags',
    #     options=st.session_state.dash_conf['annotation_tags'],
    #     default=st.session_state.current_annotation['tags'],
    #     key=f"tags_{st.session_state['cur_study_instance_uid']}",  # id needed for clearing widget on case switch
    # )
    an_form = st.form('annotation_form', clear_on_submit=True)
    ret_node, ret_ann = recurse_template(
        st.session_state['template'],
        st.session_state.current_annotation,
        upstream_activated=True,
        an_form=an_form, headline_level=2)
    # st.write(st.session_state)
    st.json(json.dumps(ret_ann, indent=4))
    #
    # for tag in st.session_state.dash_conf['annotation_tags']:
    #     visible = tag in st.session_state[f"tags_{st.session_state['cur_study_instance_uid']}"]
    #
    #     if visible:
    #         with an_form:
    #             visibility = 'visible'
    #             st.markdown(f'### {tag}')
    #             st.radio(
    #                 label='Probability',
    #                 index=st.session_state.current_annotation[tag]['probability'],
    #                 options=list(st.session_state.dash_conf['annotation_probability']),
    #                 format_func=lambda x: st.session_state.dash_conf['annotation_probability'][x],
    #                 label_visibility=visibility,
    #                 key=f'annotation_proba_{tag}',
    #                 horizontal=True,
    #             )
    #
    #             st.radio(
    #                 label='Severity',
    #                 index=st.session_state.current_annotation[tag]['severity'],
    #                 options=list(st.session_state.dash_conf['annotation_severity']),
    #                 format_func=lambda x: st.session_state.dash_conf['annotation_severity'][x],
    #                 label_visibility=visibility,
    #                 key=f'annotation_severity_{tag}',
    #                 horizontal=True,
    #             )
    #             st.radio(
    #                 label='Urgency',
    #                 index=st.session_state.current_annotation[tag]['urgency'],
    #                 options=list(st.session_state.dash_conf['annotation_urgency']),
    #                 format_func=lambda x: st.session_state.dash_conf['annotation_urgency'][x],
    #                 label_visibility=visibility,
    #                 key=f'annotation_urgency_{tag}',
    #                 horizontal=True,
    #             )
    #             radio_side_placeholder = st.empty()
    #
    #         with radio_side_placeholder:
    #             side = st.radio(
    #                 label='Annotation side',
    #                 index=st.session_state.current_annotation[tag]['side'],
    #                 options=list(st.session_state.dash_conf['annotation_side']),
    #                 format_func=lambda x: st.session_state.dash_conf['annotation_side'][x],
    #                 label_visibility=visibility,
    #                 key=f'annotation_side_{tag}',
    #                 horizontal=True,
    #             )
    #
    #         with an_form:
    #             # st.write(f"side_{tag} %s" % st.session_state[f'annotation_side_{tag}'])
    #             match int(st.session_state[f'annotation_side_{tag}']):
    #                 case 0:
    #                     pass
    #                 case 1:  # left
    #                     st.markdown("#### Left")
    #                     st.multiselect(
    #                         label='Vertical location',
    #                         default=st.session_state.current_annotation[tag]['left_height'],
    #                         options=list(st.session_state.dash_conf['annotation_height'].keys()),
    #                         format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
    #                         label_visibility=visibility,
    #                         key=f'annotation_height_left_{tag}',
    #                     )
    #                 case 2:  # Right
    #                     st.markdown("#### Right")
    #                     st.multiselect(
    #                         label='Vertical location',
    #                         default=st.session_state.current_annotation[tag]['right_height'],
    #                         options=list(st.session_state.dash_conf['annotation_height'].keys()),
    #                         format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
    #                         label_visibility=visibility,
    #                         key=f'annotation_height_right_{tag}',
    #                     )
    #                 case 3:  # both
    #                     st.markdown("#### Right")
    #                     print(list(st.session_state.dash_conf['annotation_height'].keys()))
    #                     print(st.session_state.current_annotation[tag]['right_height'])
    #                     st.multiselect(
    #                         label='Vertical location',
    #                         default=st.session_state.current_annotation[tag]['right_height'],
    #                         options=list(st.session_state.dash_conf['annotation_height'].keys()),
    #                         format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
    #                         label_visibility=visibility,
    #                         key=f'annotation_height_right_{tag}',
    #                     )
    #                     st.markdown("#### Left")
    #                     st.multiselect(
    #                         label='Vertical location',
    #                         default=st.session_state.current_annotation[tag]['left_height'],
    #                         options=list(st.session_state.dash_conf['annotation_height'].keys()),
    #                         format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
    #                         label_visibility=visibility,
    #                         key=f'annotation_height_left_{tag}',
    #                     )
    #                 case _:
    #                     pass
    #     else:
    #         pass
    with an_form:
        st.form_submit_button('save_annotation',
                              type='primary',
                              on_click=store_annotation_callback,
                              )


def load_annotation_callback():
    ...


def recursive_store_annotation(
        node: typing.Mapping[str, typing.Any],
        activate_child: bool = False
) -> typing.Dict[str, typing.Any]:
    ret_node = {'name': node['name'], 'id': node['id']}
    if "single-select-from-children" in node:
        ret_node["single-select-from-children"] = node["single-select-from-children"]
    if 'activatable' in node:
        if node['activatable']:
            ret_node['activated'] = activate_child
        else:
            pass
    if "single-selectable" in node:
        ret_node["single-selectable"] = True

    if f"annotation_{node['id']}_{st.session_state['cur_study_instance_uid']}" in st.session_state:
        try:
            assert 'children' in node
        except AssertionError as ae:
            raise RuntimeError('There are no children to this node but %s is in session_state.',
                               f"annotation_{node['id']}_{st.session_state['cur_study_instance_uid']}") from ae
        for child in node['children']:
            print(node['children'])
            activate_subchild = str(child['id']) in st.session_state[
                f"annotation_{node['id']}_{st.session_state['cur_study_instance_uid']}"]
            recursive_store_annotation(child, activate_child=activate_subchild)

    return ret_node


def store_annotation_callback():
    annotation_dict = recursive_store_annotation(st.session_state.template, activate_child=False)
    # for tag in st.session_state.dash_conf['annotation_tags']:
    #     annotation_meta = defaultdict(lambda: 0)
    #     if tag in st.session_state[f"tags_{st.session_state['cur_study_instance_uid']}"]:
    #         annotation_meta.update({
    #             'probability': int(st.session_state[f'annotation_proba_{tag}']),
    #             'severity': int(st.session_state[f'annotation_severity_{tag}']),
    #             'urgency': int(st.session_state[f'annotation_urgency_{tag}']),
    #             'side': int(st.session_state[f'annotation_side_{tag}']),
    #         })
    #         match annotation_meta['side']:
    #             case 0:
    #                 annotation_meta['left_height'] = st.session_state.dash_conf['default_annotation_height']
    #                 annotation_meta['right_height'] = st.session_state.dash_conf['default_annotation_height']
    #             case 1:  # left
    #                 annotation_meta['left_height'] = st.session_state[f'annotation_height_left_{tag}']
    #                 annotation_meta['right_height'] = st.session_state.dash_conf['default_annotation_height']
    #             case 2:  # right
    #                 annotation_meta['left_height'] = st.session_state.dash_conf['default_annotation_height']
    #                 annotation_meta['right_height'] = st.session_state[f'annotation_height_right_{tag}']
    #             case 3:  # both
    #                 annotation_meta['left_height'] = st.session_state[f'annotation_height_left_{tag}']
    #                 annotation_meta['right_height'] = st.session_state[f'annotation_height_right_{tag}']
    #             case _:
    #                 raise ValueError('We consider only annotation_side 0-3 = irrelevant, left, right, both')
    #     else:
    #         annotation_meta.update({
    #             'probability': int(st.session_state.dash_conf['default_annotation_probability']),
    #             'severity': int(st.session_state.dash_conf['default_annotation_severity']),
    #             'urgency': int(st.session_state.dash_conf['default_annotation_urgency']),
    #             'side': int(st.session_state.dash_conf['default_annotation_side']),
    #             'left_height': st.session_state.dash_conf['default_annotation_height'],
    #             'right_height': st.session_state.dash_conf['default_annotation_height'],
    #         })
    #     annotation_dict[tag] = annotation_meta
    # print(annotation_dict)

    save_annotation(
        study_instance_uid=st.session_state['cur_study_instance_uid'],
        accession_number=st.session_state['cur_accession_number'],
        annotation=annotation_dict,
        author=st.session_state.current_user,
        conn=st.session_state['db_conn']
    )
    st.success('Successfully stored your annotation.')
