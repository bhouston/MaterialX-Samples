# MaterialX Shaderball

Unified USD browser for the repository's showcase and library materials, with suite on the root prim and a flat family-plus-material variant set on each suite prim.

## Files

- `ShaderBall.usdc`: USD-converted reusable shaderball geometry
- `shaderball.usda`: root scene shell, domelight, and sublayer stack
- `layers/materials.usda`: root `suite` variant set plus one flat `material` variant set on each suite prim
- `materials/`: mirrored `.mtlx` tree with texture inputs rewritten to the original repository assets
- `environment/`: omitted in linked mode; the dome light points back to `viewer/san_giuseppe_bridge_2k.hdr`

## Building

- Linked build: `python3 usd/build_usd_shaderball.py --texture-mode linked` (this is also the default)
- Portable build: `python3 usd/build_usd_shaderball.py --texture-mode portable`

## Mirrored Material Tree

- `library/`: `274` materials
- `library/open_pbr_surface`: `78` materials
- `library/standard_surface`: `110` materials
- `library/gltf_pbr`: `86` materials
- `showcase/`: `29` materials
- `showcase/open_pbr_surface`: `8` materials
- `showcase/standard_surface`: `16` materials
- `showcase/gltf_pbr`: `5` materials

## Notes

- Texture packaging: Built with `--texture-mode linked`. This package depends on the source repository texture paths and HDR remaining available next to the USD package.
- The `suite` variant set lives on `/materialx_shaderball`, authored in `layers/materials.usda`.
- After selecting a suite, choose that suite prim (`/materialx_shaderball/showcase` or `/materialx_shaderball/library`) and switch its `material` variant set.
- Each suite `material` variant name uses the form `family__material`.
- Each `material` variant composes one `.mtlx` document at `/materialx_shaderball/<suite>/Materials` and binds both shaderball meshes directly to the imported MaterialX material prim.
- `/materialx_shaderball/domelight` points at the same `san_giuseppe_bridge_2k.hdr` environment used by the original viewer so reflective materials pick up the HDR.
