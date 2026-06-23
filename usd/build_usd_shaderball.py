#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import textwrap
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "usd" / "materialx_shaderball_showcase"
LAYERS_DIR = OUTPUT_ROOT / "layers"
PACKAGE_MATERIALS_DIR = OUTPUT_ROOT / "materials"
SOURCE_SHADERBALL_USDC = OUTPUT_ROOT / "ShaderBall.usdc"
STAGE_UP_AXIS = "Z"
TEXTURE_MODES = ("linked", "portable")


@dataclass(frozen=True)
class MaterialSpec:
    variant: str
    family_scope: str
    source_dir: str
    source_file: str


MATERIAL_SPECS: list[MaterialSpec] = [
    MaterialSpec("openpbr_carpaint", "openpbr", "materials/showcase/open_pbr_surface/carpaint", "carpaint.mtlx"),
    MaterialSpec("openpbr_glass", "openpbr", "materials/showcase/open_pbr_surface/glass", "glass.mtlx"),
    MaterialSpec("openpbr_honey", "openpbr", "materials/showcase/open_pbr_surface/honey", "honey.mtlx"),
    MaterialSpec("openpbr_ketchup", "openpbr", "materials/showcase/open_pbr_surface/ketchup", "ketchup.mtlx"),
    MaterialSpec("openpbr_lightbulb", "openpbr", "materials/showcase/open_pbr_surface/lightbulb", "lightbulb.mtlx"),
    MaterialSpec("openpbr_pearl", "openpbr", "materials/showcase/open_pbr_surface/pearl", "pearl.mtlx"),
    MaterialSpec("openpbr_soapbubble", "openpbr", "materials/showcase/open_pbr_surface/soapbubble", "soapbubble.mtlx"),
    MaterialSpec("openpbr_velvet", "openpbr", "materials/showcase/open_pbr_surface/velvet", "velvet.mtlx"),
    MaterialSpec("standard_brick_procedural", "standard", "materials/showcase/standard_surface/brick_procedural", "brick_procedural.mtlx"),
    MaterialSpec("standard_carpaint", "standard", "materials/showcase/standard_surface/carpaint", "carpaint.mtlx"),
    MaterialSpec("standard_chrome", "standard", "materials/showcase/standard_surface/chrome", "chrome.mtlx"),
    MaterialSpec("standard_copper", "standard", "materials/showcase/standard_surface/copper", "copper.mtlx"),
    MaterialSpec("standard_glass", "standard", "materials/showcase/standard_surface/glass", "glass.mtlx"),
    MaterialSpec("standard_glass_tinted", "standard", "materials/showcase/standard_surface/glass_tinted", "glass_tinted.mtlx"),
    MaterialSpec("standard_gold", "standard", "materials/showcase/standard_surface/gold", "gold.mtlx"),
    MaterialSpec("standard_marble_solid", "standard", "materials/showcase/standard_surface/marble_solid", "marble_solid.mtlx"),
    MaterialSpec("standard_metal_brushed", "standard", "materials/showcase/standard_surface/metal_brushed", "metal_brushed.mtlx"),
    MaterialSpec("standard_onyx_hextiled", "standard", "materials/showcase/standard_surface/onyx_hextiled", "onyx_hextiled.mtlx"),
    MaterialSpec("standard_onyx_hextiled_no_scale", "standard", "materials/showcase/standard_surface/onyx_hextiled_no_scale", "onyx_hextiled_no_scale.mtlx"),
    MaterialSpec("standard_plastic", "standard", "materials/showcase/standard_surface/plastic", "plastic.mtlx"),
    MaterialSpec("standard_sheen", "standard", "materials/showcase/standard_surface/sheen", "sheen.mtlx"),
    MaterialSpec("standard_velvet", "standard", "materials/showcase/standard_surface/velvet", "velvet.mtlx"),
    MaterialSpec("standard_wood_grain", "standard", "materials/showcase/standard_surface/wood_grain", "wood_grain.mtlx"),
    MaterialSpec("standard_wood_tiled", "standard", "materials/showcase/standard_surface/wood_tiled", "wood_tiled.mtlx"),
]


