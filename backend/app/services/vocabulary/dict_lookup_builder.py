from __future__ import annotations

import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SOURCES = [
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/1%20%E5%88%9D%E4%B8%AD-%E4%B9%B1%E5%BA%8F.txt", "junior"),
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/2%20%E9%AB%98%E4%B8%AD-%E4%B9%B1%E5%BA%8F.txt", "senior"),
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/3%20%E5%9B%9B%E7%BA%A7-%E4%B9%B1%E5%BA%8F.txt", "cet4"),
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/4%20%E5%85%AD%E7%BA%A7-%E4%B9%B1%E5%BA%8F.txt", "cet6"),
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/5%20%E8%80%83%E7%A0%94-%E4%B9%B1%E5%BA%8F.txt", "kaoyan"),
    ("https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/6%20%E6%89%98%E7%A6%8F-%E4%B9%B1%E5%BA%8F.txt", "toefl"),
]


def build_dict_lookup(data_dir: Path) -> Path:
    lookup: dict[str, dict[str, str]] = {}
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        for url, label in SOURCES:
            logger.info("Fetching vocabulary source %s...", label)
            text = client.get(url).raise_for_status().text
            for line in text.splitlines():
                line = line.strip()
                if not line or "\t" not in line:
                    continue
                word, trans = line.split("\t", 1)
                word = word.strip().lower()
                trans = trans.strip()
                if not word or not trans:
                    continue
                if word not in lookup or len(trans) > len(lookup[word]["definition"]):
                    lookup[word] = {"definition": trans, "source": label}

    data_dir.mkdir(parents=True, exist_ok=True)
    output = data_dir / "dict_lookup.json"
    payload = {
        "meta": {
            "source": "KyleBing/english-vocabulary",
            "count": len(lookup),
        },
        "entries": lookup,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    logger.info("Wrote %s (%s entries)", output, len(lookup))
    return output


def ensure_dict_lookup(data_dir: Path) -> Path | None:
    output = data_dir / "dict_lookup.json"
    if output.is_file() and output.stat().st_size > 0:
        return output
    return build_dict_lookup(data_dir)
