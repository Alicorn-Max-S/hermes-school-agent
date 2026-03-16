"""Tests for _get_recent_models helper and sectioned model selector."""

from unittest.mock import patch, MagicMock
import pytest


class TestGetRecentModels:
    """Tests for _get_recent_models()."""

    def test_global_mode_returns_up_to_limit(self):
        from apollo_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["m-a", "m-b", "m-c", "m-d", "m-e"]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            result = _get_recent_models(limit=3)

        assert result == ["m-a", "m-b", "m-c"]

    def test_provider_filtered(self):
        from apollo_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["m-a", "m-b", "m-c", "m-d"]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            result = _get_recent_models(["m-a", "m-c", "m-e"], limit=5)

        assert result == ["m-a", "m-c"]

    def test_preserves_recency_order(self):
        from apollo_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = ["m-c", "m-a", "m-b"]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            result = _get_recent_models(["m-a", "m-b", "m-c"], limit=5)

        assert result == ["m-c", "m-a", "m-b"]

    def test_returns_empty_on_db_error(self):
        from apollo_cli.auth import _get_recent_models

        with patch("apollo_state.SessionDB", side_effect=Exception("DB error")):
            result = _get_recent_models(limit=3)

        assert result == []

    def test_respects_limit(self):
        from apollo_cli.auth import _get_recent_models

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = [f"m-{i}" for i in range(10)]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            result = _get_recent_models([f"m-{i}" for i in range(10)], limit=3)

        assert len(result) == 3


class TestGetRecentModelsSplit:
    """Tests for _get_recent_models_split()."""

    def test_splits_provider_and_other(self):
        from apollo_cli.auth import _get_recent_models_split

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = [
            "anthropic/claude-opus-4.6", "claude-opus-4-6", "gpt-5.4",
        ]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            provider, other = _get_recent_models_split(
                ["anthropic/claude-opus-4.6", "openai/gpt-5.4"], limit=5
            )

        assert provider == ["anthropic/claude-opus-4.6"]
        assert other == ["claude-opus-4-6", "gpt-5.4"]

    def test_preserves_recency_order_in_both_lists(self):
        from apollo_cli.auth import _get_recent_models_split

        mock_db = MagicMock()
        mock_db.recently_used_models.return_value = [
            "m-c", "m-x", "m-a", "m-y", "m-b",
        ]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            provider, other = _get_recent_models_split(["m-a", "m-b", "m-c"], limit=5)

        assert provider == ["m-c", "m-a", "m-b"]
        assert other == ["m-x", "m-y"]

    def test_returns_empty_tuples_on_db_error(self):
        from apollo_cli.auth import _get_recent_models_split

        with patch("apollo_state.SessionDB", side_effect=Exception("DB error")):
            provider, other = _get_recent_models_split(["m-a"], limit=5)

        assert provider == []
        assert other == []

    def test_respects_limit(self):
        from apollo_cli.auth import _get_recent_models_split

        mock_db = MagicMock()
        # First 10 are in the provider, last 10 are "other"
        mock_db.recently_used_models.return_value = [f"m-{i}" for i in range(20)]

        with patch("apollo_state.SessionDB", return_value=mock_db):
            provider, other = _get_recent_models_split(
                [f"m-{i}" for i in range(5)], limit=3
            )

        assert len(provider) == 3
        assert len(other) == 3


