STATUS_AVAILABLE = "AVAILABLE"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_PICKED_UP = "PICKED_UP"
STATUS_COMPLETED = "COMPLETED"

DONATION_STATUSES = [STATUS_AVAILABLE, STATUS_ACCEPTED, STATUS_PICKED_UP, STATUS_COMPLETED]

PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"

DONOR_LEVELS = {
    "BRONZE": (0, 499),
    "SILVER": (500, 1499),
    "GOLD": (1500, 2999),
    "PLATINUM": (3000, float("inf")),
}

def get_donor_level(total_points: int) -> str:
    for level, (low, high) in DONOR_LEVELS.items():
        if low <= total_points <= high:
            return level
    return "BRONZE"