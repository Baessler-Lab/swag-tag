import typing
from collections import Generator

import pandas as pd

from data_load.img_load import load_images_for_list_of_uris
from image.itk_image import ImageBuffer


class image_generator(Generator):
    def __init__(self):
        ...

    def send(self, **kwargs):
        ...

    def throw(self):
        raise StopIteration


def lookup_series_instance_uids_and_uris(df: pd.DataFrame, StudyInstanceUID: str) -> pd.DataFrame:
    return df.loc[df['StudyInstanceUID'] == StudyInstanceUID, ['SeriesInstanceUID', 'image_uri']]


def load_images_for_study(
        StudyInstanceUID: str,
        df: pd.DataFrame,
        source: str = 'filesystem',
        img_type: str = 'jpeg',
) -> typing.List[ImageBuffer]:
    # lookup uris
    series_instance_uid_to_image_uri = lookup_series_instance_uids_and_uris(df, StudyInstanceUID)

    # load images
    return load_images_for_list_of_uris(
        series_instance_uid_to_image_uri['image_uri'].to_list(),
        source=source,
        img_type=img_type)
