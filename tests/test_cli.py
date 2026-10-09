"""
Tests for doodleforge.cli module.
"""

import sys
from unittest.mock import patch
import pytest
from doodleforge.cli import main


def test_cli_presets(capsys):
    with patch.object(sys, "argv", ["doodleforge", "presets"]):
        main()
    captured = capsys.readouterr()
    assert "DoodleForge Preset Creatures" in captured.out
    assert "preset_cyber_cheetah" in captured.out


def test_cli_simulate(capsys):
    with patch.object(sys, "argv", ["doodleforge", "simulate", "--preset", "preset_wheeled_rover", "--duration", "0.5"]):
        main()
    captured = capsys.readouterr()
    assert "Simulation Telemetry" in captured.out
    assert "Distance Traveled:" in captured.out


def test_cli_optimize(capsys):
    with patch.object(sys, "argv", ["doodleforge", "optimize", "--preset", "preset_cyber_cheetah", "--generations", "1"]):
        main()
    captured = capsys.readouterr()
    assert "Optimization Results" in captured.out
    assert "Fitness History:" in captured.out
