Write me an open3d script (mesher.py)that takes a ply point cloud file as input,  generates a mesh from it, and exports it according to the details below.

Provide the following arguments to the script:

--input-path <path to ply file>
--output-path <path to output ply file>
--output_format [obj|glb|stl]

Provide an additional argument to the script:

--meshing-method [poisson|bpa|alpha]

Where:

poisson: Use Poisson surface reconstruction
bpw: Use Ball Pivoting algorithm
alpha: Use Alpha shapes 

Place the script and any artifacts generated, in the workspace directory.   

--
Add an --help argument describing each argument. for the meshing-method, use the followinug descriptions: 

poisson - Poisson Surface Reconstruction: Best for smooth, watertight meshes. It solves a global optimization problem and is highly effective at handling noisy data. It usually produces the most "professional" looking results.

bpa - Ball Pivoting Algorithm (BPA): Best for preserving the exact positions of the original points. It "rolls" a virtual ball over the cloud to connect points into triangles.

alpha - Alpha Shapes: A more geometric approach that creates a "shrink-wrapped" boundary around the points.

Make Poisson be the default meshing method. 