"""Service-layer install dispatch: HOOK and MCP_SERVER are gated this release."""

import pytest

from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import AgentExtensionItem
from vibelens.services.extensions import catalog as catalog_service


def _make_item(extension_type: AgentExtensionType) -> AgentExtensionItem:
    return AgentExtensionItem(
        extension_id=f"tree:acme/widget:{extension_type.value}/x",
        extension_type=extension_type,
        name="x",
        source_url=f"https://github.com/acme/widget/tree/main/{extension_type.value}/x",
        repo_full_name="acme/widget",
        discovery_source="seed",
        topics=[],
        quality_score=0.0,
        popularity=0.0,
        stars=0,
        forks=0,
    )


class _FakeCatalog:
    def __init__(self, item: AgentExtensionItem):
        self._item = item

    def get_full(self, item_id: str):
        return self._item if item_id == self._item.extension_id else None

    def get_item(self, item_id: str):
        return self.get_full(item_id)


@pytest.mark.parametrize(
    "ext_type",
    [AgentExtensionType.HOOK, AgentExtensionType.MCP_SERVER],
)
def test_install_hook_or_mcp_returns_not_implemented(monkeypatch, ext_type):
    item = _make_item(ext_type)
    monkeypatch.setattr(catalog_service, "load_catalog", lambda: _FakeCatalog(item))
    with pytest.raises(NotImplementedError, match=ext_type.value):
        catalog_service.install_extension(
            item_id=item.extension_id, target_platform="claude", overwrite=True
        )


def test_install_repo_returns_not_implemented(monkeypatch):
    item = _make_item(AgentExtensionType.REPO)
    monkeypatch.setattr(catalog_service, "load_catalog", lambda: _FakeCatalog(item))
    with pytest.raises(NotImplementedError, match="REPO"):
        catalog_service.install_extension(
            item_id=item.extension_id, target_platform="claude", overwrite=True
        )


def test_install_unknown_id_raises_keyerror(monkeypatch):
    item = _make_item(AgentExtensionType.SKILL)
    monkeypatch.setattr(catalog_service, "load_catalog", lambda: _FakeCatalog(item))
    with pytest.raises(KeyError):
        catalog_service.install_extension(
            item_id="does-not-exist", target_platform="claude", overwrite=True
        )


def test_install_no_catalog_raises_keyerror(monkeypatch):
    monkeypatch.setattr(catalog_service, "load_catalog", lambda: None)
    with pytest.raises(KeyError):
        catalog_service.install_extension(
            item_id="anything", target_platform="claude", overwrite=True
        )
