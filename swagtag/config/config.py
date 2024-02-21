import json
import os
import typing
from pathlib import Path
import streamlit as st
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
                 templates: typing.Union[str, Path],
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
        self.templates_dir = self.root_dir / 'templates'
        self.templates_dir.mkdir(exist_ok=True,
                                 parents=True,
                                 mode=0o775)

        # # define output paths
        # self.out_dir = self.data_dir / 'output'
        # self.out_dir.mkdir(exist_ok=True,
        #                    parents=True)


if "page" in st.session_state:
    match st.session_state['page']:
        case 'llm':
            CONFIG_YAML_NAME = "llm-tag-config.yaml"
        case 'swag-tag':
            CONFIG_YAML_NAME = "config.yaml"
        case _:
            raise ValueError("'page' needs to be defined in st.session_state")
else:
    CONFIG_YAML_NAME = "config.yaml"

# load yaml
# raise RuntimeError("CONFIG_DIR = %s", os.getenv("CONFIG_DIR",))
CONFIG_PY_FPATH = Path(os.getenv("CONFIG_DIR", __file__))
CONFIG_YAML_FPATH = CONFIG_PY_FPATH.with_name(CONFIG_YAML_NAME)
CONFIG_DB_FPATH = CONFIG_PY_FPATH.with_name('db_config.yaml')
with CONFIG_DB_FPATH.open("r") as f:
    CONFIG_DICT = yaml.safe_load(f)

with CONFIG_YAML_FPATH.open("r") as f:
    DASHBOARD_CONF = yaml.safe_load(f)

sql_conf = DASHBOARD_CONF['sql']

DATA_DIR = "/mnt/nfs_swag_nas/group_data/llm_eval"
DASH_CONF = DASHBOARD_CONF['dashboard']

# init configss
path_conf = PathConfiguration(**CONFIG_DICT["local_fs"])
TEMPLATE_DIR = path_conf.templates_dir
DEFAULT_TEMPLATE_NAME = 'swag-tag-template'
with (TEMPLATE_DIR / f"{DEFAULT_TEMPLATE_NAME}.json").open('r') as f:
    DEFAULT_TEMPLATE = json.load(f)

orth_conf = OrthancConfig(**CONFIG_DICT["orthanc"])

db_conf = CONFIG_DICT["db"]

sql_conf: typing.Mapping[str, typing.Any]

MODEL_CONFIG = {
    'name': 'Llama-2-70b-chat-hf',
    'path': '/home/pwoznicki/git/text-generation-webui/models/Llama-2-70b-chat-hf/',
    'kwargs': {
        "load_in_8bit": True,
        "device_map": "auto",
    }
}
# LLM TAG SERVER config
LLM_TAG_SERVER_CONF = DASHBOARD_CONF["llm-tag-server"]
DEFAULT_LLM = LLM_TAG_SERVER_CONF.get("default-llm", "llama-2-70b-8bit")
PORT = LLM_TAG_SERVER_CONF.get("port", 5000)
ENDPOINT = f"{LLM_TAG_SERVER_CONF.get('endpoint', 'localhost')}:{PORT}"
