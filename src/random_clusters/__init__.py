"""Generate synthetic, labelled clustering datasets without filesystem side effects."""

from .core import Dataset, GeneratorConfig, add_noise, generate

__version__ = "1.0.0"
__all__ = ["Dataset", "GeneratorConfig", "add_noise", "generate"]
