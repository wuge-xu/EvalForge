from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, slots=True)
class ConfigSnapshot:
    data: dict[str, object]
    content_hash: str


def canonical_json(config: dict[str, object]) -> str:
    return json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def build_config_snapshot(
    config: dict[str, object],
) -> ConfigSnapshot:
    payload = canonical_json(config)

    normalized = json.loads(payload)

    if not isinstance(normalized, dict):
        raise ValueError("config root must be a JSON object")

    return ConfigSnapshot(
        data=cast(dict[str, object], normalized),
        content_hash=hashlib.sha256(
            payload.encode("utf-8"),
        ).hexdigest(),
    )
