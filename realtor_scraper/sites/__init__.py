from .base import SiteAdapter
from .realtor_com import RealtorComAdapter

ADAPTERS = {
    "realtor_com": RealtorComAdapter,
}

__all__ = ["SiteAdapter", "RealtorComAdapter", "ADAPTERS"]
