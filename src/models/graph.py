from typing import Dict, List, Optional
from src.models.zone import Zone
from src.models.connection import Connection

class Graph:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}

        self.adjacency_list: Dict[str, List[Connection]] = {}

        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone, is_start: bool = False, is_end: bool = False) -> None:
        """
        Adds a new zone to the graph and initializes its list of neighbors.
        """
        self.zones[zone.name] = zone
        self.adjacency_list[zone.name] = []

        if is_start:
            self.start_zone = zone
        if is_end:
            self.end_zone = zone

    def add_connection(self, connection: Connection) -> None:
        """
        Adds a bidirectional connection between two zones in the graph.
        """
        if connection.zone_from in self.adjacency_list:
            self.adjacency_list[connection.zone_from].append(connection)

        if connection.zone_to in self.adjacency_list:
            self.adjacency_list[connection.zone_to].append(connection)

    def __repr__(self) -> str:
        return f"Graph(zones_count={len(self.zones)}, start={self.start_zone.name if self.start_zone else None}, end={self.end_zone.name if self.end_zone else None})"
