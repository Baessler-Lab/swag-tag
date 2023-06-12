import typing

import SimpleITK as sitk
import numpy as np

# import streamlit as st
from config.config import dash_conf


class ImageBuffer(sitk.Image):
    '''
    Object wrapper class.
    This a wrapper for objects. It is initialiesed with the object to wrap
    and then proxies the unhandled getattribute methods to it.
    Other classes are to inherit from it.
    '''

    # noinspection PyMissingConstructor
    def __init__(
            self,
            img: sitk.Image,
            *args,
            window_pct: typing.Tuple[float, float] = None,
            window_abs: typing.Tuple[float, float] = None,
            output_minmax: typing.Tuple[float, float] = (0, 255),
            **kwargs):

        # assert 3D image
        if int(img.GetDimension()) == 2:
            img = sitk.JoinSeries(img)
        elif int(img.GetDimension()) == 3:
            pass
        else:
            raise NotImplementedError(f'Images with {int(img.GetDimension())} dimensions not yet considered')

        self._sitk_img = img
        self.windowed_img: sitk.Image
        self.__class__ = type(img.__class__.__name__,
                              (self.__class__, img.__class__),
                              {})

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

    # def __setattr__(self, name, value):
    #     setattr(self._sitk_img, name, value)

    def __getattr__(self, attr):
        # see if this object has attr
        # NOTE do not use hasattr, it goes into
        # infinite recursion
        if attr in self.__dict__:
            # this object has it
            return getattr(self, attr)
        # proxy to the wrapped object
        return getattr(self._sitk_img, attr)

    # @property
    # def windowed_img(self) -> sitk.Image:
    #     return self.windowed_img

    # @windowed_img.setter
    # def windowed_img(self, value):
    #     self.windowed_img = value

    @classmethod
    def cast_from_itk(
            cls,
            image: sitk.Image,
            window_pct: typing.Tuple[float, float] = None,
            window_abs: typing.Tuple[float, float] = None,
            output_minmax: typing.Tuple[float, float] = (0, 255),
    ) -> 'ImageBuffer':

        self = cls(
            img=image,
        )

        return self

    def set_window(
            self,
            window_pct: typing.Tuple[float, float] = None,
            window_abs: typing.Tuple[float, float] = None,
            output_minmax: typing.Tuple[float, float] = None,
    ):
        if output_minmax is not None:
            self.output_minmax = output_minmax

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
            self._sitk_img,
            windowMinimum=self.window_abs[0],
            windowMaximum=self.window_abs[1],
            outputMinimum=self.output_minmax[0],
            outputMaximum=self.output_minmax[1],
        )

    def windowed(self) -> sitk.Image:
        return self.windowed_img

    def windowed_view_2D_slice(
            self, slice_no: int = 0,
    ) -> np.ndarray:
        # slice_no should not exceed z-axis limits
        if slice_no >= int(self._sitk_img.GetSize()[-1]):
            slice_no = self._sitk_img.GetSize()[-1] - 1

        return sitk.GetArrayViewFromImage(self.windowed_img)[slice_no, :, :, ]

    def windowed_array_2D_slice(
            self, slice_no: int = 0,
    ) -> np.ndarray:
        # slice_no should not exceed z-axis limits
        if slice_no >= int(self._sitk_img.GetSize()[-1]):
            slice_no = self._sitk_img.GetSize()[-1] - 1

        return sitk.GetArrayFromImage(self.windowed_img)[slice_no, :, :, ]

    # @property
    def original(self) -> sitk.Image:
        return self._sitk_img

    def original_view_2D_slice(
            self, slice_no: int = 0,
    ) -> np.ndarray:
        # slice_no should not exceed z-axis limits
        if slice_no >= int(self._sitk_img.GetSize()[-1]):
            slice_no = self._sitk_img.GetSize()[-1] - 1

        return sitk.GetArrayViewFromImage(self.original())[slice_no, :, :, ]

    def original_array_2D_slice(
            self, slice_no: int = 0,
    ) -> np.ndarray:
        # slice_no should not exceed z-axis limits
        if slice_no >= int(self._sitk_img.GetSize()[-1]):
            slice_no = self._sitk_img.GetSize()[-1] - 1

        return sitk.GetArrayFromImage(self.original())[slice_no, :, :, ]


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
