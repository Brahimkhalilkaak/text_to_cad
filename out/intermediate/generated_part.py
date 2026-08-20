from build123d import Box, BuildPart, export_stl
from ocp_vscode import show

with BuildPart() as part:
    Box(10.0, 10.0, 10.0)

show(part.part, reset_camera=False, axes=True, grid=True)
export_stl(part.part, "generated_part.stl")