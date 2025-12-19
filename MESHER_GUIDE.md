# Mesher User Guide

## Quick Start

```bash
cd scripts
./mesher.py --input-path ../pclouds/file.ply --output-path ../meshes/output.glb
```

## Single File Processing

```bash
./mesher.py --input-path INPUT.ply --output-path OUTPUT.glb \
  --meshing-method poisson \
  --simplify 100000 \
  --cleanup
```

### Arguments

**Required:**
- `--input-path`: Input point cloud file (.ply)
- `--output-path`: Output mesh file

**Optional:**
- `--meshing-method`: poisson (default), bpa, alpha
- `--output-format`: glb (default), obj, stl, ply
- `--simplify TARGET`: Target triangle count
- `--simplify-method`: uniform (default), adaptive
- `--cleanup`: Remove artifacts and duplicates
- `--fill-holes SIZE`: Fill holes up to SIZE
- `--origin-bottom`: Move origin to bottom-left
- `--generate-tex`: Generate texture (experimental)

## Batch Processing

Process entire directories:

```bash
./mesher.py --input-path ../pclouds \
  --output-dir ../meshes \
  --output-format glb \
  --meshing-method poisson \
  --simplify 100000
```

**Output**: `filename_method.format` (e.g., `chiller_poisson.glb`)

## Methods

**Poisson** (Recommended)
- Watertight meshes
- Best for complete scans
- Automatic artifact removal

**Ball Pivoting (BPA)**
- Fast
- Preserves detail
- May have holes

**Alpha Shapes**
- Good for sparse data
- Adjustable detail level

## Post-Processing

**Cleanup** (`--cleanup`)
- Removes duplicates
- Fixes degenerate triangles
- Removes small components

**Simplification** (`--simplify`)
- Reduces poly count
- Uniform: Even reduction
- Adaptive: Preserves features

**Hole Filling** (`--fill-holes`)
- Fills gaps in mesh
- Specify max hole size

**Origin** (`--origin-bottom`)
- Moves mesh to [0,0,0]
- Aligns to lower-left corner

## Examples

**High-quality mesh:**
```bash
./mesher.py --input-path scan.ply --output-path mesh.glb \
  --meshing-method poisson --simplify 200000 --cleanup
```

**Fast preview:**
```bash
./mesher.py --input-path scan.ply --output-path preview.obj \
  --meshing-method bpa --simplify 50000
```

**Batch convert:**
```bash
./mesher.py --input-path ./scans --output-dir ./meshes \
  --output-format stl --meshing-method poisson
```

## Tips

- Use Poisson for watertight meshes
- Simplify to 100K-200K for good balance
- Enable cleanup for production meshes
- Use adaptive simplification to preserve details
