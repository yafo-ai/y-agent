import importlib.util
import pathlib
import typing as t


def parse_config(config_file: str):
    file = pathlib.Path(config_file)

    spec = importlib.util.spec_from_file_location('settings', file)
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    include_keys = [
        'FASTAPI_HOST',
        'FASTAPI_PORT',
        'DB_CONNECT_STR',
        'IS_RECORD_OPERATION_LOG',
        'WEB_NAME',
        'WEB_DESC'
    ]
    kv: t.Dict[str, t.Any] = {
        k.lower(): v for k, v in vars(settings).items() if not k.startswith('_') and k in include_keys
    }

    return kv


if __name__ == "__main__":
    config = parse_config("./src/configs/server_config.py")
    print(config)
    pass
