# Copyright (C) 2026 Tanguy Marsault - PhySense
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Pydantic schemas for the QM router.
Request and response models for eigenstates and time evolution.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# ── Grid ─────────────────────────────────────────────────────────────────────

class GridSchema(BaseModel):
    x_min: float = Field(default=-10.0)
    x_max: float = Field(default=10.0)
    n_points: int = Field(default=512, ge=64, le=2048)

    @model_validator(mode="after")
    def check_bounds(self) -> "GridSchema":
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        return self

class Grid2DSchema(BaseModel):
    x_min: float = Field(default=-10.0)
    x_max: float = Field(default=10.0)
    y_min: float = Field(default=-10.0)
    y_max: float = Field(default=10.0)
    nx: int = Field(default=512, ge=64, le=2048)
    ny: int = Field(default=512, ge=64, le=2048)

    @model_validator(mode="after")
    def check_bounds(self) -> "Grid2DSchema":
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        return self

class Grid3DSchema(BaseModel):
    x_min: float = Field(default=-10.0)
    x_max: float = Field(default=10.0)
    y_min: float = Field(default=-10.0)
    y_max: float = Field(default=10.0)
    z_min: float = Field(default=-10.0)
    z_max: float = Field(default=10.0)
    nx: int = Field(default=128, ge=32, le=512)
    ny: int = Field(default=128, ge=32, le=512)
    nz: int = Field(default=128, ge=32, le=512)

    @model_validator(mode="after")
    def check_bounds(self) -> "Grid3DSchema":
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        if self.z_min >= self.z_max:
            raise ValueError("z_min must be less than z_max")
        return self



# ── Potentials (Option A) ─────────────────────────────────────────────────────

class PotentialType(str, Enum):
    harmonic = "harmonic"
    infinite_well = "infinite_well"
    finite_well = "finite_well"
    barrier = "barrier"
    step = "step"
    double_well = "double_well"
    free = "free"
    custom = "custom"


class HarmonicParams(BaseModel):
    omega: float = Field(default=1.0, gt=0)
    x0: float = Field(default=0.0)


class InfiniteWellParams(BaseModel):
    width: float = Field(default=4.0, gt=0)
    x0: float = Field(default=0.0)


class FiniteWellParams(BaseModel):
    depth: float = Field(default=5.0, gt=0)
    width: float = Field(default=4.0, gt=0)
    x0: float = Field(default=0.0)


class BarrierParams(BaseModel):
    height: float = Field(default=2.0, gt=0)
    width: float = Field(default=1.0, gt=0)
    x0: float = Field(default=0.0)


class StepParams(BaseModel):
    height: float = Field(default=1.0)
    x0: float = Field(default=0.0)


class DoubleWellParams(BaseModel):
    a: float = Field(default=1.0, gt=0)
    b: float = Field(default=4.0, gt=0)


class PotentialSchema(BaseModel):
    type: PotentialType
    params: HarmonicParams | InfiniteWellParams | FiniteWellParams | BarrierParams | StepParams | DoubleWellParams | None = None
    # Option B: custom V(x) values on the grid
    values: list[float] | None = Field(default=None, description="Custom V(x) values, one per grid point (Option B)")

    @model_validator(mode="after")
    def check_custom(self) -> "PotentialSchema":
        if self.type == PotentialType.custom and self.values is None:
            raise ValueError("values must be provided for custom potential")
        if self.type != PotentialType.custom and self.values is not None:
            raise ValueError("values should only be provided for custom potential")
        return self




# ── Eigenstates ───────────────────────────────────────────────────────────────

class EigenstatesRequest(BaseModel):
    grid: GridSchema = Field(default_factory=GridSchema)
    potential: PotentialSchema
    n_states: int = Field(default=6, ge=1, le=20)


class EigenstatesResponse(BaseModel):
    x: list[float]
    potential: list[float]
    energies: list[float]
    wavefunctions: list[list[float]]  # shape: (n_states, n_points)
    n_states: int

class SingleAtomStateRequest(BaseModel):
    grid: Grid3DSchema = Field(default_factory=Grid3DSchema)
    Z: int = Field(default=1, ge=1, le=100, description="Atomic number")
    n: int = Field(default=1, ge=1, le=10, description="Principal quantum number")
    l: int = Field(default=0, ge=0, le=9, description="Orbital angular momentum quantum number")
    m: int = Field(default=0, description="Magnetic quantum number")

class SingleAtomStateResponse(BaseModel):
    x: list[float]
    y: list[float]
    z: list[float]
    psi: list[list[list[float]]]  # real part of ψ, signed — shape: (nx, ny, nz)
    Z: int
    n: int
    l: int
    m: int
    
# ── Evolution (WebSocket) ─────────────────────────────────────────────────────

class WavepacketSchema(BaseModel):
    x0: float = Field(default=-5.0, description="Initial position")
    k0: float = Field(default=1.5, description="Initial momentum")
    sigma: float = Field(default=1.0, gt=0, description="Spatial width")


class EvolveRequest(BaseModel):
    grid: GridSchema = Field(default_factory=GridSchema)
    potential: PotentialSchema
    wavepacket: WavepacketSchema = Field(default_factory=WavepacketSchema)
    t_max: float = Field(default=10.0, gt=0, le=50.0)
    dt: float = Field(default=0.01, gt=0, le=0.1)
    n_frames: int = Field(default=60, ge=10, le=200)


class EvolveFrame(BaseModel):
    frame: int
    t: float
    probability_density: list[float]
    norm: float


class EvolveMetadata(BaseModel):
    x: list[float]
    potential: list[float]
    t_max: float
    n_frames: int


__all__ = [
    "GridSchema",
    "PotentialType",
    "PotentialSchema",
    "EigenstatesRequest",
    "EigenstatesResponse",
    "WavepacketSchema",
    "EvolveRequest",
    "EvolveFrame",
    "EvolveMetadata",
    "SingleAtomStateRequest",
    "SingleAtomStateResponse",
]
