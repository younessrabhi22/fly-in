from typing import Dict, List, Optional
from src.models.zone import Zone
from src.models.connection import Connection


class Graph:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}

        self.connections_map: Dict[str, List[Connection]] = {}

        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    @property
    def start(self) -> Zone:
        """Typed access to the start zone (the parser guarantees it exists)."""
        assert self.start_zone is not None, "Graph has no start zone yet"
        return self.start_zone

    @property
    def end(self) -> Zone:
        """Typed access to the end zone (the parser guarantees it exists)."""
        assert self.end_zone is not None, "Graph has no end zone yet"
        return self.end_zone

    def add_zone(
        self, zone: Zone, is_start: bool = False, is_end: bool = False
    ) -> None:
        """
        Adds a new zone to the graph and initializes its list of neighbors.
        """
        self.zones[zone.name] = zone
        self.connections_map[zone.name] = []

        if is_start:
            self.start_zone = zone
        if is_end:
            self.end_zone = zone

    def has_connection(self, zone1_name: str, zone2_name: str) -> bool:
        """
        Checks if a connection already exists between zone1 and zone2.
        """
        if zone1_name in self.connections_map:
            for conn in self.connections_map[zone1_name]:
                if conn.zone_to == zone2_name or conn.zone_from == zone2_name:
                    return True
        return False

    def add_connection(self, connection: Connection) -> None:
        """
        Adds a bidirectional connection between two zones in the graph.
        """
        if connection.zone_from in self.connections_map:
            self.connections_map[connection.zone_from].append(connection)

        if connection.zone_to in self.connections_map:
            self.connections_map[connection.zone_to].append(connection)

    def __repr__(self) -> str:
        start_name = self.start_zone.name if self.start_zone else None
        end_name = self.end_zone.name if self.end_zone else None
        return (
            f"Graph(zones_count={len(self.zones)}, "
            f"start={start_name}, end={end_name})"
        )
