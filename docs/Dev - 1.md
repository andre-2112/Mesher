# OBJ
./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_poisson.obj \
--output_format obj \
--meshing_method poisson

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_bpa.obj \
--output_format obj \
--meshing_method bpa 

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_alpha.obj \
--output_format obj \
--meshing_method alpha

# GLB
./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_poisson.glb \
--output_format glb \
--meshing_method poisson

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_bpa.glb \
--output_format glb \
--meshing_method bpa 

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_alpha.glb \
--output_format glb \
--meshing_method alpha

# STL
./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_poisson.stl \
--output_format stl \
--meshing_method poisson

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_bpa.stl \
--output_format stl \
--meshing_method bpa 

./scripts/mesher.py --input_file ./pclouds/chiller.ply \
--output_filename ./meshes/chiller_alpha.stl \
--output_format stl \
--meshing_method alpha