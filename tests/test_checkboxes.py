from ui.checkboxes import mod_matches_filter, parse_mod_filter


def test_parse_mod_filter_supports_quoted_values():
    assert parse_mod_filter('dependencies:"Dark Terrain" order:2') == ["dependencies:Dark Terrain", "order:2"]


def test_parse_mod_filter_supports_unquoted_multiword_values():
    assert parse_mod_filter("dark dependencies:Remove Foilage order:2") == [
        "dark",
        "dependencies:Remove Foilage",
        "order:2",
    ]
    assert parse_mod_filter("order: 2") == ["order: 2"]


def test_parse_mod_filter_preserves_backslashes():
    assert parse_mod_filter(r"default:C:\Mods\Terrain") == [r"default:C:\Mods\Terrain"]
    assert parse_mod_filter("author:O'Connor") == ["author:O'Connor"]
    assert parse_mod_filter('default:url("s2r://image"), url("s2r://fallback")') == [
        'default:url("s2r://image"), url("s2r://fallback")'
    ]


def test_mod_matches_filter_by_name_with_and_semantics():
    assert mod_matches_filter("Dark Terrain", {}, "dark terrain")
    assert not mod_matches_filter("Dark Terrain", {}, "dark weather")


def test_mod_matches_filter_by_manifest_keys_and_nested_values():
    manifest = {
        "order": 2,
        "always": False,
        "browser": {"name": "d2pfx", "category": "terrain"},
        "dependencies": ["Weather FX"],
    }

    assert mod_matches_filter("Dark Terrain", manifest, "order:2 browser:d2pfx category:terrain")
    assert mod_matches_filter("Dark Terrain", manifest, 'dependencies:"weather fx"')
    assert mod_matches_filter("Dark Terrain", manifest, "dependencies:weather fx")
    assert not mod_matches_filter("Dark Terrain", manifest, "order:3")
    assert not mod_matches_filter("Dark Terrain", manifest, "missing:value")


def test_mod_matches_filter_handles_boolean_manifest_values():
    assert mod_matches_filter("Always Visible", {"always": True}, "always:true")
    assert not mod_matches_filter("Always Visible", {"always": True}, "always:false")


def test_mod_matches_filter_supports_dotted_paths_and_prefers_top_level_keys():
    manifest = {
        "version": ">=1.14",
        "browser": {"name": "terrain-remix", "version": "2.0", "category": "terrains"},
    }

    assert mod_matches_filter("D2PFX TERRAINS - Terrain Remix", manifest, "version:1.14")
    assert not mod_matches_filter("D2PFX TERRAINS - Terrain Remix", manifest, "version:2.0")
    assert mod_matches_filter("D2PFX TERRAINS - Terrain Remix", manifest, "browser.version:2.0")
    assert mod_matches_filter("D2PFX TERRAINS - Terrain Remix", manifest, "name:terrain-remix")
    assert mod_matches_filter("D2PFX TERRAINS - Terrain Remix", manifest, "mod:d2pfx")


def test_mod_matches_filter_searches_map_keys_and_json_null():
    manifest = {
        "browser": {
            "author": None,
            "tags": {"anime": True, "adult": False},
        }
    }

    assert mod_matches_filter("Browser Mod", manifest, "tags:anime")
    assert mod_matches_filter("Browser Mod", manifest, "browser.tags.anime:true")
    assert mod_matches_filter("Browser Mod", manifest, "author:null")
    assert not mod_matches_filter("Browser Mod", manifest, "author:none")


def test_mod_matches_filter_supports_paths_through_setting_lists():
    manifest = {"settings": [{"key": "fetch_grids", "type": "button"}]}

    assert mod_matches_filter("Custom Hero Grids", manifest, "settings.type:button")
    assert mod_matches_filter("Custom Hero Grids", manifest, "settings.key:fetch_grids")