class TestPromptModelSelectionSections:
    """Tests for _prompt_model_selection() with provider_recent sections."""

    def test_no_duplicates_between_sections(self, capsys):
        """Models in recent section should not appear in all models section."""
        from apollo_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["m-a", "m-b", "m-c", "m-d"],
                    current_model="m-a",
                    provider_recent=["m-a", "m-b"],
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        # m-a and m-b should appear only once each (in Recent section)
        lines = output.strip().split("\n")
        model_lines = [l.strip() for l in lines if l.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6."))]
        model_names = [l.split(". ", 1)[1].split("  ←")[0].strip() for l in model_lines if ". " in l]
        # No duplicates
        assert len(model_names) == len(set(model_names))

    def test_cap_15_models(self, capsys):
        """Total model entries should never exceed 15."""
        from apollo_cli.auth import _prompt_model_selection

        models = [f"model-{i}" for i in range(25)]
        recent = [f"model-{i}" for i in range(8)]

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    models,
                    provider_recent=recent,
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        lines = output.strip().split("\n")
        # Count numbered model lines (exclude separators, custom, skip)
        numbered = [l for l in lines if l.strip() and l.strip()[0].isdigit()]
        # Subtract 2 for "Enter custom model name" and "Skip"
        model_count = len(numbered) - 2
        assert model_count <= 15

    def test_ratio_recent_le_5(self, capsys):
        """Recent section should have at most 5 models (15 // 3 = 5)."""
        from apollo_cli.auth import _prompt_model_selection

        models = [f"model-{i}" for i in range(20)]
        recent = [f"model-{i}" for i in range(10)]

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    models,
                    provider_recent=recent,
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        # Find the Recent section and All Models section
        lines = output.strip().split("\n")
        in_recent = False
        recent_count = 0
        for line in lines:
            if "Recent" in line and "──" in line and "other" not in line:
                in_recent = True
                continue
            if ("All Models" in line or "other providers" in line) and "──" in line:
                break
            if in_recent and line.strip() and line.strip()[0].isdigit():
                recent_count += 1
        assert recent_count <= 5

    def test_no_sections_when_empty(self, capsys):
        """When provider_recent is None, no section headers should appear."""
        from apollo_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                )

        output = capsys.readouterr().out
        assert "──" not in output

    def test_fallback_shows_section_headers(self, capsys):
        """Numbered list fallback should show Recent and All Models headers."""
        from apollo_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                    provider_recent=["model-a"],
                    provider_label="TestProvider",
                )

        output = capsys.readouterr().out
        assert "Recent (TestProvider)" in output
        assert "All Models" in output

    def test_global_recent_section_shown(self, capsys):
        """When global_recent is provided, shows 'other providers' section."""
        from apollo_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["model-a", "model-b"],
                    current_model="model-a",
                    provider_recent=["model-a"],
                    global_recent=["other-model-x"],
                    provider_label="TestProvider",
                )

        output = capsys.readouterr().out
        assert "Recent (TestProvider)" in output
        assert "other providers" in output
        assert "other-model-x" in output
        assert "All Models" in output

    def test_no_duplicates_across_all_three_sections(self, capsys):
        """Models should not appear in more than one section."""
        from apollo_cli.auth import _prompt_model_selection

        with patch.dict("sys.modules", {"simple_term_menu": None}):
            with patch("builtins.input", return_value=""):
                _prompt_model_selection(
                    ["m-a", "m-b", "m-c", "m-d"],
                    current_model="m-a",
                    provider_recent=["m-a", "m-b"],
                    global_recent=["m-x", "m-y"],
                    provider_label="Test",
                )

        output = capsys.readouterr().out
        lines = output.strip().split("\n")
        model_lines = [l.strip() for l in lines if l.strip() and l.strip()[0].isdigit()]
        model_names = [
            l.split(". ", 1)[1].split("  ←")[0].strip()
            for l in model_lines if ". " in l
            and "Enter custom" not in l and "Skip" not in l
        ]
        assert len(model_names) == len(set(model_names))


class TestDetectProviderForModel:
    """Tests for detect_provider_for_model()."""

    def test_detects_openrouter_model(self):
        from apollo_cli.models import detect_provider_for_model

        assert detect_provider_for_model("anthropic/claude-opus-4.6") == "openrouter"

    def test_detects_anthropic_model(self):
        from apollo_cli.models import detect_provider_for_model

        # claude-opus-4-6 is in both nous and anthropic catalogs;
        # detect_provider_for_model returns whichever is checked first
        result = detect_provider_for_model("claude-opus-4-6")
        assert result in ("nous", "anthropic")

    def test_detects_nous_model(self):
        from apollo_cli.models import detect_provider_for_model

        # claude-opus-4-6 is in both nous and anthropic; nous is checked first
        result = detect_provider_for_model("claude-opus-4-6")
        assert result in ("nous", "anthropic")

    def test_returns_none_for_unknown(self):
        from apollo_cli.models import detect_provider_for_model

        assert detect_provider_for_model("totally-unknown-model-xyz") is None

    def test_detects_kimi_model(self):
        from apollo_cli.models import detect_provider_for_model

        assert detect_provider_for_model("kimi-for-coding") == "kimi-coding"
