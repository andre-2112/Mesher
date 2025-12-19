#!/usr/bin/env python3
"""
Point Cloud to Mesh Converter using Open3D

This script converts point cloud files (PLY format) to mesh files using various
meshing algorithms including Poisson surface reconstruction, Ball Pivoting, and Alpha shapes.

Usage:
    python mesher.py --input_file <path> --output_filename <path> --output_format <format> --meshing_method <method>

Example:
    python mesher.py --input_file chiller.ply --output_filename mesh.obj --output_format obj --meshing_method poisson
"""

import argparse
import sys
import os
import numpy as np
import open3d as o3d


def convert_sh_to_rgb(pcd, input_file):
    """Convert Gaussian Splatting SH coefficients to RGB colors if present."""
    if pcd.has_colors():
        return pcd  # Already has colors
    
    try:
        from plyfile import PlyData
        plydata = PlyData.read(input_file)
        vertex = plydata['vertex']
        
        if 'f_dc_0' in vertex.data.dtype.names:
            print("✓ Found Gaussian Splatting SH coefficients, converting to RGB...")
            sh_dc_0 = vertex['f_dc_0']
            sh_dc_1 = vertex['f_dc_1']
            sh_dc_2 = vertex['f_dc_2']
            
            # Convert SH to RGB
            SH_C0 = 0.28209479177387814
            rgb = np.stack([sh_dc_0, sh_dc_1, sh_dc_2], axis=1)
            rgb = 0.5 + SH_C0 * rgb
            rgb = np.clip(rgb, 0.0, 1.0)
            
            pcd.colors = o3d.utility.Vector3dVector(rgb)
            print(f"✓ Converted {len(pcd.points)} points to RGB")
    except ImportError:
        pass  # plyfile not installed
    except Exception:
        pass  # Could not convert
    
    return pcd


