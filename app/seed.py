"""Fictional seed data for Maple Grove Community Library."""

from app.models import Book, BookStatus, Member, MemberStatus

AVAILABLE, ISSUED, RESERVED = BookStatus.AVAILABLE, BookStatus.ISSUED, BookStatus.RESERVED


def seed_members() -> list:
    return [
        Member(
            id=1,
            name="Alice Hartwell",
            email="alice.hartwell@example.org",
            status=MemberStatus.ACTIVE,
        ),
        Member(
            id=2,
            name="Bashir Okafor",
            email="bashir.okafor@example.org",
            status=MemberStatus.ACTIVE,
        ),
        Member(
            id=3,
            name="Clara Lindqvist",
            email="clara.lindqvist@example.org",
            status=MemberStatus.ACTIVE,
        ),
        Member(
            id=4, name="Dmitri Varga", email="dmitri.varga@example.org", status=MemberStatus.ACTIVE
        ),
        Member(
            id=5,
            name="Esme Calloway",
            email="esme.calloway@example.org",
            status=MemberStatus.ACTIVE,
        ),
        Member(
            id=6,
            name="Felix Moreau",
            email="felix.moreau@example.org",
            status=MemberStatus.INACTIVE,
        ),
    ]


def seed_books() -> list:
    return [
        Book(
            id=1,
            title="The Maple Orchard",
            author="Rowan Ellis",
            category="Fiction",
            status=AVAILABLE,
        ),
        Book(
            id=2,
            title="Letters from Birchwood",
            author="Hana Petrov",
            category="Fiction",
            status=ISSUED,
            borrower_id=1,
        ),
        Book(
            id=3,
            title="A Short History of Grain",
            author="Tom Reyes",
            category="History",
            status=AVAILABLE,
        ),
        Book(
            id=4,
            title="Rivers of the Old Province",
            author="Ines Duarte",
            category="History",
            status=ISSUED,
            borrower_id=2,
        ),
        Book(
            id=5,
            title="Understanding Tides",
            author="Priya Nair",
            category="Science",
            status=AVAILABLE,
        ),
        Book(
            id=6, title="The Quiet Atom", author="Lars Ohlsen", category="Science", status=RESERVED
        ),
        Book(
            id=7,
            title="Backyard Astronomy",
            author="Mei Tanaka",
            category="Science",
            status=ISSUED,
            borrower_id=3,
        ),
        Book(
            id=8,
            title="Pip and the Paper Boat",
            author="Greta Foss",
            category="Children",
            status=AVAILABLE,
        ),
        Book(
            id=9, title="The Lantern Fox", author="Greta Foss", category="Children", status=RESERVED
        ),
        Book(
            id=10,
            title="Sourdough Seasons",
            author="Maya Brandt",
            category="Cooking",
            status=AVAILABLE,
        ),
        Book(
            id=11,
            title="One-Pot Winters",
            author="Maya Brandt",
            category="Cooking",
            status=AVAILABLE,
        ),
        Book(
            id=12,
            title="Gardens of the North",
            author="Owen Calder",
            category="Nature",
            status=ISSUED,
            borrower_id=5,
        ),
    ]
