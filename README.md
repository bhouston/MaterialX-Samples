# material-samples

This repository organizes sample MaterialX materials (`.mtlx`) and related textures for reference rendering workflows.

## Purpose

The included viewer assets are provided so contributors can replicate a consistent rendering setup and produce reference renders with minimal environment differences. This is intended to aid reproducibility.

## Repository Layout

- `viewer/`
  - `san_giuseppe_bridge_2k.hdr` 
  - `ShaderBall.glb`
- `materials/`
  - `open_pbr_surface/`
  - `gltf_pbr/`
  - `standard_surface/`

Each material lives in its own directory under one of the three surface-type groups.
Material directories intentionally omit the group prefix to avoid duplication (for example, `materials/gltf_pbr/gold` rather than `materials/gltf_pbr/gltf_pbr_gold`).

## Source Provenance

Initial examples are derived from official MaterialX and Three.js sources:

## License

MIT License 
