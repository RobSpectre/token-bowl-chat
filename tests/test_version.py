"""Test version information."""

from pathlib import Path

import tomli

import token_bowl_chat


def test_version() -> None:
    """Test that version is defined and matches pyproject.toml."""
    assert hasattr(token_bowl_chat, "__version__")
    assert isinstance(token_bowl_chat.__version__, str)
    assert len(token_bowl_chat.__version__) > 0

    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomli.load(f)

    # Ensure __init__.py and pyproject.toml versions match
    assert token_bowl_chat.__version__ == pyproject["project"]["version"], (
        f"Version mismatch: __init__.py has {token_bowl_chat.__version__} "
        f"but pyproject.toml has {pyproject['project']['version']}"
    )
