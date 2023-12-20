import streamlit as st




def app():
    st.set_page_config(
        page_title='Home',
        layout="wide",
    )
    # init_session_states()

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
