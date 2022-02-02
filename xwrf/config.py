import os

import yaml
from donfig import Config

fn = os.path.join(os.path.dirname(__file__), 'config.yaml')

with open(fn) as f:
    defaults = yaml.safe_load(f)

config = Config('xwrf', defaults=[defaults])
config.ensure_file(fn, comment=False)
