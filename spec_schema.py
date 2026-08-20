"""Extensible Pydantic models defining the CAD specification schema.

The schema is deliberately shaped so downstream CAD generation (build123d,
OpenSCAD, ...) can consume it directly, while `extensions` / `metadata` keep it
open for future fields without schema churn.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Unit(str, Enum):
    MM = "mm"
    CM = "cm"
    IN = "in"


class Workplane(str, Enum):
    XY = "XY"
    XZ = "XZ"
    YZ = "YZ"


class Dimensions(BaseModel):
    length: Optional[float] = Field(
        default=None, description="Primary length along the workplane X axis."
    )
    width: Optional[float] = Field(
        default=None, description="Width along the workplane Y axis."
    )
    height: Optional[float] = Field(
        default=None, description="Height along the workplane normal axis."
    )

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def _warn_missing(self) -> "Dimensions":
        # Placeholder hook so future per-field validation can be added here.
        return self


class Location(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class Feature(BaseModel):
    type: str = Field(description="Feature type, e.g. hole, slot, cut, fillet.")
    diameter: Optional[float] = None
    radius: Optional[float] = None
    depth: Optional[float] = None
    length: Optional[float] = None
    width: Optional[float] = None
    location: Optional[Location] = None
    count: Optional[int] = Field(default=None, description="Number of instances (null if single).")

    model_config = ConfigDict(extra="allow")


class CadSpec(BaseModel):
    """Top-level, extensible CAD specification document."""

    spec_version: str = Field(default="1.0", description="Schema version, used for forward compatibility.")
    part_name: str = Field(description="Short descriptive name of the part.")
    unit: Unit = Unit.MM
    primary_workplane: Workplane = Workplane.XY
    material: str = Field(default="PLA", description="Material fallback is PLA.")
    dimensions: Dimensions = Field(default_factory=Dimensions)
    features: List[Feature] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form build metadata (tolerances, finish, process, ...).",
    )
    extensions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Escape hatch for any future / unknown fields. Never drop data here.",
    )

    model_config = ConfigDict(extra="allow")