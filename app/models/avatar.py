from enum import StrEnum


class DuckAvatar(StrEnum):
    """The pickable ducklings.

    Avatars are a fixed set rather than uploads: no file storage, no moderation,
    no way for one user to put something unpleasant in front of another.
    """

    CLOVER = "clover"
    NERD = "nerd"
    BOW = "bow"
    ADVENTURER = "adventurer"
    FOODIE = "foodie"
    CHILL = "chill"


# Shown by GET /avatars so the UI never hardcodes this list.
AVATAR_CATALOG: dict[DuckAvatar, dict[str, str]] = {
    DuckAvatar.CLOVER: {
        "title": "Clover Duck",
        "description": "Carries a four-leaf clover. Quietly lucky.",
    },
    DuckAvatar.NERD: {
        "title": "Nerd Duck",
        "description": "Big glasses, bigger plans.",
    },
    DuckAvatar.BOW: {
        "title": "Bow Duck",
        "description": "Never leaves the pond without the ribbon.",
    },
    DuckAvatar.ADVENTURER: {
        "title": "Adventurer Duck",
        "description": "Backpack on, always one hill further.",
    },
    DuckAvatar.FOODIE: {
        "title": "Foodie Duck",
        "description": "Here for the snacks, staying for the streak.",
    },
    DuckAvatar.CHILL: {
        "title": "Chill Duck",
        "description": "Sunglasses on. No rush, no pressure.",
    },
}
