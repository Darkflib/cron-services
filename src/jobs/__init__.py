"""Job modules for scheduled tasks."""

from typing import Dict, Type

from .base import BaseJob
from .ecb import ECBJob
from .geonames import GeonamesJob
from .maxmind import MaxMindJob
from .ofcom import OfcomJob

__all__ = ["BaseJob", "ECBJob", "GeonamesJob", "MaxMindJob", "OfcomJob"]

# Job registry for easy lookup
JOBS: Dict[str, Type[BaseJob]] = {
    "ecb": ECBJob,
    "geonames": GeonamesJob,
    "maxmind": MaxMindJob,
    "ofcom": OfcomJob,
}
