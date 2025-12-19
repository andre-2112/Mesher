# Open3D Mesher

Production-ready mesh generation toolkit with automatic color detection, advanced post-processing, and interactive visualization.

## Features

- **Auto Color Detection**: Automatically handles Gaussian Splatting SH coefficients and RGB formats
- **Watertight Meshes**: Poisson reconstruction with bounding box cropping (removes artifacts)
- **Post-Processing**: Cleanup, simplification, hole-filling, adaptive simplification, and texture generation
- **Interactive Viewer**: Dual-pane display with advanced controls:
  - Method/format switching and background color picker
  - Mesh scaling with dimension display
  - Interactive remeshing with poly count control
  - View synchronization (rotation/pan/zoom locked by default)
  - Display controls: bounding box, wireframe, normals visualization
  - UP orientation control (Y-up/Z-up)
  - Normal length and color customization
- **Batch Processing**: Process entire directories of point clouds
- **On-Demand Meshing**: Viewer generates missing meshes automatically
- **Multiple Formats**: Export to OBJ, GLB, STL, PLY

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate mesh (with automatic cleanup)
cd scripts
./mesher.py --input-path ../pclouds/chiller_rgb.ply --output-path ../meshes/output.glb

# Launch interactive viewer
./viewer.py
```


## Batch Processing

Process entire directories of point clouds:

```bash
# Process all .ply files in a directory
./mesher.py --input-path ../pclouds --output-dir ../meshes --output-format glb --meshing-method poisson --simplify 100000

# Output: chiller_rgb_poisson.glb, chiller_shc_poisson.glb, etc.
```

## On-Demand Viewer Meshing

The viewer automatically generates missing meshes:

```bash
./viewer.py  # Auto-generates meshes if not found
```

## Mesher Usage

```
usage: mesher.py [-h] --input-path INPUT_PATH --output-path OUTPUT_PATH
                 [--output_format {obj,glb,stl,ply}]
                 [--meshing-method {poisson,bpa,alpha}] [--no-cleanup]
                 [--simplify N] [--fill-holes SIZE]

Generate 3D meshes from point clouds with automatic color detection

options:
  -h, --help            show this help message and exit
  --input-path INPUT_PATH
                        Path to input PLY point cloud file
  --output-path OUTPUT_PATH
                        Path for output mesh file
  --output_format {obj,glb,stl,ply}
                        Output file format (default: obj)
  --meshing-method {poisson,bpa,alpha}
                        Meshing algorithm (default: poisson):
                        - poisson: Watertight meshes, best quality
                        - bpa: Preserves exact point positions
                        - alpha: Shrink-wrapped boundary
  --no-cleanup          Disable automatic mesh cleanup
  --simplify N          Simplify mesh to N triangles (reduces file size)
  --fill-holes SIZE     Fill holes smaller than SIZE (experimental)
```

## Examples

```bash
# Basic usage (with automatic cleanup)
./mesher.py --input-path input.ply --output-path output.glb

# Simplified to 100K triangles
./mesher.py --input-path input.ply --output-path output.glb --simplify 100000

# BPA method with OBJ export
./mesher.py --input-path input.ply --output-path output.obj \
            --output_format obj --meshing-method bpa

# Without cleanup (keep all geometry)
./mesher.py --input-path input.ply --output-path output.glb --no-cleanup

# With hole filling (requires trimesh)
./mesher.py --input-path input.ply --output-path output.glb --fill-holes 0.1
```

## Viewer Usage

```bash
# Default (uses chiller_rgb.ply)
./viewer.py

# Custom point cloud
./viewer.py --input-path ../pclouds/your_file.ply --mesh_dir ../meshes
```

**Viewer Controls:**
- **Left Pane**: Original point cloud
- **Right Pane**: Generated mesh
- **Method Dropdown**: Switch between Poisson/BPA/Alpha
- **Format Dropdown**: Switch between OBJ/GLB/STL
- **Background Dropdown**: Change background color (Ice/White/Gray/Dark/Black)
- **Mouse**: Click and drag to rotate/orbit

## Meshing Methods

| Method | Triangles | Watertight | Best For |
|--------|-----------|------------|----------|
| **Poisson** | 100K (simplified) | Nearly | Smooth surfaces, 3D printing |
| **BPA** | 65K | No | Preserving detail, fast processing |
| **Alpha** | 100K (simplified) | No | Complex shapes, visualization |

## Post-Processing

### Cleanup (Default ON)
Automatically removes:
- Duplicate vertices
- Degenerate triangles
- Unreferenced vertices

### Simplification
Reduces triangle count using quadric decimation:
```bash
--simplify 50000  # Reduce to 50K triangles
```

### Hole Filling (Experimental)
Attempts to fill small holes:
```bash
--fill-holes 0.1  # Fill holes smaller than 0.1 units
```

## Output Formats

- **GLB**: Binary glTF (best for web/3D apps) - 1.7-2.0 MB
- **OBJ**: Wavefront (widely supported, with colors) - 7-8 MB
- **STL**: For 3D printing (no colors) - 3-5 MB
- **PLY**: Point cloud format - Variable

## Installation

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Dependencies

- open3d >= 0.19.0
- numpy >= 1.20
- trimesh >= 4.0 (for GLB export and hole filling)
- plyfile >= 1.0 (for Gaussian Splatting support)

## Project Structure

```
Open3D/
├── scripts/
│   ├── mesher.py           # Mesh generation
│   ├── viewer.py           # Interactive viewer
│   ├── convert_sh_to_rgb.py # SH to RGB converter
│   └── test_all.py         # Batch processing
├── pclouds/                # Point cloud files
├── meshes/                 # Generated meshes
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── INSTALL.md             # Installation guide
└── README.md              # This file
```

## Troubleshooting

### GLB files won't load
Install trimesh: `pip install trimesh`

### Poisson shows warnings
"Failed to close loop" warnings are normal - the mesh is still generated successfully.

### Mesh has holes
Use Poisson method for best watertight results. For other methods, try `--fill-holes 0.1`.

## License

See repository for license information.

## Repository

https://github.com/andre-2112/Mesher
