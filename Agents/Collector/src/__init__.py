"""Collector source package"""
from .ssh_connection import GatewayConnection, DirectConnection

__all__ = ["GatewayConnection", "DirectConnection"]
