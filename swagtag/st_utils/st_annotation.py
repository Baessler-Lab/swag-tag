from collections import defaultdict

import streamlit as st

from annotation.io import save_annotation


def st_annotation_box():
    st.markdown('## Annotation ##')
    st.multiselect(
        label='Tags',
        options=st.session_state.dash_conf['annotation_tags'],
        default=[],
        key='tags',
    )
    with st.form('annotation_form'):
        for tag in st.session_state.dash_conf['annotation_tags']:
            visible = tag in st.session_state['tags']
            if visible:
                visibility = 'visible'
                st.markdown(f'### {tag} ###')
                st.radio(
                    label='Probability',
                    index=0,
                    options=list(st.session_state.dash_conf['annotation_probability']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_probability'][x],
                    label_visibility=visibility,
                    key=f'annotation_proba_{tag}',
                    horizontal=True,
                )

                st.radio(
                    label='Severity & urgency',
                    index=0,
                    options=list(st.session_state.dash_conf['annotation_severity']),
                    format_func=lambda x: st.session_state.dash_conf['annotation_severity'][x],
                    label_visibility=visibility,
                    key=f'annotation_severity_{tag}',
                    horizontal=True,
                )
            else:
                pass

        st.form_submit_button('save_annotation',
                              type='primary',
                              on_click=store_annotation_callback)


def store_annotation_callback():
    annotation_dict = {}
    for tag in st.session_state.dash_conf['annotation_tags']:
        annotation_meta = defaultdict(lambda: 0)
        if tag in tag in st.session_state['tags']:
            annotation_meta.update({
                'probability': int(st.session_state[f'annotation_proba_{tag}']),
                'severity': int(st.session_state[f'annotation_severity_{tag}']),
            })
        annotation_dict[tag] = annotation_meta
    # print(annotation_dict)

    save_annotation(
        study_instance_uid=st.session_state['cur_study_instance_uid'],
        accession_number=st.session_state['cur_accession_number'],
        annotation=annotation_dict,
        conn=st.session_state['db_conn']
    )
