#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import textwrap
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "usd" / "materialx_shaderball"
LAYERS_DIR = OUTPUT_ROOT / "layers"
PACKAGE_MATERIALS_DIR = OUTPUT_ROOT / "materials"
PACKAGE_ENVIRONMENT_DIR = OUTPUT_ROOT / "environment"
SOURCE_SHADERBALL_USDC = OUTPUT_ROOT / "ShaderBall.usdc"
SOURCE_ENVIRONMENT_HDR = REPO_ROOT / "viewer" / "san_giuseppe_bridge_2k.hdr"
STAGE_UP_AXIS = "Z"
TEXTURE_MODES = ("linked", "portable")


@dataclass(frozen=True)
class MaterialSpec:
    key: str
    suite: str
    family: str
    variant: str
    source_dir: str
    source_file: str
    package_dir: str


def _family_sort_key(family: str) -> tuple[int, str]:
    priority = {
        "open_pbr_surface": 0,
        "standard_surface": 1,
        "gltf_pbr": 2,
    }
    return (priority.get(family, 99), family)


def _discover_specs() -> list[MaterialSpec]:
    specs: list[MaterialSpec] = []
    for suite, source_group in (("showcase", "showcase"), ("library", "surfaces")):
        suite_root = REPO_ROOT / "materials" / source_group
        for family_dir in sorted((p for p in suite_root.iterdir() if p.is_dir()), key=lambda p: _family_sort_key(p.name)):
            for material_dir in sorted((p for p in family_dir.iterdir() if p.is_dir()), key=lambda p: p.name):
                mtlx_files = sorted(material_dir.glob("*.mtlx"))
                if not mtlx_files:
                    continue
                source_file = mtlx_files[0]
                rel_dir = material_dir.relative_to(REPO_ROOT).as_posix()
                specs.append(
                    MaterialSpec(
                        key=f"{suite}/{family_dir.name}/{material_dir.name}",
                        suite=suite,
                        family=family_dir.name,
                        variant=material_dir.name,
                        source_dir=rel_dir,
                        source_file=source_file.name,
                        package_dir=f"{suite}/{family_dir.name}/{material_dir.name}",
                    )
                )
    return specs


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


def _copy_material_payloads(specs: list[MaterialSpec], texture_mode: str) -> dict[str, str]:
    material_name_map: dict[str, str] = {}
    for spec in specs:
        source_dir = REPO_ROOT / spec.source_dir
        dest_dir = PACKAGE_MATERIALS_DIR / spec.package_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        source_file = source_dir / spec.source_file
        root = ET.parse(source_file).getroot()
        _rewrite_texture_paths(root, source_dir, dest_dir, texture_mode)
        ET.indent(root)
        ET.ElementTree(root).write(dest_dir / spec.source_file, encoding="utf-8", xml_declaration=True)

        surfacematerial = root.find("surfacematerial")
        if surfacematerial is None:
            raise ValueError(f"No <surfacematerial> in {source_file}")
        material_name_map[spec.key] = surfacematerial.attrib["name"]
    return material_name_map


def _suite_material_variant_name(spec: MaterialSpec) -> str:
    return f"{spec.family}__{spec.variant}"


def _suite_material_variant_lines(
    spec: MaterialSpec,
    material_name: str,
    root_prim: str,
    suite_prim: str,
    indent: str,
) -> list[str]:
    rel_path = f"../materials/{spec.package_dir}/{spec.source_file}"
    variant_name = _suite_material_variant_name(spec)
    return [
        f'{indent}"{variant_name}" {{',
        f'{indent}    def Scope "Materials" (',
        f'{indent}        prepend references = @{rel_path}@</MaterialX/Materials>',
        f"{indent}    )",
        f"{indent}    {{",
        f"{indent}    }}",
        "",
        f'{indent}    over "shader_ball"',
        f"{indent}    {{",
        f'{indent}        over "Preview_Mesh"',
        f"{indent}        {{",
        f'{indent}            over "Preview_Mesh" (',
        f'{indent}                prepend apiSchemas = ["MaterialBindingAPI"]',
        f"{indent}            )",
        f"{indent}            {{",
        f"{indent}                rel material:binding = </{root_prim}/{suite_prim}/Materials/{material_name}>",
        f"{indent}            }}",
        f"{indent}        }}",
        f'{indent}        over "Calibration_Mesh"',
        f"{indent}        {{",
        f'{indent}            over "Calibration_Mesh" (',
        f'{indent}                prepend apiSchemas = ["MaterialBindingAPI"]',
        f"{indent}            )",
        f"{indent}            {{",
        f"{indent}                rel material:binding = </{root_prim}/{suite_prim}/Materials/{material_name}>",
        f"{indent}            }}",
        f"{indent}        }}",
        f"{indent}    }}",
        f"{indent}}}",
    ]


