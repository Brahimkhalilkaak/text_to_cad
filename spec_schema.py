"""Data schema for multi agent cad system.

This module defines the Pydantic BaseModel and TypedDict based langGraph state 
for the multi-agent CAD system.

"""


from pydantic import BaseModel, Field
from typing import Dict, Any, Literal , TypedDict
from enum import Enum

class CadBrief(BaseModel):
    """Top-level, extensible CAD specification document."""

    spec_version: str = Field(
        default="1.0", description="Monotonic version of this brief (incremented on each Architect-route revision)."
    )

    part_name: str = Field(
        description="Canonical part name (e.g. 'L-bracket-50x40x4-M4')."
    )

    unit: Literal["mm","cm" ,"m" , "in"] = Field(
        "mm",description = "All linear dimension in the cad spec use this unit"
    )

    origin_convention : str = Field(default = "centroid_on_base_plane" , description=
                                    "How the global origin should be placed.  Common conventions: "
                                    "'centroid_on_base_plane' (origin at XY centre of the bottom face, "
                                    "Z=0 on the bottom), 'corner_min' (origin at minimum X/Y/Z corner), "
                                    "'centroid_3d' (origin at the volumetric centroid)."
    )
    
    primary_workplane: Literal["XY" , "YZ" , "YZ"] = Field(
        "XY" , description="The principal sketch plane for the base feature"
    )

    # -- Material --
    material: str = Field(
        default="PLA", description="Intended material for the part"
    )

    # -- Bounding Box --
    max_extent_x_mm: float | None = Field(
        None,
        description="Maximum allowed bounding-box width (X).  None = unbounded.",
    )
    max_extent_y_mm: float | None = Field(
        None,
        description="Maximum allowed bounding-box depth (Y).  None = unbounded.",
    )
    max_extent_z_mm: float | None = Field(
        None,
        description="Maximum allowed bounding-box height (Z).  None = unbounded.",
    )
    target_volume_mm3: float | None = Field(
        None,
        description="Target part volume (informational, not a hard constraint).",
    )

    # -- Key parameters --
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key parameters extracted from user input, e.g. {'length': 50, 'width': 40, 'height': 4, 'hole_diameter': 4 , 'thickness': 2}.",
    )

    # -- Metadata --
    user_request_raw: str = Field(
        ...,
        description="The original user request text, preserved for traceability.",
    )



class Sketch(BaseModel):
    """2D sketch definition for the Geometric Architect."""

    sketch_id: str = Field(
        ...,
        description="Unique sketch identifier , within a plan",
        examples=["base-profile", "side-flange", "mounting-tab"],
    )

    workplane: Literal["XY", "XZ", "YZ"] | str = Field(
        "XY",
        description=(
            "Build plane for the sketch.  Standard planes 'XY', 'XZ', 'YZ', "
            "or a reference to a previously defined face / offset plane "
            "(e.g. 'face:F3', 'offset:base-profile+5mm')."
        ),
    )

    workplane_offset_mm: float = Field(
        0.0,
        description="Offset distance from the nominal workplane (mm).",
    )

    fully_constrained: bool = Field(
        False,
        description="Whether the sketch is fully constrained (recommended for production).",
    )

    notes: str | None = Field(
        None,
        description="Additional guidance for the Coder (e.g. 'use SlotCenterLine').",
    )

class ModelingStepType(str, Enum):
    """Well-known operation types that map to build123d API calls."""

    SKETCH_2D = "sketch_2d"
    """Define a 2D profile on a workplane (points, lines, arcs, splines)."""

    EXTRUDE = "extrude"
    """Linear extrusion of a sketch (additive or cut)."""

    REVOLVE = "revolve"
    """Revolve a sketch around an axis (additive or cut)."""

    FILLET = "fillet"
    """Round a selected edge or edge chain."""

    CHAMFER = "chamfer"
    """Bevel a selected edge or edge chain."""

    HOLE = "hole"
    """Drill / counterbore / countersink a cylindrical hole at a point."""

    SIMPLE_HOLE = "simple_hole"
    """Simple through hole (alias for hole)."""

    COUNTERBORE_HOLE = "counterbore_hole"
    """Counterbore hole (alias for hole with counterbore type)."""

    EXTRUDE_CUT = "extrude_cut"
    """Extrude a sketch as a subtractive cut."""

    CUT = "cut"
    """Generic subtractive operation (alias for boolean_cut)."""

    BOOLEAN_UNION = "boolean_union"
    """Fuse two or more bodies into one."""

    BOOLEAN_CUT = "boolean_cut"
    """Subtract one body (the tool) from another (the target)."""

    BOOLEAN_INTERSECT = "boolean_intersect"
    """Keep only the volume common to two bodies."""

    PATTERN_LINEAR = "pattern_linear"
    """Repeat a feature along a linear direction."""

    PATTERN_CIRCULAR = "pattern_circular"
    """Repeat a feature around an axis."""

    MIRROR = "mirror"
    """Mirror geometry across a plane."""

    SHELL = "shell"
    """Hollow out a solid to a specified wall thickness."""

    DRAFT = "draft"
    """Apply a draft angle to selected faces."""

    RIB = "rib"
    """Add a reinforcing rib / gusset between two faces."""

    REFERENCE = "reference"
    """Define a reference plane, axis, or point for downstream steps."""


