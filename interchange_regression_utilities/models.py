import abc
import json
import pickle
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Type, TypeVar, Union

import yaml
from openff.toolkit.topology import Molecule, Topology
from pydantic import BaseModel, Extra, Field, PositiveInt, conlist, parse_obj_as

from interchange_regression_utilities.utilities import use_openff_units

T = TypeVar("T")

CommonModelType = TypeVar("CommonModelType", bound=BaseModel)


def model_from_file(type_: Type[T], path: Union[Path, str, PathLike[str]]) -> T:

    path = Path(path)
    mode = "r"

    if path.suffix.lower() == ".yaml":
        serializer = yaml
    elif path.suffix.lower() == ".json":
        serializer = json
    elif path.suffix.lower() == ".pkl":
        serializer = pickle
        mode = "rb"
    else:
        raise NotImplementedError()

    with path.open(mode) as file:
        raw_object = serializer.load(file)

    return parse_obj_as(type_, raw_object)


def model_to_file(
    model: Union[BaseModel, List[BaseModel]], path: Union[Path, str, PathLike[str]]
):

    path = Path(path)
    mode = "w"

    if path.suffix.lower() == ".yaml":
        serializer = yaml
    elif path.suffix.lower() == ".json":
        serializer = json
    elif path.suffix.lower() == ".pkl":
        serializer = pickle
        mode = "wb"
    else:
        raise NotImplementedError()

    if isinstance(model, BaseModel):
        raw_object = model.dict()
    elif isinstance(model, list):
        raw_object = [item.dict() for item in model]
    else:
        raise NotImplementedError()

    with path.open(mode) as file:
        serializer.dump(raw_object, file)


class CommonModel(BaseModel):
    class Config:
        extra = Extra.forbid

    def to_file(self, path: Union[Path, str, PathLike[str]]):
        model_to_file(self, path)

    @classmethod
    def from_file(
        cls: Type[CommonModelType], path: Union[Path, str, PathLike[str]]
    ) -> CommonModelType:

        return model_from_file(cls, path)


class TopologyComponent(CommonModel):
    """Represents the type of molecule as well as how many copies of that molecule
    should be added to a topology.
    """

    smiles: str = Field(..., description="The SMILES representation of the component")

    n_copies: PositiveInt = Field(
        ...,
        description="The number of copies of the component present in the topology.",
    )


class TopologyDefinition(CommonModel):
    """A model that defines which molecules and how many of each should be added to
    a topology.
    """

    name: str = Field(..., description="A unique name to give to the system.")

    components: conlist(TopologyComponent, min_items=1) = Field(
        ..., description="The components to add to the topology."
    )
    is_periodic: bool = Field(
        ..., description="Whether the topology should be periodic."
    )

    def to_topology(self) -> Topology:

        if use_openff_units():
            from openff.units import unit
        else:
            from openmm import unit

        molecules = [
            (
                Molecule.from_smiles(component.smiles, allow_undefined_stereo=True),
                component.n_copies,
            )
            for component in self.components
        ]
        topology = Topology.from_molecules(
            [molecule for molecule, n_copies in molecules for _ in range(n_copies)]
        )

        if self.is_periodic:
            topology.box_vectors = [2.0, 2.0, 2.0] * unit.nanometers

        return topology


class ExpectedDifference(CommonModel, abc.ABC):

    type: Literal["base-type"]

    path: str = Field(..., description="The path to the field that should be different")


class ExpectedValueChange(ExpectedDifference):

    type: Literal["value-changed"] = "value-changed"

    old_value: Any = Field(..., description="The expected old value")
    new_value: Any = Field(..., description="The expected new value")


class ComparisonSettings(CommonModel):
    """Settings to use when comparing two OpenMM systems."""

    default_numeric_tolerance: float = Field(
        1.0e-6,
        description="Two numeric values whose absolute difference is larger than this "
        "value are considered as 'different'",
    )
    numeric_tolerance_overrides: Dict[str, float] = Field(
        dict(),
        description="Overrides of the ``default_numeric_tolerance`` for specific "
        "fields of the OpenMM system.",
    )


class Perturbation(CommonModel):

    path: str = Field(
        ..., description="The path to the value in the force field to perturb."
    )

    new_value: Any = Field(..., description="The new value")
    new_units: Optional[str] = Field(None, description="The units of the new value")
