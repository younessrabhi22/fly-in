import heapq
from typing import Dict, List, Optional, Set, Tuple
from connection import Connection
from graph import Graph

Path = List[Tuple[int, str]]
ConnectionKey = Tuple[str, str]


class Pathfinder:
    """Finds the fastest conflict-free space-time path for one drone."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

        self.zone_reservations: Dict[int, Dict[str, int]] = {}
        self.connection_reservations: Dict[int, Dict[ConnectionKey, int]] = {}

    def is_zone_free(self, zone_name: str, turn: int) -> bool:
        """Can a drone be inside `zone_name` at `turn`?"""
        if not self.graph.start_zone or not self.graph.end_zone:
            return False

        zone = self.graph.zones[zone_name]

        if zone.zone_type == "blocked":
            return False
        if zone_name in (self.graph.start_zone.name, self.graph.end_zone.name):
            return True

        occupied = self.zone_reservations.get(turn, {}).get(zone_name, 0)
        return occupied < zone.max_drones

    def is_connection_free(self, zone_a: str, zone_b: str, turn: int) -> bool:
        """Can a drone cross the connection between two zones at `turn`?"""
        connection = self.get_connection(zone_a, zone_b)
        key = self.connection_key(zone_a, zone_b)
        used = self.connection_reservations.get(turn, {}).get(key, 0)
        return used < connection.max_link_capacity

    @staticmethod
    def connection_key(zone_a: str, zone_b: str) -> ConnectionKey:
        """a-b and b-a must reserve the same slot, so we sort the names."""
        return (zone_a, zone_b) if zone_a < zone_b else (zone_b, zone_a)

    def get_connection(self, zone_a: str, zone_b: str) -> Connection:
        """Returns the Connection object directly linking two zones."""
        for conn in self.graph.connections_map.get(zone_a, []):
            if zone_b in (conn.zone_from, conn.zone_to):
                return conn
        raise ValueError(f"No connection between '{zone_a}' and '{zone_b}'")

    def get_neighbors(self, zone_name: str) -> List[str]:
        """Returns the names of zones directly reachable from `zone_name`."""
        neighbors: List[str] = []
        for conn in self.graph.connections_map.get(zone_name, []):
            neighbors.append(
                conn.zone_to if conn.zone_from == zone_name else conn.zone_from
            )
        return neighbors

    def find_path(self) -> Path:
        if not self.graph.start_zone or not self.graph.end_zone:
            return []

        start = self.graph.start_zone.name
        goal = self.graph.end_zone.name

        priority_queue: List[Tuple[int, int, str]] = [(0, 0, start)]
        visited: Set[Tuple[int, str]] = {(0, start)}
        came_from: Dict[Tuple[int, str], Optional[Tuple[int, str]]] = {
            (0, start): None
        }

        while priority_queue:
            turn, _, zone = heapq.heappop(priority_queue)

            if turn > 10000:
                continue

            if zone == goal:
                return self._rebuild_path((turn, zone), came_from)

            for next_zone in self.get_neighbors(zone) + [zone]:
                waiting = next_zone == zone

                if waiting:
                    step_cost = 1
                elif self.graph.zones[next_zone].zone_type == "restricted":
                    step_cost = 2
                else:
                    step_cost = 1

                arrival = turn + step_cost

                if not self._can_move(zone, next_zone, turn, arrival, waiting):
                    continue

                state = (arrival, next_zone)

                if state not in visited:
                    visited.add(state)
                    came_from[state] = (turn, zone)

                    if self.graph.zones[next_zone].zone_type == "priority":
                        tiebreak = 0
                    elif waiting:
                        tiebreak = 3
                    else:
                        tiebreak = 1
                    heapq.heappush(
                        priority_queue, (arrival, tiebreak, next_zone)
                        )

        return []

    def _can_move(
        self, zone: str, next_zone: str, turn: int, arrival: int, waiting: bool
    ) -> bool:
        """Checks every capacity rule that applies to one candidate move."""
        if waiting:
            return self.is_zone_free(next_zone, arrival)

        # Restricted moves (2 turns) require
        # the connection to be free on the transit turn
        if arrival - turn == 2:
            transit_turn = turn + 1
            return (
                self.is_connection_free(zone, next_zone, transit_turn)
                and self.is_zone_free(next_zone, arrival)
            )

        return (
            self.is_connection_free(zone, next_zone, arrival)
            and self.is_zone_free(next_zone, arrival)
        )

    @staticmethod
    def _rebuild_path(
        goal_state: Tuple[int, str],
        came_from: Dict[Tuple[int, str], Optional[Tuple[int, str]]],
    ) -> Path:
        """Walks `came_from` backwards from the goal to rebuild the path."""
        path: Path = []
        state: Optional[Tuple[int, str]] = goal_state
        while state is not None:
            path.append(state)
            state = came_from[state]
        path.reverse()
        return path
