"""
Tests for doodleforge.presets module.
"""

import pytest
from doodleforge.presets import (
    ALL_PRESETS,
    get_all_presets,
    get_bipedal_strider,
    get_cyber_cheetah,
    get_hexapod_scuttler,
    get_preset_by_id,
    get_pterodactyl_flapper,
    get_wheeled_rover,
)


def test_all_presets_validity():
    presets = get_all_presets()
    assert len(presets) == len(ALL_PRESETS)
    assert len(presets) >= 5

    for bp in presets:
        assert bp.id is not None
        assert bp.name is not None
        assert len(bp.bodies) >= 2
        assert len(bp.joints) >= 1
        assert bp.torso_id in [b.id for b in bp.bodies]
        assert bp.locomotion is not None


def test_specific_presets():
    cheetah = get_cyber_cheetah()
    assert cheetah.id == "preset_cyber_cheetah"
    assert len([b for b in cheetah.bodies if b.part_type.value == "leg"]) == 4

    strider = get_bipedal_strider()
    assert len([b for b in strider.bodies if b.part_type.value == "leg"]) == 2

    hexapod = get_hexapod_scuttler()
    assert len([b for b in hexapod.bodies if b.part_type.value == "leg"]) == 6

    flapper = get_pterodactyl_flapper()
    assert len([b for b in flapper.bodies if b.part_type.value == "wing"]) == 2

    rover = get_wheeled_rover()
    assert len([b for b in rover.bodies if b.part_type.value == "wheel"]) == 2


def test_get_preset_by_id():
    found = get_preset_by_id("preset_cyber_cheetah")
    assert found is not None
    assert found.name == "Cyber-Cheetah"

    not_found = get_preset_by_id("preset_nonexistent")
    assert not_found is None
