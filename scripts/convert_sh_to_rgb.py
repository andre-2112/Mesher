#!/Library/Frameworks/Python.framework/Versions/3.12/bin/python3
"""
Convert Gaussian Splatting PLY with SH coefficients to standard RGB PLY
"""

import numpy as np
import open3d as o3d
from plyfile import PlyData
import sys

def convert_sh_to_rgb_ply(input_file, output_file):
    """Convert Gaussian Splatting PLY with SH coefficients to RGB PLY."""
    print(f"Loading {input_file}...")
    
    # Load with Open3D
    pcd = o3d.io.read_point_cloud(input_file)
    
    # Load with plyfile to get SH coefficients
    plydata = PlyData.read(input_file)
    vertex = plydata['vertex']
    
    # Extract SH coefficients
    sh_dc_0 = vertex['f_dc_0']
    sh_dc_1 = vertex['f_dc_1']
    sh_dc_2 = vertex['f_dc_2']
    
    # Convert SH to RGB
    SH_C0 = 0.28209479177387814
    rgb = np.stack([sh_dc_0, sh_dc_1, sh_dc_2], axis=1)
    rgb = 0.5 + SH_C0 * rgb
    rgb = np.clip(rgb, 0.0, 1.0)
    
    # Assign colors
    pcd.colors = o3d.utility.Vector3dVector(rgb)
    
    # Save
    print(f"Saving to {output_file}...")
    o3d.io.write_point_cloud(output_file, pcd)
    print(f"✓ Converted {len(pcd.points)} points with RGB colors")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./convert_sh_to_rgb.py input.ply output.ply")
        sys.exit(1)
    
    convert_sh_to_rgb_ply(sys.argv[1], sys.argv[2])
