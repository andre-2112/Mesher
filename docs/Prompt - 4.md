##
Add the following enhancements to the viewer:

1 - Scaling.

- Create and add UI and the functionality for the scaling of the generated mesh size on any axis, but with locked aspect ratio. Included in the UI is the display of the dimensions and the scale factor. 

2 - Extending the already existing feature to mesh on-demand, implement remeshing.

- Create and add UI and the functionality for the remeshing, with the option to define the poly count.

- Create and add UI and the functionality for the remeshing through simplification, and the option to define the simplification method.

3 - Lock Rotation.

- Create and add UI and the functionality for Locking/syncronize the display panels (point cold and mesh), with check box optioons for locking the orientation, rotation, panning and zooming of the point cloud and the mesh.

##
Go ahead and implement the view syncronization.

But first, Make the side drawer wider. At least 60% wider then the current width. 

##
- The viewr crashes when i try to move the scale slider. remove the slider. lets have only fields for entering absolute values. 

- Create and add UI and the functionality for the UP orientation. Z up should be the default.

- Can you execute the viewr and test UI to make sure all work?

##
- Set synchronization to be default on all options.
- Create and add UI and the functionality for displaying a bounding box around the point cloud and the mesh.
- Create and add UI and the functionality for displaying the mesh wireframe.
- Create and add UI and the functionality for displaying the normals (for point cloud and mesh), as small thin lines - being able to choose the lenght of the arrows and the color (hopefully via a small bucket icon that triggers a color widget - are the any good libraries for this? if you add a new library for this, add it to the requirements document.
- Make the 3 options above, part of the Display section.

##
- Display wireframe in thicker line. maybe 4x.
- Add "Rendering" as a display option. if unselected and mesh selected then display would only show the see through mesh. if selected (with wireframe deselected)then display would show the mesh with the default rendering options.
- Start mesh with origin same as pc and provide a button to apply default mesh origin (which is lower left).
- Increase side panel to 600px.

##
1 - in the optional enhanecements you mentioned #1 - add mesh repair algorithms for better watertight results. 

2 - what algorithms? what are the expected efficiency of each and difficulty to implement? 

3 - lastly, are there any modern ML models from google gemini or meta sam3d, that could be used for this purpose?

##


