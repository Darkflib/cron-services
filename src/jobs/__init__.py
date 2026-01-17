"""Job modules for scheduled tasks."""

from .base import BaseJob
from .ecb import ECBJob
from .geonames import GeonamesJob
from .maxmind import MaxMindJob
from .ofcom import OfcomJob

__all__ = ["BaseJob", "ECBJob", "GeonamesJob", "MaxMindJob", "OfcomJob"]

# Job registry for easy lookup
JOBS = {
    "ecb": ECBJob,
    "geonames": GeonamesJob,
    "maxmind": MaxMindJob,
    "ofcom": OfcomJob,
}
