import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
@pytest.fixture
def files():
    return [(p.name,p.read_bytes()) for p in sorted((ROOT/'sample_data').glob('*.pdf'))]
