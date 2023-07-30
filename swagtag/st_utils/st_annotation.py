from collections import defaultdict

import streamlit as st

from annotation.io import save_annotation


def st_annotation_box():
    st.markdown('## Annotation ##')

    st.multiselect(
        label='Tags',
        options=st.session_state.dash_conf['annotation_tags'],
        default=st.session_state.current_annotation['tags'],
        key=f"tags_{st.session_state['cur_study_instance_uid']}",  # id needed for clearing widget on case switch
    )
    an_form = st.form('annotation_form', clear_on_submit=True)
    for tag in st.session_state.dash_conf['annotation_tags']:
        visible = tag in st.session_state[f"tags_{st.session_state['cur_study_instance_uid']}"]

        if visible:
            with an_form:
                visibility = 'visible'
                st.markdown(f'### {tag}')
                st.radio(
                    label='Probability',
                    index=st.session_state.current_annotation[tag]['probability'],
                    options=list(st.session_state.dash_conf['annotation_probability']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_probability'][x],
                    label_visibility=visibility,
                    key=f'annotation_proba_{tag}',
                    horizontal=True,
                )

                st.radio(
                    label='Severity',
                    index=st.session_state.current_annotation[tag]['severity'],
                    options=list(st.session_state.dash_conf['annotation_severity']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_severity'][x],
                    label_visibility=visibility,
                    key=f'annotation_severity_{tag}',
                    horizontal=True,
                )
                st.radio(
                    label='Urgency',
                    index=st.session_state.current_annotation[tag]['urgency'],
                    options=list(st.session_state.dash_conf['annotation_urgency']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_urgency'][x],
                    label_visibility=visibility,
                    key=f'annotation_urgency_{tag}',
                    horizontal=True,
                )
                radio_side_placeholder = st.empty()

            with radio_side_placeholder:
                side = st.radio(
                    label='Annotation side',
                    index=st.session_state.current_annotation[tag]['side'],
                    options=list(st.session_state.dash_conf['annotation_side']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_side'][x],
                    label_visibility=visibility,
                    key=f'annotation_side_{tag}',
                    horizontal=True,
                )

            with an_form:
                # st.write(f"side_{tag} %s" % st.session_state[f'annotation_side_{tag}'])
                match int(st.session_state[f'annotation_side_{tag}']):
                    case 0:
                        pass
                    case 1:  # left
                        st.markdown("#### Left")
                        st.multiselect(
                            label='Vertical location',
                            default=st.session_state.current_annotation[tag]['left_height'],
                            options=list(st.session_state.dash_conf['annotation_height'].keys()),
                            format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
                            label_visibility=visibility,
                            key=f'annotation_height_left_{tag}',
                        )
                    case 2:  # Right
                        st.markdown("#### Right")
                        st.multiselect(
                            label='Vertical location',
                            default=st.session_state.current_annotation[tag]['right_height'],
                            options=list(st.session_state.dash_conf['annotation_height'].keys()),
                            format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
                            label_visibility=visibility,
                            key=f'annotation_height_right_{tag}',
                        )
                    case 3:  # both
                        st.markdown("#### Right")
                        st.multiselect(
                            label='Vertical location',
                            default=st.session_state.current_annotation[tag]['right_height'],
                            options=list(st.session_state.dash_conf['annotation_height'].keys()),
                            format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
                            label_visibility=visibility,
                            key=f'annotation_height_right_{tag}',
                        )
                        st.markdown("#### Left")
                        st.multiselect(
                            label='Vertical location',
                            default=st.session_state.current_annotation[tag]['left_height'],
                            options=list(st.session_state.dash_conf['annotation_height'].keys()),
                            format_func=lambda x: st.session_state.dash_conf['annotation_height'][x],
                            label_visibility=visibility,
                            key=f'annotation_height_left_{tag}',
                        )
                    case _:
                        pass
        else:
            pass
    with an_form:
        st.form_submit_button('save_annotation',
                              type='primary',
                              on_click=store_annotation_callback,
                              )


def store_annotation_callback():
    annotation_dict = {}
    for tag in st.session_state.dash_conf['annotation_tags']:
        annotation_meta = defaultdict(lambda: 0)
        if tag in st.session_state[f"tags_{st.session_state['cur_study_instance_uid']}"]:
            annotation_meta.update({
                'probability': int(st.session_state[f'annotation_proba_{tag}']),
                'severity': int(st.session_state[f'annotation_severity_{tag}']),
                'urgency': int(st.session_state[f'annotation_urgency_{tag}']),
                'side': int(st.session_state[f'annotation_side_{tag}']),
            })
            match annotation_meta['side']:
                case 0:
                    annotation_meta['left_height'] = st.session_state.dash_conf['default_annotation_height']
                    annotation_meta['right_height'] = st.session_state.dash_conf['default_annotation_height']
                case 1:  # left
                    annotation_meta['left_height'] = st.session_state[f'annotation_height_left_{tag}']
                    annotation_meta['right_height'] = st.session_state.dash_conf['default_annotation_height']
                case 2:  # right
                    annotation_meta['left_height'] = st.session_state.dash_conf['default_annotation_height']
                    annotation_meta['right_height'] = st.session_state[f'annotation_height_right_{tag}']
                case 3:  # both
                    annotation_meta['left_height'] = st.session_state[f'annotation_height_left_{tag}']
                    annotation_meta['right_height'] = st.session_state[f'annotation_height_right_{tag}']
                case _:
                    raise ValueError('We consider only annotation_side 0-3 = irrelevant, left, right, both')
        else:
            annotation_meta.update({
                'probability': int(st.session_state.dash_conf['default_annotation_probability']),
                'severity': int(st.session_state.dash_conf['default_annotation_severity']),
                'urgency': int(st.session_state.dash_conf['default_annotation_urgency']),
                'side': int(st.session_state.dash_conf['default_annotation_side']),
                'left_height': st.session_state.dash_conf['default_annotation_height'],
                'right_height': st.session_state.dash_conf['default_annotation_height'],
            })
        annotation_dict[tag] = annotation_meta
    # print(annotation_dict)

    save_annotation(
        study_instance_uid=st.session_state['cur_study_instance_uid'],
        accession_number=st.session_state['cur_accession_number'],
        annotation=annotation_dict,
        conn=st.session_state['db_conn']
    )
    st.success('Successfully stored your annotation.')
