__version__ = "0.0.4"

from .duration import GoDuration
from .parser import parse_compose_files

assert parse_compose_files is not None
assert GoDuration is not None
