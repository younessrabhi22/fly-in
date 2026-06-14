class Connection:
    """
    Represents a bidirectional path between two zones.
    """
    def __init__(
        self,
        zone_from: str,
        zone_to: str,
        max_link_capacity: int = 1
    ) -> None:
        self.zone_from = zone_from
        self.zone_to = zone_to
        self.max_link_capacity = max_link_capacity
        self.current_drones: int = 0

    def __repr__(self) -> str:
        return f"Connection({self.name}, capacity={self.max_link_capacity}, current={self.current_drones})"
