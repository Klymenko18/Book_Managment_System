import pytest

mod = pytest.importorskip("src.services.recommendations")
if not hasattr(mod, "recommend_by_genre"):
    pytest.skip("recommend_by_genre not implemented", allow_module_level=True)

def test_recommend_by_genre_empty_input():
    out = mod.recommend_by_genre([], target_genre="Fiction")
    assert out == []
