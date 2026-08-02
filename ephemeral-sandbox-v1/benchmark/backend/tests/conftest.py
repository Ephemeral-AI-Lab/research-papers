import os
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def symlink_or_skip() -> Callable[..., None]:
    def create(
        link: Path,
        target: Path,
        *,
        target_is_directory: bool = False,
    ) -> None:
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as error:
            if os.name == "nt" and getattr(error, "winerror", None) == 1314:
                pytest.skip("Windows symlink privilege is unavailable")
            raise

    return create
