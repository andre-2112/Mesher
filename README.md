# Automated Mesh Viewer

Interactive dual-pane viewer for point clouds and meshes with automated mesh generation.

## Project Structure

```
Open3D/
├── scripts/          # Python scripts
│   ├── mesher.py     # Core meshing functionality
│   ├── test_all.py   # Automated mesh generation
│   └── viewer.py     # Interactive dual-pane viewer
├── pclouds/          # Point cloud files (.ply)
├── meshes/           # Generated mesh files
├── docs/             # Documentation and development notes
└── README.md         # This file
```

## Features

- **Automated Mesh Generation**: Execute all meshing commands with a single script
- **Dual-Pane Viewer**: Side-by-side point cloud and mesh visualization
- **Interactive Controls**: Dropdown menus to switch between meshing methods and export formats
- **3D Navigation**: Full orbit/rotation controls for both views

## Quick Start

### 1. Generate All Meshes

Run the automation script to generate all mesh combinations:

```bash
cd scripts
./test_all.py
```

This will create 9 mesh files (3 methods × 3 formats) in the `meshes/` directory.

### 2. Launch the Viewer

Open the interactive dual-pane viewer:

```bash
cd scripts
./viewer.py
```

## Usage

### Automation Script

```bash
cd scripts
./test_all.py
```

**What it does:**
- Executes all meshing commands from Dev - 1.md
- Generates meshes using 3 methods: Poisson, Ball Pivoting (BPA), Alpha Shapes
- Exports in 3 formats: OBJ, GLB, STL
- Saves all outputs to `../meshes/` directory with filenames based on input file (e.g., `chiller_bpa.obj`)
- Provides progress feedback and summary

### Mesh Viewer

```bash
cd scripts
./viewer.py [OPTIONS]
```

**Options:**
- `--input_file PATH` - Path to input PLY point cloud (default: ../pclouds/chiller.ply)
- `--mesh_dir PATH` - Directory containing generated meshes (default: ../meshes)

**Controls:**
- **Left Pane**: Displays the original point cloud
- **Right Pane**: Displays the selected mesh
- **Meshing Method Dropdown**: Select between POISSON, BPA, or ALPHA
- **Export Format Dropdown**: Select between OBJ, GLB, or STL
- **Mouse**: Click and drag to rotate/orbit both views

## Meshing Methods

### Poisson Surface Reconstruction
- Best for smooth, watertight meshes
- Handles noisy data well
- May fail with certain point cloud configurations

### Ball Pivoting Algorithm (BPA)
- Preserves exact positions of original points
- Fast and reliable
- Good for detailed surface reconstruction

### Alpha Shapes
- Creates "shrink-wrapped" boundary around points
- Geometric approach
- Good for complex shapes

## Output Formats

- **OBJ**: Wavefront OBJ - widely supported, human-readable
- **GLB**: Binary glTF - optimized for web and 3D applications
- **STL**: STereoLithography - standard for 3D printing

## Troubleshooting

### Poisson Reconstruction Fails
If Poisson reconstruction shows "Found bad data" error, this is due to point cloud data issues. The BPA and Alpha methods should still work correctly.

### Mesh Not Found in Viewer
Ensure you've run `./test_all.py` first to generate the mesh files.

## Files

- `test_all.py` - Automated mesh generation script
- `viewer.py` - Interactive dual-pane viewer
- `mesher.py` - Core meshing functionality
- `meshes/` - Output directory for generated meshes