class ModelingStep(BaseModel):
    """Single modeling step in the Geometric Architect's plan."""

    step_id: str = Field(
        ...,
        description="Unique identifier within the plan (e.g. 'step-01-extrude-base').",
        examples=["step-01-base-sketch", "step-02-extrude-base", "step-05-fillet-edges"],
    )

    step_type: ModelingStepType = Field(
        ...,
        description="The build123d operation to perform.",
    )

    label: str = Field(
        ...,
        description="Short human-readable label shown in logs / reports.",
        examples=["Extrude base plate 4mm", "Fillet all vertical edges R2"],
    )

    sketch_id: str | None = Field(
        None,
        description="Reference to a Sketch.sketch_id, if this step uses a sketch.",
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operation-specific parameters (e.g. {'distance': 10, 'direction': 'Z+','radius': 2}).",
    )

    # -- Operation parameters --
    distance_mm: float | None = Field(
        None,
        description="Extrusion distance / cut depth (mm).",
    )
    direction: Literal["positive", "negative", "symmetric", "midplane", "both"] | None = Field(
        None,
        description="Extrusion direction relative to the sketch normal.",
    )
    taper_angle_deg: float | None = Field(
        None,
        description="Draft / taper angle for extrusion (degrees, 0 = vertical walls).",
    )

    # -- Revolve parameters --
    revolve_angle_deg: float | None = Field(
        None,
        description="Revolution angle (360 = full revolution).",
    )
    revolve_axis: Literal["x", "y", "z"] | None = Field(
        None,
        description="Axis of revolution.",
    )
    revolve_axis_point: Point3D | None = Field(
        None,
        description="Point the revolution axis passes through.",
    )

    # -- Fillet / Chamfer parameters --
    radius_mm: float | None = Field(
        None,
        description="Fillet radius (mm).",
    )
    chamfer_distance_mm: float | None = Field(
        None,
        description="Chamfer distance (mm, equal-leg).",
    )
    chamfer_distance1_mm: float | None = Field(
        None,
        description="Chamfer distance 1 (mm, unequal-leg).",
    )
    chamfer_distance2_mm: float | None = Field(
        None,
        description="Chamfer distance 2 (mm, unequal-leg).",
    )
    edge_selector: str | None = Field(
        None,
        description=(
            "Which edge(s) to fillet/chamfer.  Either a selector expression "
            "(e.g. 'Edge:1', 'Edges:all-vertical') or a description the Coder "
            "must translate into a selector (e.g. 'all edges of the base plate')."
        ),
    )

    # -- Hole parameters --
    hole_diameter_mm: float | None = Field(
        None,
        description="Finished hole diameter (mm).",
    )
    hole_depth_mm: float | None = Field(
        None,
        description="Hole depth (mm).  None or > thickness = through-all.",
    )
    hole_position: Point3D | None = Field(
        None,
        description=(
            "3D world-space centre point of the hole (mm). "
            "Accepts Point3D, Point2D (z=0 assumed), [x,y], or [x,y,z]."
        ),
    )
    hole_type: Literal["simple", "counterbore", "countersink", "tapped", "counterbored"] | None = Field(
        "simple",
        description="Type of hole.",
    )
    counterbore_diameter_mm: float | None = Field(
        None,
        description="Counterbore diameter (mm).",
    )
    counterbore_depth_mm: float | None = Field(
        None,
        description="Counterbore depth (mm).",
    )
    countersink_angle_deg: float | None = Field(
        None,
        description="Countersink included angle (degrees, typically 82 or 90).",
    )

    # -- Boolean parameters --
    target_step_id: str | None = Field(
        None,
        description="Reference to another step_id whose geometry is the target of a boolean operation.",
    )
    tool_step_id: str | None = Field(
        None,
        description="Reference to another step_id whose geometry is the tool in a boolean cut.",
    )

    # -- Pattern parameters --
    pattern_count: int | None = Field(
        None,
        description="Number of instances in a pattern (including the original).",
    )
    pattern_spacing_mm: float | None = Field(
        None,
        description="Spacing between pattern instances (mm, linear patterns).",
    )
    pattern_axis: Literal["x", "y", "z"] | None = Field(
        None,
        description="Axis for linear displacement or circular rotation.",
    )
    pattern_total_angle_deg: float | None = Field(
        None,
        description="Total angular span for a circular pattern (degrees, 360 = full circle).",
    )
    feature_step_ids: list[str] | None = Field(
        None,
        description="Step IDs of the features to be patterned.",
    )

    # -- Mirror parameters --
    mirror_plane: Literal["XY", "XZ", "YZ"] | None = Field(
        None,
        description="Mirror plane (standard or offset by a reference).",
    )
    mirror_plane_offset_mm: float | None = Field(
        None,
        description="Offset from the nominal mirror plane (mm).",
    )

    # -- Shell parameters --
    shell_thickness_mm: float | None = Field(
        None,
        description="Target wall thickness for a shell operation (mm).",
    )
    shell_open_faces: list[str] | None = Field(
        None,
        description="Face selector expressions for faces to remove in a shell operation.",
    )

    # -- Draft parameters --
    draft_angle_deg: float | None = Field(
        None,
        description="Draft angle in degrees.",
    )
    draft_neutral_plane: Literal["XY", "XZ", "YZ"] | str | None = Field(
        None,
        description="Neutral plane for the draft (faces are rotated about their intersection with this plane).",
    )
    draft_face_selectors: list[str] | None = Field(
        None,
        description="Face selector expressions for faces to draft.",
    )

    # -- Rib parameters --
    rib_thickness_mm: float | None = Field(
        None,
        description="Rib thickness (mm).",
    )
    rib_height_mm: float | None = Field(
        None,
        description="Rib height (mm).",
    )
    rib_face_selectors: list[str] | None = Field(
        None,
        description="Face selector expressions for faces to attach the rib to.",
    )

    # -- Reference geometry --
    reference_type: Literal["plane", "axis", "point"] | None = Field(
        None,
        description="Type of reference geometry to create (for REFERENCE steps).",
    )
    reference_definition: str | None = Field(
        None,
        description=(
            "How the reference is defined (e.g. 'offset:XY:10mm', "
            "'through:point1:point2', 'normal:face:F3:point:P1')."
        ),
    )


