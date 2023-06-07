import typing
from pathlib import Path

import yaml


class OrthancConfig(object):
    def __init__(
            self,
            port: int = 8042,
            host: str = "localhost",
            protocol: str = "http",
            source_modality: str = "PHOENIX",
            retrieve_ae_title: str = None,
            max_workers: int = 16,
    ):
        self.port = port
        self.host = host
        self.protocol = protocol
        self.peer_url = f"{protocol}://{host}:{port}"
        self.source_modality = source_modality
        self.retrieve_ae_title = retrieve_ae_title
        self.max_workers = max_workers


class PathConfiguration:
    def __init__(self, rootdir: typing.Union[str, Path],
                 fname: typing.Union[str, Path],
                 **kwargs,
                 ):

        # define root path
        if isinstance(rootdir,
                      Path):
            self.root_dir = rootdir
        elif isinstance(rootdir,
                        str):
            self.root_dir = Path(rootdir)
        else:
            raise NotImplementedError('You need to specify a DATA_DIR as str or Path!')

        # define relative paths

        # define data path
        self.data_dir = self.root_dir / 'data'

        # define csv paths
        self.tables_dir = self.data_dir / 'tables'
        self.tables_dir.mkdir(exist_ok=True,
                              parents=True)

        # set fpath to csv file
        if Path(fname).is_absolute():
            self.tab_data_fpath = fname
        else:
            self.tab_data_fpath = self.tables_dir / fname

        # define output paths
        self.out_dir = self.data_dir / 'output'
        self.out_dir.mkdir(exist_ok=True,
                           parents=True)


# load yaml
config_py_fpath = Path(__file__).with_name("config.yaml")
with config_py_fpath.open("r") as f:
    config_dict = yaml.safe_load(f)

# init configs
orth_conf = OrthancConfig(**config_dict["orthanc"])

dash_conf = config_dict['dashboard']

db_conf = config_dict["db"]

sql_conf = config_dict['sql']