def _build_materials_layer(specs: list[MaterialSpec], material_name_map: dict[str, str]) -> str:
    grouped: dict[str, dict[str, list[MaterialSpec]]] = defaultdict(lambda: defaultdict(list))
    for spec in specs:
        grouped[spec.suite][spec.family].append(spec)

    suites = sorted(grouped.keys())
    default_suite = "showcase" if "showcase" in grouped else suites[0]

    suite_defaults: dict[str, MaterialSpec] = {}
    for suite in suites:
        families = sorted(grouped[suite].keys(), key=_family_sort_key)
        default_family = "open_pbr_surface" if "open_pbr_surface" in grouped[suite] else families[0]
        suite_defaults[suite] = sorted(grouped[suite][default_family], key=lambda spec: spec.variant)[0]

    lines: list[str] = [
        "#usda 1.0",
        "(",
        '    defaultPrim = "materialx_shaderball"',
        f'    upAxis = "{STAGE_UP_AXIS}"',
        ")",
        "",
        'over "materialx_shaderball" (',
        "    variants = {",
        f'        string suite = "{default_suite}"',
        "    }",
        '    prepend variantSets = "suite"',
        ")",
        "{",
        '    variantSet "suite" = {',
    ]

    for suite in suites:
        suite_specs = sorted(
            [spec for family_specs in grouped[suite].values() for spec in family_specs],
            key=lambda spec: (_family_sort_key(spec.family), spec.variant),
        )
        default_spec = suite_defaults[suite]
        lines.extend(
            [
                f'        "{suite}" {{',
                f'            def Xform "{suite}" (',
                '                kind = "component"',
                "                variants = {",
                f'                    string material = "{_suite_material_variant_name(default_spec)}"',
                "                }",
                '                prepend variantSets = "material"',
                "            )",
                "            {",
                '                def Xform "shader_ball" (',
                '                    prepend references = @../ShaderBall.usdc@</root>',
                "                )",
                "                {",
                "                }",
                "",
                '                variantSet "material" = {',
            ]
        )
        for spec in suite_specs:
            lines.extend(
                _suite_material_variant_lines(
                    spec,
                    material_name_map[spec.key],
                    "materialx_shaderball",
                    suite,
                    "                    ",
                )
            )
            lines.append("")
        if lines[-1] == "":
            lines.pop()
        lines.extend(
            [
                "                }",
                "            }",
                "        }",
                "",
            ]
        )

    if lines[-1] == "":
        lines.pop()
    lines.extend(["    }", "}"])
    return "\n".join(lines)


def _prepare_environment_asset(texture_mode: str) -> str:
    if texture_mode == "portable":
        PACKAGE_ENVIRONMENT_DIR.mkdir(parents=True, exist_ok=True)
        portable_hdr_path = PACKAGE_ENVIRONMENT_DIR / SOURCE_ENVIRONMENT_HDR.name
        shutil.copy2(SOURCE_ENVIRONMENT_HDR, portable_hdr_path)
        return f"./environment/{SOURCE_ENVIRONMENT_HDR.name}"
    return f"../../viewer/{SOURCE_ENVIRONMENT_HDR.name}"


def _build_root_layer(environment_asset_path: str) -> str:
    return "\n".join(
        [
            "#usda 1.0",
            "(",
            '    defaultPrim = "materialx_shaderball"',
            '    subLayers = [',
            '        @./layers/materials.usda@',
            "    ]",
            f'    upAxis = "{STAGE_UP_AXIS}"',
            ")",
            "",
            'def Xform "materialx_shaderball" (',
            '    kind = "component"',
            ")",
            "{",
            '    def DomeLight "domelight"',
            "    {",
            f'        asset inputs:texture:file = @{environment_asset_path}@',
            '        token inputs:texture:format = "latlong"',
            "    }",
            "}",
        ]
    )