class ArchitectPlan(BaseModel):
    """Step-by-step build123d modeling plan produced by the Geometric Architect."""

    plan_id: str = Field(
        ...,
        description="Unique plan identifier, keyed to the CADBrief it was derived from.",
        examples=["plan-l-bracket-50x40x4-v1"],
    )

    cad_brief_id: str = Field(
        ...,
        description="Corresponding CADBrief.part_name this plan addresses.",
    )

    # -- Sketches --
    sketches: list[Sketch] = Field(
        default_factory=list,
        description="All 2D sketches defined in this plan (referenced by ModelingStep.sketch_id).",
    )

    # -- Modeling steps --
    steps: list[ModelingStep] = Field(
        default_factory=list,
        description="Ordered sequence of build123d operations.",
    )


class AgentState(TypedDict, total=False):

    # -- input text --
    input_text: str
    """Raw user input text describing the desired CAD part."""

    # -- planner output --
    cad_brief: CadBrief | None
    """specification produced by the spec planner agent"""
    

    # -- Python Coder output --
    current_python_code: str | None
    """The latest build123d Python script generated by the Python Coder agent.
    This script must define a ``gen_step()`` callable that returns a build123d
    Shape, compatible with cadpy.generation's script-runner machinery."""

    # -- Geometric Architect output --
    architect_plan: ArchitectPlan | None
    """Step-by-step build123d modeling plan produced by the Geometric Architect."""

    execution_log: list[str]
    """Human-readable log lines from each node (appended by each agent)."""
