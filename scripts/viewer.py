#!/usr/bin/env python3
"""
Interactive Dual-Pane Mesh Viewer
Displays point cloud and mesh side-by-side with dropdown controls
for selecting meshing methods and export formats.
"""

import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import numpy as np
import argparse
import sys
from pathlib import Path


def convert_sh_to_rgb(pcd, input_file):
    """Convert Gaussian Splatting SH coefficients to RGB colors if present."""
    if pcd.has_colors():
        return pcd
    try:
        from plyfile import PlyData
        plydata = PlyData.read(input_file)
        vertex = plydata['vertex']
        if 'f_dc_0' in vertex.data.dtype.names:
            print("✓ Found Gaussian Splatting SH coefficients, converting to RGB...")
            sh_dc_0, sh_dc_1, sh_dc_2 = vertex['f_dc_0'], vertex['f_dc_1'], vertex['f_dc_2']
            SH_C0 = 0.28209479177387814
            rgb = np.stack([sh_dc_0, sh_dc_1, sh_dc_2], axis=1)
            rgb = 0.5 + SH_C0 * rgb
            rgb = np.clip(rgb, 0.0, 1.0)
            pcd.colors = o3d.utility.Vector3dVector(rgb)
            print(f"✓ Converted {len(pcd.points)} points to RGB")
    except:
        pass
    return pcd


