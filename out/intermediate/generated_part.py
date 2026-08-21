from build123d import (
    Box, BuildPart, BuildSketch, Circle, Cylinder, Hole, Locations, Mode,
    Plane, Pos, Rectangle, extrude, export_stl,
)
from ocp_vscode import show

# A solid box
with BuildPart() as part:
    Box(10.0, 10.0, 10.0)

# Visualize
show(part.part, reset_camera=False, axes=True, grid=True)

# Export
export_stl(part.part, "generated_part.stl")