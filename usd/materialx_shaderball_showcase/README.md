# MaterialX Shaderball Showcase

This package is a direct USD translation wrapper around the reusable GLB test geometry, using `ShaderBall.usdc` plus the curated MaterialX sample set from this repository.

## Files

- `ShaderBall.usdc`: USD-converted reusable shaderball geometry
- `shaderball_showcase.usda`: root scene shell and sublayer stack
- `layers/geometry.usda`: references `ShaderBall.usdc` under `shader_ball`
- `layers/materials.usda`: top-level `material` variant set, `.mtlx` composition, and mesh binding
- `materials/`: copied `.mtlx` documents with texture inputs rewritten to the original repository assets

## Building

- Linked build: `python3 usd/build_usd_shaderball.py`
- Portable build: `python3 usd/build_usd_shaderball.py --texture-mode portable`

Use `linked` when you want the smallest generated package and are working inside this repository. In that mode, generated `.mtlx` files point back to the source textures under `materials/showcase/...`, so nothing is duplicated.

Use `portable` when you want to hand the package to another tool, machine, or web viewer as a self-contained folder. In that mode, the generator copies the referenced textures into the package so `usd/materialx_shaderball_showcase/` can be moved independently.

In practice, `linked` is the better default for version control, while `portable` is better for distribution and viewer deployment artifacts.

## Variants

- `openpbr_carpaint` -> `Car_Paint`
- `openpbr_glass` -> `Glass`
- `openpbr_honey` -> `Honey`
- `openpbr_ketchup` -> `Ketchup`
- `openpbr_lightbulb` -> `Light_Bulb`
- `openpbr_pearl` -> `Pearl`
- `openpbr_soapbubble` -> `Soap_Bubble`
- `openpbr_velvet` -> `Velvet`
- `standard_brick_procedural` -> `M_BrickPattern`
- `standard_carpaint` -> `Car_Paint`
- `standard_chrome` -> `Chrome`
- `standard_copper` -> `Copper`
- `standard_glass` -> `Glass`
- `standard_glass_tinted` -> `GlassTinted`
- `standard_gold` -> `Gold`
- `standard_marble_solid` -> `Marble_3D`
- `standard_metal_brushed` -> `Metal_Brushed`
- `standard_onyx_hextiled` -> `M_OnyxHextiled`
- `standard_onyx_hextiled_no_scale` -> `M_OnyxHextiledNoScale`
- `standard_plastic` -> `Plastic`
- `standard_sheen` -> `mat_sheen_test`
- `standard_velvet` -> `Velvet`
- `standard_wood_grain` -> `Tiled_Wood`
- `standard_wood_tiled` -> `Tiled_Wood`

## Notes

- Texture packaging: Built with `--texture-mode linked`. This package depends on the source repository texture paths remaining available next to the USD package.
- The variant set lives on `/materialx_shaderball_showcase`, authored in `layers/materials.usda`.
- Each variant composes one `.mtlx` document at `/materialx_shaderball_showcase/Materials` and binds `/materialx_shaderball_showcase/shader_ball/Preview_Mesh` directly to the imported MaterialX material prim.
- This generator intentionally avoids extra camera/light/reference-scene authoring so the package stays close to the original reusable GLB test setup.