def _rewrite_texture_paths(root: ET.Element, source_dir: Path, dest_dir: Path, texture_mode: str) -> None:
    for input_elem in root.iter("input"):
        if input_elem.attrib.get("type") != "filename":
            continue

        value = input_elem.attrib.get("value")
        if not value:
            continue

        source_path = Path(value)
        if source_path.is_absolute():
            continue

        resolved_source_path = (source_dir / source_path).resolve()
        if texture_mode == "portable":
            portable_texture_path = dest_dir / source_path
            portable_texture_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved_source_path, portable_texture_path)
            rewritten_path = source_path.as_posix()
        else:
            rewritten_path = Path(os.path.relpath(resolved_source_path, start=dest_dir.resolve())).as_posix()
        input_elem.set("value", rewritten_path)


def _copy_material_payloads(texture_mode: str) -> dict[str, str]:
    material_name_map: dict[str, str] = {}
    for spec in MATERIAL_SPECS:
        source_dir = REPO_ROOT / spec.source_dir
        dest_dir = PACKAGE_MATERIALS_DIR / spec.family_scope / spec.variant
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        source_file = source_dir / spec.source_file
        root = ET.parse(source_file).getroot()
        _rewrite_texture_paths(root, source_dir, dest_dir, texture_mode)
        ET.indent(root)
        ET.ElementTree(root).write(dest_dir / spec.source_file, encoding="utf-8", xml_declaration=True)

        surfacematerial = root.find("surfacematerial")
        if surfacematerial is None:
            raise ValueError(f"No <surfacematerial> in {source_file}")
        material_name_map[spec.variant] = surfacematerial.attrib["name"]
    return material_name_map


def _build_geometry_layer() -> str:
    return "\n".join(
        [
            "#usda 1.0",
            "(",
            '    defaultPrim = "materialx_shaderball_showcase"',
            f'    upAxis = "{STAGE_UP_AXIS}"',
            ")",
            "",
            'over "materialx_shaderball_showcase"',
            "{",
            '    def Xform "shader_ball" (',
            '        prepend references = @../ShaderBall.usdc@</root>',
            "    )",
            "    {",
            "    }",
            "}",
        ]
    )


def _build_materials_layer(material_name_map: dict[str, str]) -> str:
    lines: list[str] = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "materialx_shaderball_showcase"',
        f'    upAxis = "{STAGE_UP_AXIS}"',
        ")",
        "",
        'over "materialx_shaderball_showcase" (',
        "    variants = {",
        '        string material = "standard_gold"',
        "    }",
        '    prepend variantSets = "material"',
        ")",
        "{",
        '    variantSet "material" = {',
    ]

    for spec in MATERIAL_SPECS:
        rel_path = f"../materials/{spec.family_scope}/{spec.variant}/{spec.source_file}"
        material_name = material_name_map[spec.variant]
        lines.extend(
            [
                f'        "{spec.variant}" {{',
                '            def Scope "Materials" (',
                f'                prepend references = @{rel_path}@</MaterialX/Materials>',
                "            )",
                "            {",
                "            }",
                "",
                '            over "shader_ball"',
                "            {",
                '                over "Preview_Mesh"',
                "                {",
                '                    over "Preview_Mesh" (',
                '                        prepend apiSchemas = ["MaterialBindingAPI"]',
                "                    )",
                "                    {",
                f"                        rel material:binding = </materialx_shaderball_showcase/Materials/{material_name}>",
                "                    }",
                "                }",
                '                over "Calibration_Mesh"',
                "                {",
                '                    over "Calibration_Mesh" (',
                '                        prepend apiSchemas = ["MaterialBindingAPI"]',
                "                    )",
                "                    {",
                f"                        rel material:binding = </materialx_shaderball_showcase/Materials/{material_name}>",
                "                    }",
                "                }",
                "            }",
                "        }",
                "",
            ]
        )

    lines.extend(["    }", "}"])
    return "\n".join(lines)


