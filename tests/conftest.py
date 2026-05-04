from pathlib import Path
import sys
import pytest

pytest_plugins = 'sphinx.testing.fixtures'

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


@pytest.fixture(scope='session')
def rootdir() -> Path:
    return Path(__file__).parent / 'roots'
