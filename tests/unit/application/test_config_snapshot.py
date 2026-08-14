import math

import pytest

from evalforge.application.config_snapshot import (
    build_config_snapshot,
    canonical_json,
)


def test_equivalent_configs_produce_same_hash() -> None:
    config_a: dict[str, object] = {
        "model": "mock-llm",
        "top_k": 5,
        "retrieval": {
            "dense": True,
            "bm25": True,
        },
    }
    config_b: dict[str, object] = {
        "retrieval": {
            "bm25": True,
            "dense": True,
        },
        "top_k": 5,
        "model": "mock-llm",
    }

    snapshot_a = build_config_snapshot(config_a)
    snapshot_b = build_config_snapshot(config_b)

    assert snapshot_a.content_hash == snapshot_b.content_hash
    assert len(snapshot_a.content_hash) == 64


def test_different_configs_produce_different_hashes() -> None:
    snapshot_a = build_config_snapshot(
        {
            "model": "mock-llm",
            "top_k": 5,
        }
    )
    snapshot_b = build_config_snapshot(
        {
            "model": "mock-llm",
            "top_k": 10,
        }
    )

    assert snapshot_a.content_hash != snapshot_b.content_hash


def test_snapshot_is_detached_from_source_config() -> None:
    config: dict[str, object] = {
        "model": "mock-llm",
        "top_k": 5,
        "retrieval": {
            "dense": True,
        },
    }

    snapshot = build_config_snapshot(config)

    config["top_k"] = 10
    retrieval = config["retrieval"]

    assert isinstance(retrieval, dict)
    retrieval["dense"] = False

    assert snapshot.data["top_k"] == 5
    assert snapshot.data["retrieval"] == {
        "dense": True,
    }


def test_canonical_json_has_stable_compact_representation() -> None:
    payload = canonical_json(
        {
            "z": 1,
            "a": "中文",
        }
    )

    assert payload == '{"a":"中文","z":1}'


def test_non_finite_float_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_config_snapshot(
            {
                "temperature": math.nan,
            }
        )


def test_snapshot_accepts_nested_json_values() -> None:
    config: dict[str, object] = {
        "model": "mock-llm",
        "enabled": True,
        "temperature": 0.2,
        "stop": None,
        "tags": ["baseline", "rag"],
        "retrieval": {
            "top_k": 5,
        },
    }

    snapshot = build_config_snapshot(config)

    assert snapshot.data == config
