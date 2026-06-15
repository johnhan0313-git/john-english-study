"""Build data/dict_lookup.json from open vocabulary sources."""

from __future__ import annotations

from app.data_paths import get_data_dir
from app.services.vocabulary.dict_lookup_builder import build_dict_lookup


def main() -> None:
    build_dict_lookup(get_data_dir())


if __name__ == "__main__":
    main()
