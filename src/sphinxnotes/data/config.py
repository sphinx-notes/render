"""
sphinxnotes.data.config
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: Copyright 2025~2026 by the Shengyu Zhang.
:license: BSD, see LICENSE for details.
"""

from sphinx.application import Sphinx
from sphinx.config import Config as SphinxConfig


class Config:
    """Global config of extesion."""

    template_debug: bool

    date_fmt: str
    time_fmt: str
    datetime_fmt: str


def _config_inited(app: Sphinx, config: SphinxConfig) -> None:
    Config.template_debug = config.data_template_debug

    Config.date_fmt = config.data_date_fmt
    Config.time_fmt = config.data_time_fmt
    Config.datetime_fmt = config.data_datetime_fmt


def setup(app: Sphinx):
    app.add_config_value('data_template_debug', False, '', bool)
    app.add_config_value('data_date_fmt', '%Y-%m-%d', '', str)
    app.add_config_value('data_time_fmt', '%H:%M:%S', '', str)
    app.add_config_value('data_datetime_fmt', '%Y-%m-%d %H:%M:%S', '', str)

    app.connect('config-inited', _config_inited)
