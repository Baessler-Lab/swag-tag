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
    def __init__(self,
                 rootdir: typing.Union[str, Path],
                 fname: typing.Union[str, Path],
                 datadir: typing.Union[str, Path],
                 tablesdir: typing.Union[str, Path],
                 user: str = 'flaqua',
                 host: str = 'localhost',
                 **kwargs,
                 ):
        # define user and host
        self.user = user
        self.host = host

        # define root path
        if isinstance(rootdir,
                      Path):
            self.root_dir = rootdir
        elif isinstance(rootdir,
                        str):
            self.root_dir = Path(rootdir)
        else:
            raise NotImplementedError('You need to specify a rootdir as str or Path!')

        # define relative paths

        # define data path
        self.data_dir = self.root_dir / datadir
        self.data_dir.mkdir(exist_ok=True,
                            parents=True,
                            mode=0o775)

        # define csv paths
        self.tables_dir = self.root_dir / tablesdir
        self.tables_dir.mkdir(exist_ok=True,
                              parents=True,
                              mode=0o775)

        # # set fpath to csv file
        if Path(fname).is_absolute():
            self.tab_data_fpath = fname
        else:
            self.tab_data_fpath = self.tables_dir / fname
        #
        # # define output paths
        # self.out_dir = self.data_dir / 'output'
        # self.out_dir.mkdir(exist_ok=True,
        #                    parents=True)


# load yaml
CONFIG_PY_FPATH = Path(__file__)
CONFIG_YAML_NAME = "config.yaml"

CONFIG_YAML_FPATH = CONFIG_PY_FPATH.with_name(CONFIG_YAML_NAME)

with CONFIG_YAML_FPATH.open("r") as f:
    CONFIG_DICT = yaml.safe_load(f)

# init configss
path_conf = PathConfiguration(**CONFIG_DICT["local_fs"])

orth_conf = OrthancConfig(**CONFIG_DICT["orthanc"])

DASH_CONF = CONFIG_DICT['dashboard']

db_conf = CONFIG_DICT["db"]

sql_conf = CONFIG_DICT['sql']
sql_conf: typing.Mapping[str, typing.Any]