def load_point_cloud(input_file):
    """Load a point cloud from a PLY file."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    print(f"Loading point cloud from: {input_file}")
    pcd = o3d.io.read_point_cloud(input_file)
    
    if not pcd.has_points():
        raise ValueError("Point cloud is empty or invalid")
    # Auto-convert Gaussian Splatting SH coefficients to RGB
    pcd = convert_sh_to_rgb(pcd, input_file)
    
    print(f"Loaded {len(pcd.points)} points")
    return pcd


def estimate_normals(pcd):
    """Estimate normals for the point cloud if not already present."""
    if not pcd.has_normals():
        print("Estimating normals...")
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
        )
        # Orient normals consistently
        pcd.orient_normals_consistent_tangent_plane(k=15)
        print("Normals estimated and oriented")
    else:
        print("Point cloud already has normals")
    return pcd


def poisson_reconstruction(pcd):
    """Generate mesh using Poisson surface reconstruction."""
    print("Performing Poisson surface reconstruction...")
    
    # Force re-estimation of normals (original file has zero-value normals)
    print("Re-estimating normals for better Poisson reconstruction...")
    pcd.normals = o3d.utility.Vector3dVector([])
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=50)
    )
    pcd.orient_normals_consistent_tangent_plane(k=30)
    
    # Perform Poisson reconstruction with optimized parameters
    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, 
        depth=8,  # Lower depth for more tolerance with noisy data
        width=0,
        scale=1.1,
        linear_fit=True
    )
    
    print(f"Generated mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
    
    # Crop to point cloud bounding box to remove ground plane and other artifacts
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)
    print(f"After bounding box crop: {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
    
    # NOTE: Density cleanup removed to preserve watertight mesh
    # The raw Poisson output is watertight; cleanup creates holes
    print(f"Mesh is watertight: {mesh.is_watertight()}")
    
    return mesh


def ball_pivoting_reconstruction(pcd):
    """Generate mesh using Ball Pivoting algorithm."""
    print("Performing Ball Pivoting reconstruction...")
    
    # Ensure normals are estimated
    pcd = estimate_normals(pcd)
    
    # Estimate point cloud spacing
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    
    # Define ball radii (multiple radii for better coverage)
    radii = [avg_dist * multiplier for multiplier in [1.0, 2.0, 4.0]]
    print(f"Using ball radii: {radii}")
    
    # Perform Ball Pivoting
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd, o3d.utility.DoubleVector(radii)
    )
    
    # Transfer colors from point cloud to mesh if available
    if pcd.has_colors() and len(mesh.vertices) > 0:
        # BPA preserves vertex positions, so we can directly copy colors
        mesh.vertex_colors = pcd.colors
        print(f"Transferred vertex colors from point cloud to mesh")
    
    print(f"Generated mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
    return mesh


def alpha_shape_reconstruction(pcd):
    """Generate mesh using Alpha shapes."""
    print("Performing Alpha shape reconstruction...")
    
    # Estimate optimal alpha value
    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    alpha = avg_dist * 2.0
    
    print(f"Using alpha value: {alpha}")
    
    # Create alpha shape mesh
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha)
    
    # Transfer colors from point cloud to mesh if available
    if pcd.has_colors() and len(mesh.vertices) > 0:
        # Alpha shapes creates a subset of points, need to find corresponding colors
        pcd_tree = o3d.geometry.KDTreeFlann(pcd)
        colors = []
        for vertex in mesh.vertices:
            # Find nearest point in original point cloud
            [_, idx, _] = pcd_tree.search_knn_vector_3d(vertex, 1)
            colors.append(pcd.colors[idx[0]])
        mesh.vertex_colors = o3d.utility.Vector3dVector(np.array(colors))
        print(f"Transferred vertex colors from point cloud to mesh")
    
    print(f"Generated mesh with {len(mesh.vertices)} vertices and {len(mesh.triangles)} triangles")
    return mesh


def generate_mesh(pcd, method):
    """Generate mesh using the specified method."""
    if method == "poisson":
        return poisson_reconstruction(pcd)
    elif method == "bpa":
        return ball_pivoting_reconstruction(pcd)
    elif method == "alpha":
        return alpha_shape_reconstruction(pcd)
    else:
        raise ValueError(f"Unknown meshing method: {method}")


def set_origin_to_bottom(mesh):
    """Move mesh origin to bottom corner (min_bound) for better placement and 3D printing."""
    bbox = mesh.get_axis_aligned_bounding_box()
    translation = -bbox.min_bound
    mesh.translate(translation)
    print(f"  Moved origin to bottom corner (translated by {translation})")
    return mesh


def post_process_mesh(mesh, cleanup=True, simplify_target=None, fill_holes_size=None, origin_bottom=True):
    """Post-process mesh with cleanup, simplification, and hole filling."""
    original_triangles = len(mesh.triangles)
    
    if cleanup:
        print("Performing mesh cleanup...")
        # Remove duplicates and degenerate geometry
        mesh.remove_duplicated_vertices()
        mesh.remove_duplicated_triangles()
        mesh.remove_degenerate_triangles()
        mesh.remove_unreferenced_vertices()
        print(f"  Removed duplicates/degenerates: {original_triangles - len(mesh.triangles)} triangles")
    
    if simplify_target and simplify_target > 0:
        print(f"Simplifying mesh to {simplify_target} triangles...")
        if len(mesh.triangles) > simplify_target:
            mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=simplify_target)
            print(f"  Simplified: {original_triangles} → {len(mesh.triangles)} triangles")
        else:
            print(f"  Mesh already has fewer triangles ({len(mesh.triangles)}) than target")
    
    if fill_holes_size and fill_holes_size > 0:
        print(f"Attempting to fill holes smaller than {fill_holes_size}...")
        # Note: Open3D doesn't have built-in hole filling
        # This would require trimesh or other libraries
        try:
            import trimesh
            # Convert to trimesh for hole filling
            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)
            tmesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            
            # Fill holes
            tmesh.fill_holes()
            
            # Convert back
            mesh.vertices = o3d.utility.Vector3dVector(tmesh.vertices)
            mesh.triangles = o3d.utility.Vector3iVector(tmesh.faces)
            print(f"  Filled holes: now {len(mesh.triangles)} triangles")
        except ImportError:
            print("  Warning: trimesh not available for hole filling")
        except Exception as e:
            print(f"  Warning: hole filling failed: {e}")
    
    if origin_bottom:
        mesh = set_origin_to_bottom(mesh)
    
    return mesh


def save_mesh(mesh, output_filename, output_format):
    """Save the mesh to a file in the specified format."""
    # Determine the actual output path
    base_name, ext = os.path.splitext(output_filename)
    
    # Map format to extension
    format_extensions = {
        "obj": ".obj",
        "glb": ".glb",
        "stl": ".stl",
        "ply": ".ply"
    }
    
    if output_format not in format_extensions:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    # Use the specified format extension
    output_path = base_name + format_extensions[output_format]
    
    print(f"Saving mesh to: {output_path}")
    
    # Compute vertex normals for better visualization
    mesh.compute_vertex_normals()
    
    # Use trimesh for GLB export (Open3D's GLB exporter is broken in v0.19.0)
    if output_format == "glb":
        try:
            import trimesh
            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)
            
            # Convert colors if present
            if mesh.has_vertex_colors():
                colors = np.asarray(mesh.vertex_colors)
                colors_255 = (colors * 255).astype(np.uint8)
                tmesh = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_colors=colors_255)
            else:
                tmesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            
            tmesh.export(output_path)
            print(f"Mesh successfully saved to: {output_path} (using trimesh)")
        except ImportError:
            print("Warning: trimesh not installed, falling back to Open3D (may have issues)")
            print("Install with: pip install trimesh")
            success = o3d.io.write_triangle_mesh(output_path, mesh)
            if not success:
                raise RuntimeError(f"Failed to save mesh to: {output_path}")
    else:
        # Use Open3D for other formats
        success = o3d.io.write_triangle_mesh(output_path, mesh)
        
        if success:
            print(f"Mesh successfully saved to: {output_path}")
        else:
            raise RuntimeError(f"Failed to save mesh to: {output_path}")
    
    return output_path


def main():
    """Main function to parse arguments and execute the meshing pipeline."""
    parser = argparse.ArgumentParser(
        description="Convert point cloud to mesh using Open3D",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mesher.py --input_file cloud.ply --output_filename mesh.ply --output_format obj --meshing_method poisson
  python mesher.py --input_file cloud.ply --output_filename mesh.glb --output_format glb --meshing_method bpa
  python mesher.py --input_file cloud.ply --output_filename mesh.stl --output_format stl --meshing_method alpha
        """
    )
    
    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Path to input PLY point cloud file (must be a valid .ply file containing point cloud data)"
    )
    
    parser.add_argument(
        "--output_filename",
        type=str,
        required=True,
        help="Path to output mesh file (the file extension will be automatically set based on --output_format)"
    )
    
    parser.add_argument(
        "--output_format",
        type=str,
        default="obj",
        choices=["obj", "glb", "stl", "ply"],
        help="Output file format (default: obj)"
    )
    
    # Post-processing options
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Disable automatic mesh cleanup (remove duplicates, degenerates, unreferenced vertices)"
    )
    
    parser.add_argument(
        "--simplify",
        type=int,
        default=None,
        metavar="N",
        help="Simplify mesh to N triangles using quadric decimation (reduces file size)"
    )
    
    parser.add_argument(
        "--fill-holes",
        type=float,
        default=None,
        metavar="SIZE",
        help="Fill holes smaller than SIZE (requires trimesh, experimental)"
    )
    
    parser.add_argument(
        "--no-origin-bottom",
        action="store_true",
        help="Disable moving origin to bottom corner (keeps origin at center)"
    )
    
    parser.add_argument(
        "--meshing_method",
        type=str,
        default="poisson",
        choices=["poisson", "bpa", "alpha"],
        help="""Meshing algorithm to use (default: poisson):
        - poisson: Poisson Surface Reconstruction - Best for smooth, watertight meshes. 
                   Solves a global optimization problem and is highly effective at handling noisy data. 
                   Usually produces the most "professional" looking results.
        - bpa: Ball Pivoting Algorithm - Best for preserving the exact positions of the original points. 
               "Rolls" a virtual ball over the cloud to connect points into triangles.
        - alpha: Alpha Shapes - A more geometric approach that creates a "shrink-wrapped" boundary around the points.
        """
    )
    
    args = parser.parse_args()
    
    try:
        # Load point cloud
        pcd = load_point_cloud(args.input_file)
        
        # Generate mesh
        mesh = generate_mesh(pcd, args.meshing_method)
    
        # Post-process mesh
        cleanup = not args.no_cleanup
        origin_bottom = not args.no_origin_bottom
        mesh = post_process_mesh(
            mesh,
            cleanup=cleanup,
            simplify_target=args.simplify,
            fill_holes_size=args.fill_holes,
            origin_bottom=origin_bottom
        )
        
        # Validate mesh
        if len(mesh.triangles) == 0:
            print("WARNING: Generated mesh has no triangles. Try a different meshing method or adjust parameters.")
            sys.exit(1)
        
        # Save mesh
        save_mesh(mesh, args.output_filename, args.output_format)
        
        print("\nMeshing completed successfully!")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
