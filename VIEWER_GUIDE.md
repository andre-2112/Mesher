# Viewer User Guide

## Quick Start

```bash
./scripts/viewer.py
```

The viewer launches with on-demand meshing - meshes are generated automatically if not found.

## Interface

### Dual-Panel Display
- **Left**: Point cloud visualization
- **Right**: Mesh visualization
- **Control Panel**: 600px wide sidebar with all controls

### Mesh Controls

**Method & Format**
- Method: Poisson, BPA, Alpha
- Format: OBJ, GLB, STL
- Changes update mesh instantly

**Mesh Scaling**
- Enter scale value (e.g., 2.0)
- Click Apply
- Dimensions update automatically

**Remeshing**
- Poly Count: Target triangle count
- Method: Uniform or Adaptive
- Click Remesh to apply

**Mesh Origin**
- X, Y, Z input fields
- Default: Lower-left corner (0, 0, 0)
- Click Apply to move mesh

### View Controls

**Synchronization** (Default: ON)
- Lock Rotation
- Lock Pan
- Lock Zoom

**UP Orientation**
- Y-up or Z-up (default: Z-up)

### Display Options

**Bounding Box**
- Blue wireframe boxes
- Shows geometry extent

**Wireframe**
- 2x thickness black edges
- Shows mesh topology

**Normals**
- Length: Adjustable (default: 0.01)
- Color: Color picker (default: red)
- Invert: Flip normal direction

**Rendering**
- ON: Solid mesh
- OFF: Transparent mesh

### Background Color
- Ice, White, Black, Gray

## Keyboard/Mouse

- **Left Click + Drag**: Rotate
- **Right Click + Drag**: Pan
- **Scroll**: Zoom

## Tips

- Use view sync to compare point cloud and mesh
- Adjust normal length for better visibility
- Use wireframe to inspect mesh quality
- Remesh to reduce poly count for performance
