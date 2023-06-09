import typing

import streamlit as st

from image.itk_image import ImageBuffer


def st_image_box(fig_spot: st.container):
    with fig_spot:
        imgs = st.session_state['images']
        imgs: typing.List[ImageBuffer]
        # show windowed images
        st.image(map(lambda x: x.windowed_view_2D_slice(slice_no=st.session_state['slice_no']), imgs))


def update_fig_window(image_id):
    for img in st.session_state['images']:
        img: ImageBuffer
        img.set_window(window_pct=st.session_state['window_borders'])
