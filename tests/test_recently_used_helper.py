"""Tests for the recently-used model helper and sectioned model selector."""

from unittest.mock import patch, MagicMock
import pytest


class TestGetRecentlyUsedForProvider:
    """Tests for _get_recently_used_for_provider()."""

    def test_filters_to_provider_models(self):
        from hermes_cli.auth import _get_recently_used_for_provider

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["model-a", "model-b", "model-c"]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            per_provider, global_recent = _get_recently_used_for_provider(
                ["model-a", "model-c", "model-d"]
            )

        assert per_provider == ["model-a", "model-c"]
        assert global_recent == ["model-b"]

    def test_preserves_recency_order(self):
        from hermes_cli.auth import _get_recently_used_for_provider

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["model-c", "model-a", "model-b"]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            per_provider, _ = _get_recently_used_for_provider(
                ["model-a", "model-b", "model-c"]
            )

        # Order from DB should be preserved, not re-sorted
        assert per_provider == ["model-c", "model-a", "model-b"]

    def test_returns_empty_on_db_error(self):
        from hermes_cli.auth import _get_recently_used_for_provider

        with patch("hermes_state.SessionDB", side_effect=Exception("DB error")):
            per_provider, global_recent = _get_recently_used_for_provider(
                ["model-a", "model-b"]
            )

        assert per_provider == []
        assert global_recent == []

    def test_respects_limit(self):
        from hermes_cli.auth import _get_recently_used_for_provider

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = [f"model-{i}" for i in range(10)]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            per_provider, _ = _get_recently_used_for_provider(
                [f"model-{i}" for i in range(10)], limit=3
            )

        assert len(per_provider) == 3

    def test_global_recent_excludes_provider_models(self):
        from hermes_cli.auth import _get_recently_used_for_provider

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = [
            "provider-model", "other-model", "another-provider"
        ]

        with patch("hermes_state.SessionDB", return_value=mock_db):
            per_provider, global_recent = _get_recently_used_for_provider(
                ["provider-model", "another-provider"]
            )

        assert per_provider == ["provider-model", "another-provider"]
        assert global_recent == ["other-model"]


class TestPromptModelSelectionSections:
    """Tests for _prompt_model_selection() with recently_used sections."""

    def test_menu_entries_with_recently_used(self):
        """TerminalMenu choices should include section separators."""
        from hermes_cli.auth import _prompt_model_selection

        captured_choices = []

        class FakeMenu:
            def __init__(self, choices, **kwargs):
                captured_choices.extend(choices)

            def show(self):
                return None  # user cancelled

        with patch("hermes_cli.auth.TerminalMenu", FakeMenu, create=True):
            with patch.dict("sys.modules", {"simple_term_menu": MagicMock(TerminalMenu=FakeMenu)}):
                # We need to patch the import inside the function
                import importlib
                import hermes_cli.auth as auth_mod

                # Call with recently_used
                result = _prompt_model_selection(
                    ["model-a", "model-b", "model-c"],
                    current_model="model-a",
                    recently_used=["model-a", "model-b"],
                )

        # Result should be None (cancelled)
        assert result is None

    def test_no_sections_when_empty(self):
        """When recently_used is None, no section headers should appear."""
        from hermes_cli.auth import _prompt_model_selection

        captured_choices = []

        class FakeMenu:
            def __init__(self, choices, **kwargs):
                captured_choices.extend(choices)

            def show(self):
                return None

        with patch.dict("sys.modules", {"simple_term_menu": MagicMock(TerminalMenu=FakeMenu)}):
            _prompt_model_selection(
                ["model-a", "model-b"],
                current_model="model-a",
                recently_used=None,
            )

        # No separator lines should appear
        for choice in captured_choices:
            assert "──" not in choice

    def test_fallback_numbered_list_sections(self, capsys):
        """Numbered list fallback should show section headers without numbers."""
        from hermes_cli.auth import _prompt_model_selection

        # Force ImportError for TerminalMenu to trigger fallback
        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                    recently_used=["model-a"],
                )

        output = capsys.readouterr().out
        assert "Previously Used" in output
        assert "All Models" in output