def _build_root_layer() -> str:
    return "\n".join(
        [
            "#usda 1.0",
            "(",
            '    defaultPrim = "materialx_shaderball_showcase"',
            '    subLayers = [',
            '        @./layers/materials.usda@,',
            '        @./layers/geometry.usda@',
            '    ]',
            f'    upAxis = "{STAGE_UP_AXIS}"',
            ")",
            "",
            'def Xform "materialx_shaderball_showcase" (',
            '    kind = "component"',
            ")",
            "{",
            "}",
        ]
    )


def _build_readme(material_name_map: dict[str, str], texture_mode: str) -> str:
    variant_lines = "\n".join(f"- `{spec.variant}` -> `{material_name_map[spec.variant]}`" for spec in MATERIAL_SPECS)
    if texture_mode == "portable":
        materials_line = "- `materials/`: copied `.mtlx` documents plus vendored textures for a portable package"
        texture_mode_summary = "Built with `--texture-mode portable`. This package is self-contained: MaterialX texture inputs resolve within `usd/materialx_shaderball_showcase/`."
    else:
        materials_line = "- `materials/`: copied `.mtlx` documents with texture inputs rewritten to the original repository assets"
        texture_mode_summary = "Built with `--texture-mode linked`. This package depends on the source repository texture paths remaining available next to the USD package."
    return textwrap.dedent(
        f"""\
# MaterialX Shaderball Showcase

This package is a direct USD translation wrapper around the reusable GLB test geometry, using `ShaderBall.usdc` plus the curated MaterialX sample set from this repository.

## Files

- `ShaderBall.usdc`: USD-converted reusable shaderball geometry
- `shaderball_showcase.usda`: root scene shell and sublayer stack
- `layers/geometry.usda`: references `ShaderBall.usdc` under `shader_ball`
- `layers/materials.usda`: top-level `material` variant set, `.mtlx` composition, and mesh binding
{materials_line}

## Building

- Linked build: `python3 usd/build_usd_shaderball.py`
- Portable build: `python3 usd/build_usd_shaderball.py --texture-mode portable`

Use `linked` when you want the smallest generated package and are working inside this repository. In that mode, generated `.mtlx` files point back to the source textures under `materials/showcase/...`, so nothing is duplicated.

Use `portable` when you want to hand the package to another tool, machine, or web viewer as a self-contained folder. In that mode, the generator copies the referenced textures into the package so `usd/materialx_shaderball_showcase/` can be moved independently.

In practice, `linked` is the better default for version control, while `portable` is better for distribution and viewer deployment artifacts.

## Variants

{variant_lines}

## Notes

- Texture packaging: {texture_mode_summary}
- The variant set lives on `/materialx_shaderball_showcase`, authored in `layers/materials.usda`.
- Each variant composes one `.mtlx` document at `/materialx_shaderball_showcase/Materials` and binds `/materialx_shaderball_showcase/shader_ball/Preview_Mesh` directly to the imported MaterialX material prim.
- This generator intentionally avoids extra camera/light/reference-scene authoring so the package stays close to the original reusable GLB test setup.
"""
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the MaterialX USD shaderball showcase package.")
    parser.add_argument(
        "--texture-mode",
        choices=TEXTURE_MODES,
        default="linked",
        help="Whether generated MaterialX files should reference source repo textures or vendor them into the package.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if not SOURCE_SHADERBALL_USDC.exists():
        raise FileNotFoundError(f"Missing required source geometry asset: {SOURCE_SHADERBALL_USDC}")

    if LAYERS_DIR.exists():
        shutil.rmtree(LAYERS_DIR)
    if PACKAGE_MATERIALS_DIR.exists():
        shutil.rmtree(PACKAGE_MATERIALS_DIR)

    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

    material_name_map = _copy_material_payloads(args.texture_mode)
    (LAYERS_DIR / "geometry.usda").write_text(_build_geometry_layer(), encoding="utf-8")
    (LAYERS_DIR / "materials.usda").write_text(_build_materials_layer(material_name_map), encoding="utf-8")
    (OUTPUT_ROOT / "shaderball_showcase.usda").write_text(_build_root_layer(), encoding="utf-8")
    (OUTPUT_ROOT / "README.md").write_text(_build_readme(material_name_map, args.texture_mode), encoding="utf-8")


if __name__ == "__main__":
    main()
