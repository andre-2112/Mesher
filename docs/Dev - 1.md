# OBJ
./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_poisson.obj \
--output_format obj \
--meshing-method poisson

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_bpa.obj \
--output_format obj \
--meshing-method bpa 

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_alpha.obj \
--output_format obj \
--meshing-method alpha

# GLB
./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_poisson.glb \
--output_format glb \
--meshing-method poisson

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_bpa.glb \
--output_format glb \
--meshing-method bpa 

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_alpha.glb \
--output_format glb \
--meshing-method alpha

# STL
./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_poisson.stl \
--output_format stl \
--meshing-method poisson

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_bpa.stl \
--output_format stl \
--meshing-method bpa 

./scripts/mesher.py --input-path ./pclouds/chiller.ply \
--output-path ./meshes/chiller_alpha.stl \
--output_format stl \
--meshing-method alpha