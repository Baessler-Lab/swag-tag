import typing

import streamlit as st

from image.itk_image import ImageBuffer


def get_max_slices():
    max_slices = 0
    for img in st.session_state['images']:
        img: ImageBuffer
        if int(img.GetSize()[-1]) > max_slices:
            max_slices = int(img.GetSize()[-1])
    return max_slices


def st_image_box(fig_spot: st.container):
    with fig_spot:
        imgs = st.session_state['images']
        imgs: typing.List[ImageBuffer]

        img_spots = []
        # show windowed images
        for im_no, img in enumerate(imgs):
            img_spots.append(st.image(
                # image=img.windowed_array_2D_slice(slice_no=st.session_state['slice_no']),
                use_column_width=True,
            ))

        update_fig_window(img_spots)
        return img_spots


def update_fig_window(img_spots: typing.List[st.empty]):
    for img_spot, img in zip(img_spots, st.session_state['images']):
        img: ImageBuffer
        img.set_window(window_pct=st.session_state['window_borders'])
        img.apply_window()

        img_spot.image(
            image=img.windowed_array_2D_slice(slice_no=st.session_state['slice_no']),
            use_column_width=True,
            # use_column_width=True,
        )
