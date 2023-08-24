import streamlit as st

from config.load_config import load_dash_conf
from swagtag.st_utils.sidebar import sidebar
from swagtag.st_utils.st_annotation import st_annotation_box
from swagtag.st_utils.st_image import st_image_box
from swagtag.st_utils.st_report import st_report_box
from swagtag.st_utils.states_swag_tag import init_session_states


def app():
    st.set_page_config(
        page_title='Home',
        layout="wide",
    )
    init_session_states()

    st.title('This are Baessler-Lab\'s annotation tools for radiology reports.')

    st.markdown(
        """
        ## Please select the scenario from the sidebar.
        Feel free to contact us using github.com/baessler-lab/swag-tag
        or via woznicki_p@ukw.de, amar.hekalo@uni-wuerzburg.de, orlaqua_f@ukw.de
        
        
        """
    )


if __name__ == '__main__':
    app()
