import typing

import streamlit as st

from image.itk_image import ImageBuffer


def image_control(**kwargs):
    assert 'img_spots' in kwargs
    img_spots = kwargs['img_spots']
    with st.expander("Image controls", expanded=True):
        st.slider(
            label="Min/Max Values for Window?",
            value=st.session_state.dash_conf['window_default_range'],
            **st.session_state.dash_conf['window_default_min_max'],
            key='window_border_slider',
            on_change=callback_window_border_slider,
            kwargs=dict(img_spots=img_spots)

        )
        st.slider(
            label="Slice number on z-axis",
            min_value=0,
            max_value=get_max_slices(),
            key='slice_no',
            on_change=update_fig_window,
            kwargs=dict(img_spots=img_spots)
        )


def get_max_slices():
    max_slices = 0
    for img in st.session_state['images']:
        img: ImageBuffer
        if int(img.GetSize()[-1]) > max_slices:
            max_slices = int(img.GetSize()[-1])
    return max_slices


def st_image_box(fig_spots: typing.Sequence[st.container]):
    # with fig_spot:


    imgs = st.session_state['images']
    imgs: typing.List[ImageBuffer]

    img_spots = []
    # show windowed images
    for im_no, (img, fig_spot) in enumerate(zip(imgs, fig_spots)):
        with fig_spot:
            img_spots.append(st.image(
                image=img.windowed_array_2D_slice(slice_no=st.session_state['slice_no']),
                use_column_width=True,
            ))

    update_fig_window(img_spots)
    image_control(img_spots=img_spots)
    return img_spots


def callback_window_border_slider(img_spots: typing.List[st.empty]):
    if 'window_border_slider' in st.session_state:
        st.session_state['window_borders'] = st.session_state['window_border_slider']
    update_fig_window(img_spots)

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
