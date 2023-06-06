import typing

import SimpleITK as sitk
import numpy as np

# import streamlit as st
from config.config import dash_conf


class ImageBuffer(sitk.Image):
    def __init__(
            self, *args,
            window_pct: typing.Tuple[float, float] = None,
            window_abs: typing.Tuple[float, float] = None,
            output_minmax: typing.Tuple[float, float] = (0, 255),
            **kwargs):

        super().__init__(*args, **kwargs)

        self.windowed_img = None
        if window_pct is not None:
            self.window_pct = window_pct
        else:
            self.window_pct = dash_conf['window_default_range']

        if window_abs is not None:
            self.window_abs = window_abs
        else:
            min_max = sitk.MinimumMaximumImageFilter()
            min_max.Execute(self)
            range = abs(min_max.GetMinimum() - min_max.GetMaximum())
            self.window_abs = self.window_pct[0] / 100. * range, self.window_pct[1] / 100. * range

            # TODO: we could consider a histogram/percentile based windowing as well
            # something like:
            # self.window_abs = \
            #     np.percentile(sitk.GetArrayViewFromImage(self), self.window_pct[0]), \
            #     np.percentile(sitk.GetArrayViewFromImage(self), self.window_pct[1])

        self.output_minmax = output_minmax

        # apply windowing

        self.apply_window()
        self.windowed_img: sitk.Image

    def set_window(
            self,
            window_pct: typing.Tuple[float, float] = None,
            window_abs: typing.Tuple[float, float] = None
    ):
        if window_abs is not None:
            self.window_abs = window_abs
        else:
            if window_pct is not None:
                self.window_pct = window_pct
                min_max = sitk.MinimumMaximumImageFilter()
                min_max.Execute(self)
                range = abs(min_max.GetMinimum() - min_max.GetMaximum())
                self.window_abs = self.window_pct[0] / 100. * range, self.window_pct[1] / 100. * range
            else:
                raise ValueError('You need to provide either window_abs or window_pct.')

    def apply_window(self):
        self.windowed_img = sitk.IntensityWindowing(
            self,
            windowMinimum=self.window_abs[0],
            windowMaximum=self.window_abs[1],
            outputMinimum=self.output_minmax[0],
            outputMaximum=self.output_minmax[1],
        )

    def windowed(self):
        return self.windowed_img

    def original(self):
        return self


def clone_img(img: sitk.Image) -> sitk.Image:
    """
    there is no itk.ImageDuplicater in SITK. Hacky workaround for deep copy
    :param img: input SITK image
    :return: deep copy of img
    """
    cloned_img = sitk.GetImageFromArray(sitk.GetArrayViewFromImage(img), isVector=False)

    # set meta info
    cloned_img.SetOrigin(img.GetOrigin())
    cloned_img.SetDirection(img.GetDirection())
    cloned_img.SetSpacing(img.GetSpacing())

    # TODO: check for meta tags and copy them as well

    return cloned_img


def clone_meta(source: sitk.Image, target: typing.Union[np.ndarray, sitk.Image]) -> sitk.Image:
    """
    copies Origin, Direction and Spacing from `source` to target
    :return: sitk.Image with meta from `source`
    """
    if not isinstance(target, sitk.Image):
        target = sitk.GetImageFromArray(target, isVector=False)

    # set meta info
    target.SetOrigin(source.GetOrigin())
    target.SetDirection(source.GetDirection())
    target.SetSpacing(source.GetSpacing())

    # check for meta tags and copy them as well

    return target
