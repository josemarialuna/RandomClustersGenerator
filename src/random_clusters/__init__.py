"""Generate synthetic, labelled clustering datasets without filesystem side effects."""

from .core import Dataset, GeneratorConfig, add_noise, generate
from .families import Condition, FamilyConfig, PairedDataset, PairedFamily

__version__ = "1.1.0"
__all__ = [
    "Dataset",
    "GeneratorConfig",
    "add_noise",
    "generate",
    "Condition",
    "FamilyConfig",
    "PairedDataset",
    "PairedFamily",
]
