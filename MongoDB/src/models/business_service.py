"""Pydantic models for business_services collection"""
from typing import List, Optional
from pydantic import BaseModel


class BAO(BaseModel):
    name: str
    email: str


class Contacts(BaseModel):
    bao: BAO
    dl_team: str
    reperibilita_number: str
    snow_group: Optional[str] = None


class ServiceInfo(BaseModel):
    name: str
    service_now_id: str
    status: str


class Schema(BaseModel):
    schema_name: str
    type: str


class TechnicalMapping(BaseModel):
    db_unique_name: str
    schemas: List[Schema] = []


class BusinessService(BaseModel):
    """Main model for business_services collection"""
    service_info: ServiceInfo
    contacts: Contacts
    technical_mapping: List[TechnicalMapping] = []

    class Config:
        populate_by_name = True
