# Installation Guide

## Prerequisites

- Python 3.12 or higher
- macOS (tested on macOS)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `open3d` - 3D data processing library
- `numpy` - Numerical computing
- `trimesh` - Mesh processing (for GLB export)
- `plyfile` - PLY file reading (for Gaussian Splatting support)

### 2. Verify Installation

```bash
python3 -c "import open3d; import trimesh; import plyfile; print('✓ All dependencies installed')"
```

## Quick Start

### Generate Meshes

```bash
cd scripts

# Generate watertight mesh (default: Poisson + GLB)
./mesher.py --input_file ../pclouds/chiller_rgb.ply --output_filename ../meshes/output.glb

# Specify method and format
./mesher.py --input_file ../pclouds/chiller_rgb.ply \
            --output_filename ../meshes/output.obj \
            --output_format obj \
            --meshing_method bpa
```

### Launch Viewer

```bash
cd scripts

# Use default file (chiller_rgb.ply)
./viewer.py

# Specify custom file
./viewer.py --input_file ../pclouds/your_file.ply
```

## Features

- **Auto Color Detection** - Automatically converts Gaussian Splatting SH coefficients to RGB
- **Watertight Meshes** - Poisson method creates hermetically closed meshes
- **Multiple Formats** - Export to OBJ, GLB, or STL
- **Interactive Viewer** - Dual-pane display with background color picker

## Meshing Methods

- **Poisson** (default) - Creates watertight meshes, best for 3D printing
- **BPA** - Preserves exact point positions, faster
- **Alpha** - Shrink-wrapped boundary, good for visualization

## Supported Formats

- **GLB** (default) - Binary glTF, best for web/3D apps
- **OBJ** - Wavefront, widely supported, includes colors
- **STL** - For 3D printing (no color support)

## Troubleshooting

### "Command not found"
Make scripts executable:
```bash
chmod +x scripts/*.py
```

### "Module not found"
Ensure you're using the correct Python:
```bash
which python3
pip install -r requirements.txt
```

### GLB files won't load
The `trimesh` library is required for GLB export:
```bash
pip install trimesh
```

## File Structure

```
Open3D/
├── scripts/          # Python scripts
│   ├── mesher.py     # Mesh generation
│   ├── viewer.py     # Interactive viewer
│   └── convert_sh_to_rgb.py  # Utility
├── pclouds/          # Point cloud files (.ply)
├── meshes/           # Generated meshes
├── docs/             # Documentation
├── requirements.txt  # Python dependencies
└── README.md         # Project overview
```

## Next Steps

1. Generate meshes: `./scripts/mesher.py --help`
2. Launch viewer: `./scripts/viewer.py`
3. Explore different meshing methods and formats
