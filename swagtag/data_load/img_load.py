import logging
import os
import tempfile
import typing
from pathlib import Path

import SimpleITK as sitk
import streamlit as st
from dicom_base.orthanc import export
from dicom_base.orthanc import find

from config.config import orth_conf, dash_conf
from image.itk_image import ImageBuffer

log = logging.getLogger(__name__)


def load_images_for_list_of_uris(
        series_uris: typing.List[str],
        source: str = 'filesystem',
        img_type: str = 'jpeg',
) -> typing.List[ImageBuffer]:
    img_per_study = []
    for uri in series_uris:
        img_per_study.append(
            load_single_uri_image(
                uri,
                source=source,
                img_type=img_type,
            )
        )
    return img_per_study


@st.cache_data(max_entries=dash_conf['max_img_buffer_size'])
def load_single_uri_image(
        uri: str,
        source: str = 'filesystem',
        img_type: str = 'jpeg'
) -> ImageBuffer:
    match source.lower():
        case 'filesystem':
            match img_type.lower():
                case 'jpeg':
                    return ImageBuffer.cast_from_itk(
                        read_jpg(Path(uri))
                    )
                case 'nifti':
                    raise NotImplementedError('Nifti on filesystem not yet considered.')
                case _:
                    raise NotImplementedError('We currently support loading jpeg and nifti only.')
        case 'orthance':
            match img_type.lower():
                case 'jpeg':
                    raise NotImplementedError('Jpeg on orthanc not yet considered.')
                case 'nifti':
                    return ImageBuffer.cast_from_itk(
                        download_series_by_orthanc_id_to_nifti_tmpfile(orthanc_id=uri)
                    )
                case _:
                    raise NotImplementedError('We currently support loading jpeg and nifti only.')
        case _:
            raise NotImplementedError('We currently support loading from orthanc and filesystem only.')


def read_jpg(fpath: Path):
    img = sitk.ReadImage(fpath.absolute().__str__(), imageIO='JPEGImageIO')
    return img


def download_series_by_series_instance_uid_to_nifti_tmpfile(
        SeriesInstanceUID: str,
):
    series_ids = find.find(
        level="Series",
        peer_url=orth_conf.peer_url,
        SeriesInstanceUID=SeriesInstanceUID,
    )
    if len(series_ids) == 0:
        log.error(f"Nothing to download for {SeriesInstanceUID}")
        return

    with tempfile.NamedTemporaryFile(
            dir=Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')),
            suffix='.nii.gz',
            delete=True,
    ) as tmp_dir:
        series_path = export.download_to_tmpfile(
            orthanc_id=series_ids[0],
            level="Series",
            temp_file=tmp_dir,
            peer_url=orth_conf.peer_url,
            as_nifti=True,
        )
        return sitk.ReadImage(series_path.absolute().__str__(), imageIO='NIFTIImageIO')


def download_series_by_orthanc_id_to_nifti_tmpfile(
        orthanc_id: str,
) -> sitk.Image:
    with tempfile.NamedTemporaryFile(
            dir=Path(os.environ.get('XDG_RUNTIME_DIR', '/tmp')),
            suffix='.nii.gz',
            delete=True,
    ) as tmp_dir:
        series_path = export.download_to_tmpfile(
            orthanc_id=orthanc_id,
            level="Series",
            temp_file=tmp_dir,
            peer_url=orth_conf.peer_url,
            as_nifti=True,
        )
        return sitk.ReadImage(series_path.absolute().__str__(), imageIO='NIFTIImageIO')


def read_from_orthanc(uri: Path):
    with tempfile.TemporaryDirectory(os.environ['XDG_RUNTIME_DIR']) as tmp_dir:
        # download from orthanc
        get_series()
    img = sitk.ReadImage(fpath.absolute().__str__(), imageIO='JPEGImageIO')
