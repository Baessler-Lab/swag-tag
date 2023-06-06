import streamlit as st

from image.itk_image import ImageBuffer


def st_image_box(fig_spot: st.container, image_id: int = 0):
    with fig_spot:
        img = st.session_state['images'][image_id]
        img: ImageBuffer
        st.image(img.windowed())


def update_fig_window(image_id):
    img = st.session_state['images'][image_id]
    img: ImageBuffer
    img.set_window(window_pct=st.session_state['window_borders'])
