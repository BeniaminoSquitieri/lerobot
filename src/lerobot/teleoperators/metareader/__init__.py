from .config_metareader import MetaReaderConfig

try:
    from .metareader import MetaReaderTeleoperator
except ImportError as e:
    _metareader_import_error = e

    class MetaReaderTeleoperator:
        def __init__(self, *args, **kwargs):
            raise _metareader_import_error
