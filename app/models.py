from enum import Enum
from typing import Optional

from pydantic import BaseModel


class BookStatus(str, Enum):
    AVAILABLE = "available"
    ISSUED = "issued"
    RESERVED = "reserved"


class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Book(BaseModel):
    id: int
    title: str
    author: str
    category: str
    status: BookStatus
    borrower_id: Optional[int] = None


class Member(BaseModel):
    id: int
    name: str
    email: str
    status: MemberStatus


class IssueRequest(BaseModel):
    member_id: int


class BookView(BaseModel):
    id: int
    title: str
    author: str
    category: str
    status: BookStatus
    borrower_id: Optional[int] = None
    borrower_name: Optional[str] = None


class DashboardSummary(BaseModel):
    total_books: int
    available_books: int
    issued_books: int
    active_members: int