class DualPaneMeshViewer:
    """Interactive viewer with side-by-side point cloud and mesh display."""
    
    def __init__(self, input_file, mesh_dir="meshes"):
        self.input_file = input_file
        self.mesh_dir = Path(mesh_dir)
        
        # Load point cloud
        self.point_cloud = self._load_point_cloud()
        
        # Available options
        self.methods = ["poisson", "bpa", "alpha"]
        self.formats = ["obj", "glb", "stl"]
        
        # Current selections (poisson now works and creates watertight meshes)
        self.current_method = "poisson"
        self.current_format = "glb"
        self.original_mesh = None
        self.scale_factor = 1.0
        self.current_mesh = None
        self.view_locks = {'rotation': True, 'pan': True, 'zoom': True}
        self.up_direction = "Z"
        self.show_bbox = False
        self.show_wireframe = False
        self.show_normals = False
        self.show_axes = True
        self.mesh_modified = False
        self.invert_normals = False
        self.show_rendering = True
        self.mesh_origin_offset = None
        
        # Display options
        self.show_bbox = False
        self.show_wireframe = False
        self.show_normals = False
        self.normal_length = 0.01
        self.normal_color = [1.0, 0.0, 0.0]  # Red
        
        # Initialize GUI
        self.app = gui.Application.instance
        self.app.initialize()
        
        self.window = self.app.create_window("Mesh Viewer - Point Cloud & Mesh Comparison", 1600, 800)
        self._setup_ui()
        self._update_mesh()  # Load mesh immediately
        
    def _load_point_cloud(self):
        """Load the point cloud from file."""
        try:
            pcd = o3d.io.read_point_cloud(self.input_file)
            if not pcd.has_points():
                raise ValueError("Point cloud is empty")
            
            # Ensure normals are present
            if not pcd.has_normals():
                pcd.estimate_normals(
                    search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
                )
            
            # Auto-convert Gaussian Splatting SH coefficients to RGB
            pcd = convert_sh_to_rgb(pcd, self.input_file)
            
            # Report color status
            if pcd.has_colors():
                print(f"Point cloud has vertex colors")
            else:
                print(f"Warning: Point cloud has no vertex colors")
            
            print(f"Loaded point cloud with {len(pcd.points)} points")
            return pcd
            
        except Exception as e:
            print(f"Error loading point cloud: {e}")
            sys.exit(1)
    
    def _load_mesh(self, method, format_type):
        """Load or generate mesh on-demand."""
        input_base = Path(self.input_file).stem
        mesh_filename = f"{input_base}_{method}.{format_type}"
        mesh_path = self.mesh_dir / mesh_filename
        
        # Check if mesh exists
        if not mesh_path.exists():
            print(f"Mesh not found: {mesh_path}")
            print(f"Generating {method} mesh on-demand...")
            
            # Import meshing functions
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            try:
                from mesher import generate_mesh, post_process_mesh
                
                # Generate mesh
                mesh = generate_mesh(self.point_cloud, method)
                
                # Post-process
                mesh, texture = post_process_mesh(
                    mesh,
                    pcd=self.point_cloud,
                    cleanup=True,
                    simplify_target=100000,
                    simplify_method="uniform",
                    adaptive_threshold=0.1,
                    fill_holes_size=None,
                    origin_bottom=False,
                    generate_tex=False,
                    uv_method="simple",
                    texture_size=2048
                )
                
                print(f"✓ Generated: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
                
                # Save for future use
                try:
                    if format_type == "glb":
                        import trimesh
                        import numpy as np
                        vertices = np.asarray(mesh.vertices)
                        faces = np.asarray(mesh.triangles)
                        colors = np.asarray(mesh.vertex_colors) if mesh.has_vertex_colors() else None
                        
                        if colors is not None:
                            colors_255 = (colors * 255).astype(np.uint8)
                            tmesh = trimesh.Trimesh(vertices=vertices, faces=faces, vertex_colors=colors_255)
                        else:
                            tmesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                        
                        tmesh.export(str(mesh_path))
                    else:
                        o3d.io.write_triangle_mesh(str(mesh_path), mesh)
                    
                    print(f"✓ Saved to: {mesh_path}")
                except Exception as e:
                    print(f"Warning: Could not save: {e}")
                
                # Compute normals for rendering
                mesh.compute_vertex_normals()
                return mesh
                
            except Exception as e:
                print(f"✗ Failed to generate: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Load existing mesh
        try:
            mesh = o3d.io.read_triangle_mesh(str(mesh_path))
            
            if len(mesh.triangles) == 0:
                print(f"Warning: Mesh has no triangles: {mesh_path}")
                return None
            
            mesh.compute_vertex_normals()
            
            if mesh.has_vertex_colors():
                print(f"Mesh has vertex colors")
            else:
                print(f"Warning: Mesh has no vertex colors")
            
            print(f"Loaded mesh: {mesh_filename} ({len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles)")
            
            # Store original and current mesh
            import copy
            self.original_mesh = mesh
            self.current_mesh = copy.deepcopy(mesh)
            
            # Update dimension display
            self._update_dimension_display()
            
            return mesh
            
        except Exception as e:
            print(f"Error loading mesh: {e}")
            return None

    def _setup_ui(self):
        """Setup the user interface with dual panes and controls."""
        # Create main layout
        self.window.set_on_layout(self._on_layout)
        
        # Create widgets
        self._create_widgets()
        
        # Add widgets to window
        self.window.add_child(self.panel)
        self.window.add_child(self.scene_widget_left)
        self.window.add_child(self.scene_widget_right)

        # Info overlay at bottom of window
        self.info_overlay = gui.Horiz()
        self.info_overlay.add_child(self.method_label)
        self.info_overlay.add_child(gui.Label("  "))
        self.info_overlay.add_child(self.format_label)
        self.info_overlay.add_child(gui.Label("  "))
        self.info_overlay.add_child(self.vertices_label)
        self.info_overlay.add_child(gui.Label("  "))
        self.info_overlay.add_child(self.triangles_label)
        self.window.add_child(self.info_overlay)
        
        # Setup scenes
        self._setup_scenes()
        
        # Load initial mesh
        self._update_mesh()
    
    def _create_widgets(self):
        """Create UI widgets."""
        em = self.window.theme.font_size
        
        # Control panel
        self.panel = gui.Vert(0.5 * em, gui.Margins(0.5 * em))
        
        # Title
        title = gui.Label("Mesh Viewer Controls")
        self.panel.add_child(title)
        
        # Method dropdown
        method_label = gui.Label("Meshing Method:")
        self.panel.add_child(method_label)
        
        self.method_dropdown = gui.Combobox()
        for method in self.methods:
            self.method_dropdown.add_item(method.upper())
        self.method_dropdown.selected_index = 0  # Poisson (creates watertight meshes)
        self.method_dropdown.set_on_selection_changed(self._on_method_changed)
        self.panel.add_child(self.method_dropdown)
        
        self.panel.add_fixed(0.5 * em)
        
        # Format dropdown
        format_label = gui.Label("Export Format:")
        self.panel.add_child(format_label)
        
        self.format_dropdown = gui.Combobox()
        for fmt in self.formats:
            self.format_dropdown.add_item(fmt.upper())
        self.format_dropdown.selected_index = 1  # GLB
        self.format_dropdown.set_on_selection_changed(self._on_format_changed)
        self.panel.add_child(self.format_dropdown)
        
        self.panel.add_fixed(0.5 * em)
        
        # Settings panel for mesh scaling and background color
        self.settings = gui.Vert(0.5 * em, gui.Margins(0.5 * em))
        self.panel.add_child(self.settings)
        
        # Mesh Scaling
        self.settings.add_child(gui.Label("Mesh Scaling"))
        
        scale_layout = gui.Horiz()
        scale_layout.add_child(gui.Label("Scale:"))
        self.scale_input = gui.TextEdit()
        self.scale_input.text_value = "1.0"
        scale_layout.add_child(self.scale_input)
        self.scale_apply_button = gui.Button("Apply")
        self.scale_apply_button.set_on_clicked(self._on_scale_apply)
        scale_layout.add_child(self.scale_apply_button)
        self.settings.add_child(scale_layout)
        
        self.dimension_label = gui.Label("Dimensions: --")
        self.settings.add_child(self.dimension_label)
        
        self.settings.add_fixed(0.5 * em)
        
        # UP Orientation
        self.settings.add_child(gui.Label("UP Orientation"))
        
        up_layout = gui.Horiz()
        up_layout.add_child(gui.Label("UP Axis:"))
        self.up_combo = gui.Combobox()
        self.up_combo.add_item("Y-up")
        self.up_combo.add_item("Z-up")
        self.up_combo.selected_index = 1  # Z-up default
        self.up_combo.set_on_selection_changed(self._on_up_changed)
        up_layout.add_child(self.up_combo)
        self.settings.add_child(up_layout)
        
        self.settings.add_fixed(0.5 * em)
        
        # Remeshing
        self.settings.add_child(gui.Label("Remeshing"))
        
        poly_layout = gui.Horiz()
        poly_layout.add_child(gui.Label("Poly Count:"))
        self.poly_count_input = gui.TextEdit()
        self.poly_count_input.text_value = "100000"
        poly_layout.add_child(self.poly_count_input)
        self.settings.add_child(poly_layout)
        
        method_layout = gui.Horiz()
        method_layout.add_child(gui.Label("Method:"))
        self.simplify_method_combo = gui.Combobox()
        self.simplify_method_combo.add_item("Uniform")
        self.simplify_method_combo.add_item("Adaptive")
        self.simplify_method_combo.selected_index = 0
        method_layout.add_child(self.simplify_method_combo)
        self.settings.add_child(method_layout)
        
        self.remesh_button = gui.Button("Remesh")
        self.remesh_button.set_on_clicked(self._on_remesh_clicked)
        self.settings.add_child(self.remesh_button)
        
        self.settings.add_fixed(0.5 * em)
        
        # View Synchronization
        self.settings.add_child(gui.Label("View Synchronization"))
        
        self.lock_rotation_cb = gui.Checkbox("Lock Rotation")
        self.lock_rotation_cb.checked = True  # Default ON
        self.lock_rotation_cb.set_on_checked(lambda checked: self._on_view_lock_changed('rotation', checked))
        self.settings.add_child(self.lock_rotation_cb)
        
        self.lock_pan_cb = gui.Checkbox("Lock Pan")
        self.lock_pan_cb.checked = True  # Default ON
        self.lock_pan_cb.set_on_checked(lambda checked: self._on_view_lock_changed('pan', checked))
        self.settings.add_child(self.lock_pan_cb)
        
        self.lock_zoom_cb = gui.Checkbox("Lock Zoom")
        self.lock_zoom_cb.checked = True  # Default ON
        self.lock_zoom_cb.set_on_checked(lambda checked: self._on_view_lock_changed('zoom', checked))
        self.settings.add_child(self.lock_zoom_cb)
        
        self.settings.add_fixed(0.5 * em)
        
        # Display Options
        self.settings.add_child(gui.Label("Display"))
        
        self.axes_cb = gui.Checkbox("Show Axes")
        self.axes_cb.checked = True
        self.axes_cb.set_on_checked(self._on_axes_changed)
        self.settings.add_child(self.axes_cb)

        self.bbox_cb = gui.Checkbox("Show Bounding Box")
        self.bbox_cb.set_on_checked(self._on_bbox_changed)
        self.settings.add_child(self.bbox_cb)
        
        self.wireframe_cb = gui.Checkbox("Show Wireframe")
        self.wireframe_cb.set_on_checked(self._on_wireframe_changed)
        self.settings.add_child(self.wireframe_cb)
        
        self.normals_cb = gui.Checkbox("Show Normals")
        self.normals_cb.set_on_checked(self._on_normals_changed)
        self.settings.add_child(self.normals_cb)

        self.invert_normals_cb = gui.Checkbox("Invert Normals")
        self.invert_normals_cb.set_on_checked(self._on_invert_normals_changed)
        self.settings.add_child(self.invert_normals_cb)
        
        # Normal length
        normal_len_layout = gui.Horiz()
        normal_len_layout.add_child(gui.Label("Normal Length:"))
        self.normal_len_input = gui.TextEdit()
        self.normal_len_input.text_value = "0.01"
        normal_len_layout.add_child(self.normal_len_input)
        self.settings.add_child(normal_len_layout)
        
        # Normal color
        normal_color_layout = gui.Horiz()
        normal_color_layout.add_child(gui.Label("Normal Color:"))
        self.normal_color_edit = gui.ColorEdit()
        self.normal_color_edit.color_value = gui.Color(1.0, 0.0, 0.0)  # Red
        normal_color_layout.add_child(self.normal_color_edit)
        self.settings.add_child(normal_color_layout)

        self.rendering_cb = gui.Checkbox("Show Rendering")
        self.rendering_cb.checked = True
        self.rendering_cb.set_on_checked(self._on_rendering_changed)
        self.settings.add_child(self.rendering_cb)

        # Mesh Origin
        origin_layout = gui.Horiz()
        origin_layout.add_child(gui.Label("Mesh Origin:"))
        self.origin_x = gui.TextEdit()
        self.origin_x.text_value = "0.0"
        origin_layout.add_child(self.origin_x)
        self.origin_y = gui.TextEdit()
        self.origin_y.text_value = "0.0"
        origin_layout.add_child(self.origin_y)
        self.origin_z = gui.TextEdit()
        self.origin_z.text_value = "0.0"
        origin_layout.add_child(self.origin_z)
        self.origin_apply = gui.Button("Apply")
        self.origin_apply.set_on_clicked(self._on_origin_apply)
        self.origin_center = gui.Button("Center")
        self.origin_center.set_on_clicked(self._on_origin_center)
        origin_layout.add_child(self.origin_center)
        origin_layout.add_child(self.origin_apply)
        self.settings.add_child(origin_layout)
        
        self.settings.add_fixed(0.5 * em)
        
        # Background color picker
        self.settings.add_child(gui.Label("Background Color"))
        self.bg_color_combo = gui.Combobox()
        
        self.bg_colors = {
            "Ice": [0.94, 0.97, 0.98, 1.0],
            "White": [1.0, 1.0, 1.0, 1.0],
            "Light Gray": [0.9, 0.9, 0.9, 1.0],
            "Dark Gray": [0.2, 0.2, 0.2, 1.0],
            "Black": [0.0, 0.0, 0.0, 1.0]
        }
        
        self.bg_dropdown = gui.Combobox()
        for color_name in self.bg_colors.keys():
            self.bg_dropdown.add_item(color_name)
        self.bg_dropdown.selected_index = 3
        self.bg_dropdown.set_on_selection_changed(self._on_bg_color_changed)
        self.panel.add_child(self.bg_dropdown)
        
        self.panel.add_fixed(0.5 * em)
        
        # Info labels
        # Info display (single row at bottom)
        info_layout = gui.Horiz()
        self.method_label = gui.Label("Method: --")
        info_layout.add_child(self.method_label)
        info_layout.add_child(gui.Label("  "))
        self.format_label = gui.Label("Format: --")
        info_layout.add_child(self.format_label)
        info_layout.add_child(gui.Label("  "))
        self.vertices_label = gui.Label("Vertices: --")
        info_layout.add_child(self.vertices_label)
        info_layout.add_child(gui.Label("  "))
        self.triangles_label = gui.Label("Triangles: --")
        info_layout.add_child(self.triangles_label)
        # self.panel.add_child(info_layout)

        # Export Mesh button
        self.export_button = gui.Button("Export Mesh")
        self.export_button.enabled = False
        self.export_button.set_on_clicked(self._on_export_mesh)
        self.panel.add_child(self.export_button)
        
        # Scene widgets (3D viewers)
        self.scene_widget_left = gui.SceneWidget()
        self.scene_widget_left.scene = rendering.Open3DScene(self.window.renderer)
        
        self.scene_widget_right = gui.SceneWidget()
        self.scene_widget_right.scene = rendering.Open3DScene(self.window.renderer)
    
    def _on_layout(self, layout_context):
        """Handle window layout."""
        r = self.window.content_rect
        panel_width = 600  # Increased from 250 (60% wider)
        
        # Panel on the left
        self.panel.frame = gui.Rect(r.x, r.y, panel_width, r.height)
        
        # Calculate remaining width for scenes
        scene_x = r.x + panel_width
        scene_width = (r.width - panel_width) // 2
        
        # Left scene (point cloud)
        self.scene_widget_left.frame = gui.Rect(scene_x, r.y, scene_width, r.height)
        
        # Right scene (mesh)
        self.scene_widget_right.frame = gui.Rect(scene_x + scene_width, r.y, scene_width, r.height)

        # Info overlay at bottom
        info_height = 30
        self.info_overlay.frame = gui.Rect(r.width - 600, r.height - info_height, 600, info_height)
    
    def _setup_scenes(self):
        """Setup the 3D scenes for point cloud and mesh."""
        # Set initial background color to Ice
        ice_color = [0.94, 0.97, 0.98, 1.0]
        self.scene_widget_left.scene.set_background(ice_color)
        self.scene_widget_right.scene.set_background(ice_color)
        
        # Setup left scene (point cloud)
        self.scene_widget_left.scene.add_geometry("point_cloud", self.point_cloud, 
                                                   rendering.MaterialRecord())
        
        # Setup camera for left scene
        bounds = self.point_cloud.get_axis_aligned_bounding_box()
        self.scene_widget_left.setup_camera(60, bounds, bounds.get_center())
        
        # Add mouse event handlers for view synchronization
        self.scene_widget_left.set_on_mouse(self._on_mouse_left)
        self.scene_widget_right.set_on_mouse(self._on_mouse_right)
        
        # Add label for left scene
        self.scene_widget_left.scene.show_axes(True)
        
        # Setup right scene (will be populated with mesh)
        self.scene_widget_right.scene.show_axes(True)
    
    def _update_mesh(self):
        """Update the mesh display based on current selections."""
        # Load new mesh
        mesh = self._load_mesh(self.current_method, self.current_format)
        
        if mesh is None:
            self.info_label.text = f"⚠ Mesh not found: {self.current_method}.{self.current_format}"
            # Clear right scene
            self.scene_widget_right.scene.clear_geometry()
            return
        
        self.current_mesh = mesh
        
        # Update info
        self.method_label.text = f"Method: {self.current_method.upper()}"
        self.format_label.text = f"Format: {self.current_format.upper()}"
        self.vertices_label.text = f"Vertices: {len(mesh.vertices):,}"
        self.triangles_label.text = f"Triangles: {len(mesh.triangles):,}"
        
        # Clear and update right scene
        self.scene_widget_right.scene.clear_geometry()
        self.scene_widget_right.scene.add_geometry("mesh", mesh, rendering.MaterialRecord())
        
        # Setup camera for right scene
        bounds = mesh.get_axis_aligned_bounding_box()
        # self.scene_widget_right.setup_camera(60, bounds, self.point_cloud.get_axis_aligned_bounding_box().get_center())
        # Camera already set up in __init__, no need to re-center
    
    def _on_method_changed(self, new_value, new_index):
        """Handle meshing method selection change."""
        self.current_method = self.methods[new_index]
        print(f"Method changed to: {self.current_method}")
        self._update_mesh()
    
    def _on_format_changed(self, new_value, new_index):
        """Handle format selection change."""
        self.current_format = self.formats[new_index]
        print(f"Format changed to: {self.current_format}")
        self._update_mesh()
    
    
    def _on_scale_apply(self):
        """Apply scale to mesh."""
        try:
            value = float(self.scale_input.text_value)
            if value <= 0:
                print("Scale must be positive")
                return
            
            self.scale_factor = value
            
            if self.original_mesh is not None:
                import copy
                self.current_mesh = copy.deepcopy(self.original_mesh)
                self.current_mesh.scale(value, center=self.current_mesh.get_center())
                
                self.scene_widget_right.scene.clear_geometry()
                mat = rendering.MaterialRecord()
                mat.shader = "defaultLit"
                self.scene_widget_right.scene.add_geometry("mesh", self.current_mesh, mat)
                
                self._update_dimension_display()
                self.mesh_modified = True
                self.export_button.enabled = True
                print(f"✓ Scaled to {value}x")
        except ValueError:
            print("Invalid scale value")
    
    def _on_up_changed(self, new_val, new_idx):
        """Handle UP orientation change."""
        self.up_direction = "Y" if new_idx == 0 else "Z"
        print(f"UP orientation: {self.up_direction}-up")
        
        # Reconfigure cameras with new up vector
        # Note: Open3D's camera doesn't have set_up_vector, 
        # so we need to reset the camera with the new up direction
        # This is a limitation of the current Open3D API
        
        # For now, just log the change
        # Full implementation would require recreating the scene
        print(f"  (Camera up vector change requires scene reset - not implemented)")
    
    def _update_dimension_display(self):
        """Update dimension label with current mesh bounds."""
        if self.current_mesh is not None:
            bounds = self.current_mesh.get_axis_aligned_bounding_box()
            extent = bounds.get_extent()
            self.dimension_label.text = f"Dimensions: {extent[0]:.3f} × {extent[1]:.3f} × {extent[2]:.3f}"
        else:
            self.dimension_label.text = "Dimensions: --"
    
    def _on_remesh_clicked(self):
        """Handle remesh button click."""
        if self.current_mesh is None:
            print("No mesh loaded to remesh")
            return
        
        try:
            # Get parameters
            target_count = int(self.poly_count_input.text_value)
            method = self.simplify_method_combo.selected_text.lower()
            
            print(f"Remeshing to {target_count} triangles using {method} method...")
            
            # Import mesher functions
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from mesher import post_process_mesh
            
            # Remesh (use original mesh as base)
            mesh_to_process = self.original_mesh if self.original_mesh else self.current_mesh
            
            mesh, _ = post_process_mesh(
                mesh_to_process,
                pcd=self.point_cloud,
                cleanup=True,
                simplify_target=target_count,
                simplify_method=method,
                adaptive_threshold=0.1,
                fill_holes_size=None,
                origin_bottom=False,
                generate_tex=False,
                uv_method="simple",
                texture_size=2048
            )
            
            # Update meshes
            self.original_mesh = mesh
            import copy
            self.current_mesh = copy.deepcopy(mesh)
            
            # Apply current scale
            if self.scale_factor != 1.0:
                self.current_mesh.scale(self.scale_factor, center=self.current_mesh.get_center())
            
            # Update display
            self.scene_widget_right.scene.clear_geometry()
            mat = rendering.MaterialRecord()
            mat.shader = "defaultLit"
            self.scene_widget_right.scene.add_geometry("mesh", self.current_mesh, mat)
            
            # Update info
            self.method_label.text = f"Method: {self.current_method.upper()}"
            self.format_label.text = f"Format: {self.current_format.upper()}"
            self.vertices_label.text = f"Vertices: {len(mesh.vertices):,}"
            
            # Update dimensions
            self._update_dimension_display()
            
            print(f"✓ Remeshed: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
            self.mesh_modified = True
            self.export_button.enabled = True
            
        except Exception as e:
            print(f"✗ Remeshing failed: {e}")
            import traceback
            traceback.print_exc()
    
    
    def _on_view_lock_changed(self, lock_type, checked):
        """Handle view lock checkbox changes."""
        self.view_locks[lock_type] = checked
        status = 'ON' if checked else 'OFF'
        print(f"View lock {lock_type}: {status}")
    
    def _on_mouse_left(self, event):
        """Handle mouse events on left panel (point cloud)."""
        # Sync camera to right panel if any locks are enabled
        if any(self.view_locks.values()):
            self._sync_camera_left_to_right()
        return gui.Widget.EventCallbackResult.HANDLED
    
    def _on_mouse_right(self, event):
        """Handle mouse events on right panel (mesh)."""
        # Sync camera to left panel if any locks are enabled
        if any(self.view_locks.values()):
            self._sync_camera_right_to_left()
        return gui.Widget.EventCallbackResult.HANDLED
    
    def _sync_camera_left_to_right(self):
        """Synchronize camera from left (point cloud) to right (mesh)."""
        try:
            # Get camera from left scene
            left_camera = self.scene_widget_left.scene.camera
            right_camera = self.scene_widget_right.scene.camera
            
            # Sync based on lock settings
            if self.view_locks['rotation'] or self.view_locks['pan']:
                # Copy view matrix (handles both rotation and pan)
                right_camera.copy_from(left_camera)
            
            if self.view_locks['zoom']:
                # Match field of view
                right_camera.set_projection(
                    left_camera.get_field_of_view(),
                    right_camera.get_aspect_ratio(),
                    right_camera.get_near(),
                    right_camera.get_far(),
                    left_camera.get_field_of_view_type()
                )
        except Exception as e:
            # Silently handle errors (camera API may vary)
            pass
    
    def _sync_camera_right_to_left(self):
        """Synchronize camera from right (mesh) to left (point cloud)."""
        try:
            # Get camera from right scene
            left_camera = self.scene_widget_left.scene.camera
            right_camera = self.scene_widget_right.scene.camera
            
            # Sync based on lock settings
            if self.view_locks['rotation'] or self.view_locks['pan']:
                # Copy view matrix (handles both rotation and pan)
                left_camera.copy_from(right_camera)
            
            if self.view_locks['zoom']:
                # Match field of view
                left_camera.set_projection(
                    right_camera.get_field_of_view(),
                    left_camera.get_aspect_ratio(),
                    left_camera.get_near(),
                    left_camera.get_far(),
                    right_camera.get_field_of_view_type()
                )
        except Exception as e:
            # Silently handle errors (camera API may vary)
            pass
    
    def _on_bbox_changed(self, checked):
        """Toggle bounding box display."""
        self.show_bbox = checked
        
        if checked:
            # Add bounding boxes
            pcd_bbox = self.point_cloud.get_axis_aligned_bounding_box()
            pcd_bbox.color = (0, 0, 1)  # Green
            self.scene_widget_left.scene.add_geometry("pcd_bbox", pcd_bbox, rendering.MaterialRecord())
            
            if self.current_mesh:
                mesh_bbox = self.current_mesh.get_axis_aligned_bounding_box()
                mesh_bbox.color = (0, 0, 1)  # Green
                self.scene_widget_right.scene.add_geometry("mesh_bbox", mesh_bbox, rendering.MaterialRecord())
        else:
            # Remove bounding boxes
            try:
                self.scene_widget_left.scene.remove_geometry("pcd_bbox")
            except:
                pass
            try:
                self.scene_widget_right.scene.remove_geometry("mesh_bbox")
            except:
                pass
        
        print(f"Bounding box: {'ON' if checked else 'OFF'}")
    
    def _on_wireframe_changed(self, checked):
        """Toggle wireframe display."""
        self.show_wireframe = checked
        
        if self.current_mesh:
            try:
                self.scene_widget_right.scene.remove_geometry("mesh")
            except:
                pass
            mat = rendering.MaterialRecord()
            mat.shader = "defaultLit"
            if checked:
                mat.line_width = 1.0
                # Create wireframe by adding edges
                import numpy as np
                edges = []
                triangles = np.asarray(self.current_mesh.triangles)
                for tri in triangles:
                    edges.append([tri[0], tri[1]])
                    edges.append([tri[1], tri[2]])
                    edges.append([tri[2], tri[0]])
                
                line_set = o3d.geometry.LineSet()
                line_set.points = self.current_mesh.vertices
                line_set.lines = o3d.utility.Vector2iVector(edges)
                line_set.colors = o3d.utility.Vector3dVector([[0, 0, 0]] * len(edges))  # Black
                self.scene_widget_right.scene.add_geometry("wireframe", line_set, rendering.MaterialRecord())
            else:
                try:
                    self.scene_widget_right.scene.remove_geometry("wireframe")
                except:
                    pass
            
            self.scene_widget_right.scene.add_geometry("mesh", self.current_mesh, mat)
        
        print(f"Wireframe: {'ON' if checked else 'OFF'}")
    
    def _on_normals_changed(self, checked):
        """Toggle normals display."""
        self.show_normals = checked
        
        try:
            normal_length = float(self.normal_len_input.text_value)
            color = self.normal_color_edit.color_value
            normal_color = [color.red, color.green, color.blue]
        except:
            normal_length = 0.01
            normal_color = [1.0, 0.0, 0.0]
        
        if checked:
            # Add normals for point cloud
            import numpy as np
            pcd_points = np.asarray(self.point_cloud.points)
            pcd_normals = np.asarray(self.point_cloud.normals)
            
            pcd_lines = []
            pcd_line_points = []
            for i, (pt, normal) in enumerate(zip(pcd_points, pcd_normals)):
                pcd_line_points.append(pt)
                pcd_line_points.append(pt + normal * normal_length)
                pcd_lines.append([len(pcd_line_points)-2, len(pcd_line_points)-1])
            
            pcd_line_set = o3d.geometry.LineSet()
            pcd_line_set.points = o3d.utility.Vector3dVector(pcd_line_points)
            pcd_line_set.lines = o3d.utility.Vector2iVector(pcd_lines)
            pcd_line_set.colors = o3d.utility.Vector3dVector([normal_color] * len(pcd_lines))
            self.scene_widget_left.scene.add_geometry("pcd_normals", pcd_line_set, rendering.MaterialRecord())
            
            # Add normals for mesh
            if self.current_mesh and self.current_mesh.has_vertex_normals():
                mesh_points = np.asarray(self.current_mesh.vertices)
                mesh_normals = np.asarray(self.current_mesh.vertex_normals)
                
                mesh_lines = []
                mesh_line_points = []
                for i, (pt, normal) in enumerate(zip(mesh_points, mesh_normals)):
                    mesh_line_points.append(pt)
                    mesh_line_points.append(pt + normal * normal_length)
                    mesh_lines.append([len(mesh_line_points)-2, len(mesh_line_points)-1])
                
                mesh_line_set = o3d.geometry.LineSet()
                mesh_line_set.points = o3d.utility.Vector3dVector(mesh_line_points)
                mesh_line_set.lines = o3d.utility.Vector2iVector(mesh_lines)
                mesh_line_set.colors = o3d.utility.Vector3dVector([normal_color] * len(mesh_lines))
                self.scene_widget_right.scene.add_geometry("mesh_normals", mesh_line_set, rendering.MaterialRecord())
        else:
            # Remove normals
            try:
                self.scene_widget_left.scene.remove_geometry("pcd_normals")
            except:
                pass
            try:
                self.scene_widget_right.scene.remove_geometry("mesh_normals")
            except:
                pass
        
        print(f"Normals: {'ON' if checked else 'OFF'}")
    
    def _on_bbox_changed(self, checked):
        """Toggle bounding box display."""
        self.show_bbox = checked

        if checked:
            pcd_bbox = self.point_cloud.get_axis_aligned_bounding_box()
            pcd_bbox.color = (0, 0, 1)
            self.scene_widget_left.scene.add_geometry("pcd_bbox", pcd_bbox, rendering.MaterialRecord())

            if self.current_mesh:
                mesh_bbox = self.current_mesh.get_axis_aligned_bounding_box()
                mesh_bbox.color = (0, 0, 1)
                self.scene_widget_right.scene.add_geometry("mesh_bbox", mesh_bbox, rendering.MaterialRecord())
        else:
            try:
                self.scene_widget_left.scene.remove_geometry("pcd_bbox")
            except:
                pass
            try:
                self.scene_widget_right.scene.remove_geometry("mesh_bbox")
            except:
                pass

        print(f"Bounding box: {'ON' if checked else 'OFF'}")

    def _on_wireframe_changed(self, checked):
        """Toggle wireframe display."""
        self.show_wireframe = checked

        if self.current_mesh:
            try:
                self.scene_widget_right.scene.remove_geometry("wireframe")
            except:
                pass
            if checked:
                import numpy as np
                edges = []
                triangles = np.asarray(self.current_mesh.triangles)
                for tri in triangles:
                    edges.append([tri[0], tri[1]])
                    edges.append([tri[1], tri[2]])
                    edges.append([tri[2], tri[0]])

                line_set = o3d.geometry.LineSet()
                line_set.points = self.current_mesh.vertices
                line_set.lines = o3d.utility.Vector2iVector(edges)
                line_set.colors = o3d.utility.Vector3dVector([[0, 0, 0]] * len(edges))
                self.scene_widget_right.scene.add_geometry("wireframe", line_set, rendering.MaterialRecord())

        print(f"Wireframe: {'ON' if checked else 'OFF'}")

    def _on_normals_changed(self, checked):
        """Toggle normals display."""
        self.show_normals = checked

        try:
            normal_length = float(self.normal_len_input.text_value)
            color = self.normal_color_edit.color_value
            normal_color = [color.red, color.green, color.blue]
        except:
            normal_length = 0.01
            normal_color = [1.0, 0.0, 0.0]

        if checked:
            import numpy as np
            pcd_points = np.asarray(self.point_cloud.points)
            pcd_normals = np.asarray(self.point_cloud.normals)

            pcd_lines = []
            pcd_line_points = []
            for pt, normal in zip(pcd_points, pcd_normals):
                pcd_line_points.append(pt)
                pcd_line_points.append(pt + normal * normal_length)
                pcd_lines.append([len(pcd_line_points)-2, len(pcd_line_points)-1])

            pcd_line_set = o3d.geometry.LineSet()
            pcd_line_set.points = o3d.utility.Vector3dVector(pcd_line_points)
            pcd_line_set.lines = o3d.utility.Vector2iVector(pcd_lines)
            pcd_line_set.colors = o3d.utility.Vector3dVector([normal_color] * len(pcd_lines))
            self.scene_widget_left.scene.add_geometry("pcd_normals", pcd_line_set, rendering.MaterialRecord())

            if self.current_mesh and self.current_mesh.has_vertex_normals():
                mesh_points = np.asarray(self.current_mesh.vertices)
                mesh_normals = np.asarray(self.current_mesh.vertex_normals)

                mesh_lines = []
                mesh_line_points = []
                for pt, normal in zip(mesh_points, mesh_normals):
                    mesh_line_points.append(pt)
                    mesh_line_points.append(pt + normal * normal_length)
                    mesh_lines.append([len(mesh_line_points)-2, len(mesh_line_points)-1])

                mesh_line_set = o3d.geometry.LineSet()
                mesh_line_set.points = o3d.utility.Vector3dVector(mesh_line_points)
                mesh_line_set.lines = o3d.utility.Vector2iVector(mesh_lines)
                mesh_line_set.colors = o3d.utility.Vector3dVector([normal_color] * len(mesh_lines))
                self.scene_widget_right.scene.add_geometry("mesh_normals", mesh_line_set, rendering.MaterialRecord())
        else:
            try:
                self.scene_widget_left.scene.remove_geometry("pcd_normals")
            except:
                pass
            try:
                self.scene_widget_right.scene.remove_geometry("mesh_normals")
            except:
                pass

        print(f"Normals: {'ON' if checked else 'OFF'}")



    def _on_rendering_changed(self, checked):
        """Toggle mesh rendering (solid vs transparent)."""
        self.show_rendering = checked
        if self.current_mesh:
            try:
                self.scene_widget_right.scene.remove_geometry("mesh")
            except:
                pass
            mat = rendering.MaterialRecord()
            mat.shader = "defaultLit" if checked else "defaultUnlit"
            if not checked:
                mat.base_color = [1.0, 1.0, 1.0, 0.3]
            self.scene_widget_right.scene.add_geometry("mesh", self.current_mesh, mat)
        print(f"Rendering: {'ON' if checked else 'OFF'}")


    def _on_origin_center(self):
        """Set origin to center (0, 0, 0)."""
        self.origin_x.text_value = "0.0"
        self.origin_y.text_value = "0.0"
        self.origin_z.text_value = "0.0"
        print("Origin set to center: [0, 0, 0]")

    def _on_origin_apply(self):
        """Apply mesh origin offset."""
        if self.current_mesh:
            try:
                x = float(self.origin_x.text_value)
                y = float(self.origin_y.text_value)
                z = float(self.origin_z.text_value)
                bounds = self.current_mesh.get_axis_aligned_bounding_box()
                min_bound = bounds.get_min_bound()
                offset = [x - min_bound[0], y - min_bound[1], z - min_bound[2]]
                self.current_mesh.translate(offset)
            except:
                pass
            mat = rendering.MaterialRecord()
            mat.shader = "defaultLit"
            self.scene_widget_right.scene.add_geometry("mesh", self.current_mesh, mat)
            self._update_dimension_display()
            print(f"✓ Reset origin: offset = {offset}")

    def _on_invert_normals_changed(self, checked):
        """Toggle normal inversion."""
        self.invert_normals = checked
        if self.show_normals:
            self._on_normals_changed(False)
            self._on_normals_changed(True)
        print(f"Invert normals: {'ON' if checked else 'OFF'}")



    def _on_export_mesh(self):
        """Export modified mesh."""
        if self.current_mesh:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            filename = filedialog.asksaveasfilename(
                defaultextension=".glb",
                filetypes=[("GLB files", "*.glb"), ("OBJ files", "*.obj"), ("STL files", "*.stl")]
            )
            if filename:
                import open3d as o3d
                o3d.io.write_triangle_mesh(filename, self.current_mesh)
                print(f"✓ Exported mesh to {filename}")

    def _on_axes_changed(self, checked):
        """Toggle axes display."""
        self.show_axes = checked
        self.scene_widget_left.scene.show_axes(checked)
        self.scene_widget_right.scene.show_axes(checked)
        print(f"Axes: {'ON' if checked else 'OFF'}")

    def _on_bg_color_changed(self, new_value, new_index):
        """Handle background color selection change."""
        color_name = list(self.bg_colors.keys())[new_index]
        color = self.bg_colors[color_name]
        print(f"Background color changed to: {color_name}")
        self.scene_widget_left.scene.set_background(color)
        self.scene_widget_right.scene.set_background(color)
    
    def run(self):
        """Run the application."""
        self.app.run()


def main():
    """Main function."""
    # Get script directory to compute default paths
    script_dir = Path(__file__).parent
    default_input = script_dir.parent / "pclouds" / "chiller_rgb.ply"
    default_mesh_dir = script_dir.parent / "meshes"
    
    parser = argparse.ArgumentParser(
        description="Interactive dual-pane mesh viewer for point clouds and meshes"
    )
    
    parser.add_argument(
        "--input_file",
        type=str,
        default=str(default_input),
        help="Path to input PLY point cloud file"
    )
    
    parser.add_argument(
        "--mesh_dir",
        type=str,
        default=str(default_mesh_dir),
        help="Directory containing generated mesh files"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input_file).exists():
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Create and run viewer
    viewer = DualPaneMeshViewer(args.input_file, args.mesh_dir)
    viewer.run()


if __name__ == "__main__":
    main()
