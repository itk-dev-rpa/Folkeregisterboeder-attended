"""This module contains a single 'Task' dataclass."""

from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
# pylint: disable=too-many-instance-attributes
class Task:
    """A dataclass representing a single task."""
    cpr: str
    move_date: datetime
    register_date: datetime
    eflyt_case_number: str

    name: Optional[str] = None
    address: Optional[str] = None
    nova_case_uuid: Optional[str] = None
    nova_case_number: Optional[str] = None
    document_uuid: Optional[str] = None