def _build_readme(specs: list[MaterialSpec], texture_mode: str) -> str:
    grouped: dict[str, dict[str, list[MaterialSpec]]] = defaultdict(lambda: defaultdict(list))
    for spec in specs:
        grouped[spec.suite][spec.family].append(spec)

    summary_lines: list[str] = []
    for suite in sorted(grouped.keys()):
        total = sum(len(grouped[suite][family]) for family in grouped[suite])
        summary_lines.append(f"- `{suite}/`: `{total}` materials")
        for family in sorted(grouped[suite].keys(), key=_family_sort_key):
            summary_lines.append(f"- `{suite}/{family}`: `{len(grouped[suite][family])}` materials")

    if texture_mode == "portable":
        materials_line = "- `materials/`: mirrored `.mtlx` tree plus vendored textures for a portable package"
        environment_line = "- `environment/`: vendored HDR used by the authored USD dome light"
        texture_mode_summary = "Built with `--texture-mode portable`. This package is self-contained: MaterialX texture inputs and the dome light HDR resolve within `usd/materialx_shaderball/`."
    else:
        materials_line = "- `materials/`: mirrored `.mtlx` tree with texture inputs rewritten to the original repository assets"
        environment_line = "- `environment/`: omitted in linked mode; the dome light points back to `viewer/san_giuseppe_bridge_2k.hdr`"
        texture_mode_summary = "Built with `--texture-mode linked`. This package depends on the source repository texture paths and HDR remaining available next to the USD package."

    return textwrap.dedent(
        f"""\
# MaterialX Shaderball

Unified USD browser for the repository's showcase and library materials, with suite on the root prim and a flat family-plus-material variant set on each suite prim.

## Files

- `ShaderBall.usdc`: USD-converted reusable shaderball geometry
- `shaderball.usda`: root scene shell, domelight, and sublayer stack
- `layers/materials.usda`: root `suite` variant set plus one flat `material` variant set on each suite prim
{materials_line}
{environment_line}

## Building

- Linked build: `python3 usd/build_usd_shaderball.py`
- Portable build: `python3 usd/build_usd_shaderball.py --texture-mode portable`

## Mirrored Material Tree

{os.linesep.join(summary_lines)}

## Notes

- Texture packaging: {texture_mode_summary}
- The `suite` variant set lives on `/materialx_shaderball`, authored in `layers/materials.usda`.
- After selecting a suite, choose that suite prim (`/materialx_shaderball/showcase` or `/materialx_shaderball/library`) and switch its `material` variant set.
- Each suite `material` variant name uses the form `family__material`.
- Each `material` variant composes one `.mtlx` document at `/materialx_shaderball/<suite>/Materials` and binds both shaderball meshes directly to the imported MaterialX material prim.
- `/materialx_shaderball/domelight` points at the same `san_giuseppe_bridge_2k.hdr` environment used by the original viewer so reflective materials pick up the HDR.
"""
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the unified MaterialX USD shaderball package.")
    parser.add_argument(
        "--texture-mode",
        choices=TEXTURE_MODES,
        default="linked",
        help="Whether generated MaterialX files should reference source repo textures or vendor them into the package.",
    )
    return parser.parse_args()


def _clean_output_root() -> None:
    for relative_path in ("layers", "materials", "environment", "shaderball.usda", "README.md"):
        path = OUTPUT_ROOT / relative_path
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def main() -> None:
    args = _parse_args()

    if not SOURCE_SHADERBALL_USDC.exists():
        raise FileNotFoundError(f"Missing required source geometry asset: {SOURCE_SHADERBALL_USDC}")
    if not SOURCE_ENVIRONMENT_HDR.exists():
        raise FileNotFoundError(f"Missing required environment asset: {SOURCE_ENVIRONMENT_HDR}")

    specs = _discover_specs()

    _clean_output_root()
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)

    material_name_map = _copy_material_payloads(specs, args.texture_mode)
    environment_asset_path = _prepare_environment_asset(args.texture_mode)
    (LAYERS_DIR / "materials.usda").write_text(_build_materials_layer(specs, material_name_map), encoding="utf-8")
    (OUTPUT_ROOT / "shaderball.usda").write_text(_build_root_layer(environment_asset_path), encoding="utf-8")
    (OUTPUT_ROOT / "README.md").write_text(_build_readme(specs, args.texture_mode), encoding="utf-8")


if __name__ == "__main__":
    main()
