# Auto Color Detection & Background Color Picker - Complete

## Summary

Successfully implemented automatic color detection for both Gaussian Splatting (SH coefficients) and standard RGB formats, plus a background color picker in the viewer.

## Features Implemented

### 1. Automatic Color Detection

Both `mesher.py` and `viewer.py` now automatically detect and convert Gaussian Splatting spherical harmonic coefficients to RGB colors.

**How it works:**
- Checks if point cloud has standard RGB colors
- If not, looks for Gaussian Splatting format (`f_dc_0`, `f_dc_1`, `f_dc_2`)
- Automatically converts SH coefficients to RGB using formula: `RGB = 0.5 + SH_C0 * sh_dc`
- Works transparently - no user action required

**Supported formats:**
- ✓ Standard RGB PLY files
- ✓ Gaussian Splatting PLY files with SH coefficients

### 2. Background Color Picker

Added dropdown menu to viewer with 5 background color options:
- **Ice** (default) - Off-white: `[0.94, 0.97, 0.98]`
- White - Pure white: `[1.0, 1.0, 1.0]`
- Light Gray - `[0.9, 0.9, 0.9]`
- Dark Gray - `[0.2, 0.2, 0.2]`
- Black - Pure black: `[0.0, 0.0, 0.0]`

Changes apply to both point cloud and mesh views simultaneously.

## Testing Results

### Mesher Tests

**Test 1: RGB format (chiller_rgb.ply)**
```
✓ Loaded 77000 points
✓ Transferred vertex colors from point cloud to mesh
✓ Generated mesh with colors
```

**Test 2: SH format (chiller_shc.ply)**
```
✓ Found Gaussian Splatting SH coefficients, converting to RGB...
✓ Converted 77000 points to RGB
✓ Transferred vertex colors from point cloud to mesh
✓ Generated mesh with colors
```

Both BPA and Alpha methods successfully transfer colors to meshes.

## Usage

### With Mesher
```bash
cd scripts

# Works with either format automatically
./mesher.py --input_file ../pclouds/chiller_shc.ply --output_filename ../meshes/output.obj --output_format obj --meshing_method bpa
./mesher.py --input_file ../pclouds/chiller_rgb.ply --output_filename ../meshes/output.obj --output_format obj --meshing_method bpa
```

### With Viewer
```bash
cd scripts

# Works with either format automatically
./viewer.py --input_file ../pclouds/chiller_shc.ply
./viewer.py --input_file ../pclouds/chiller_rgb.ply
```

Use the "Background Color" dropdown in the viewer to change the background.

## Files Modified

- `scripts/mesher.py` - Added `convert_sh_to_rgb()` helper and auto-detection
- `scripts/viewer.py` - Added `convert_sh_to_rgb()` helper, auto-detection, and background color picker
- `scripts/convert_sh_to_rgb.py` - Utility for manual conversion (still available)

## Technical Details

**SH to RGB Conversion Formula:**
```python
SH_C0 = 0.28209479177387814  # 0th order SH constant
rgb = 0.5 + SH_C0 * sh_dc
rgb = np.clip(rgb, 0.0, 1.0)
```

This converts the 0th order spherical harmonic coefficients (which represent base color) to standard RGB values in the [0, 1] range.
