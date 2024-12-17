import pytest

# Simulación de localStorage en un diccionario para pruebas


class MockLocalStorage:
    def __init__(self):
        self.storage = {}

    def getItem(self, key):
        return self.storage.get(key, None)

    def setItem(self, key, value):
        self.storage[key] = value


@pytest.fixture
def mock_local_storage():
    return MockLocalStorage()

# Función para simular la lógica de cambio de tema


def apply_theme(localStorage, theme):
    themes = {
        "light": {"disabled": False, "enabled": True},
        "dark": {"disabled": True, "enabled": False}
    }
    localStorage.setItem("theme", theme)
    return themes[theme]

# Pruebas Unitarias


def test_apply_light_theme(mock_local_storage):
    result = apply_theme(mock_local_storage, "light")
    assert mock_local_storage.getItem("theme") == "light"
    assert result["disabled"] is False
    assert result["enabled"] is True


def test_apply_dark_theme(mock_local_storage):
    result = apply_theme(mock_local_storage, "dark")
    assert mock_local_storage.getItem("theme") == "dark"
    assert result["disabled"] is True
    assert result["enabled"] is False
