import heapq
from typing import Dict, List, Optional, Set, Tuple

from src.models.connection import Connection
from src.models.graph import Graph

Path = List[Tuple[int, str]]
ConnectionKey = Tuple[str, str]


class Pathfinder:
    """Finds the fastest conflict-free space-time path for one drone."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

        # Tracks how many drones are in a specific zone at a specific time
        self.zone_reservations: Dict[int, Dict[str, int]] = {}
        # Tracks how many drones are traversing a connection at a specific time
        self.connection_reservations: Dict[int, Dict[ConnectionKey, int]] = {}

    def is_zone_free(self, zone_name: str, turn: int) -> bool:
        """Can a drone be inside `zone_name` at `turn`?"""
        zone = self.graph.zones[zone_name]

        if zone.zone_type == "blocked":
            return False
        if zone_name in (self.graph.start.name, self.graph.end.name):
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
            neighbors.append(conn.zone_to if conn.zone_from == zone_name else conn.zone_from)
        return neighbors

    def move_cost(self, zone_name: str) -> int:
        """Turns needed to enter `zone_name`: 2 for restricted, 1 otherwise."""
        return 2 if self.graph.zones[zone_name].zone_type == "restricted" else 1

    def is_priority(self, zone_name: str) -> bool:
        """Whether `zone_name` should be preferred when two routes tie on cost."""
        return self.graph.zones[zone_name].zone_type == "priority"

    def find_path(self) -> Path:
        start = self.graph.start.name
        goal = self.graph.end.name

        # Counter guarantees strict FIFO tie-breaking, avoiding string/alphabet comparison
        counter = 0

        # Queue format: (arrival_time, priority_tiebreak, heatmap_crowd, fifo_counter, zone_name)
        priority_queue: List[Tuple[int, int, int, int, str]] = [(0, 0, 0, counter, start)]

        # Tracks visited states to prevent infinite loops (Time-Space node tracking)
        visited: Set[Tuple[int, str]] = {(0, start)}

        # Stores the optimal path reconstruction map
        came_from: Dict[Tuple[int, str], Optional[Tuple[int, str]]] = {(0, start): None}

        while priority_queue:
            turn, _, _, _, zone = heapq.heappop(priority_queue)

            # Failsafe to prevent endless wandering in highly congested maps
            if turn > 10000:
                continue

            if zone == goal:
                return self._rebuild_path((turn, zone), came_from)

            # Evaluate moving to all neighbors PLUS the option to wait in the current zone
            for next_zone in self.get_neighbors(zone) + [zone]:
                waiting = next_zone == zone
                step_cost = 1 if waiting else self.move_cost(next_zone)
                arrival = turn + step_cost

                # Validate if capacities (zone and connection) allow this move
                if not self._can_move(zone, next_zone, turn, arrival, waiting):
                    continue

                state = (arrival, next_zone)

                if state not in visited:
                    visited.add(state)
                    came_from[state] = (turn, zone)

                    # Tiebreak 1: Priority zones get 0 (top of queue), normal get 1
                    tiebreak = 0 if self.is_priority(next_zone) else 1

                    # Tiebreak 2: Heatmap logic. Sums all historical reservations for this zone
                    # to naturally force load balancing (Zipper effect) across the map
                    crowd_level = sum(turn_data.get(next_zone, 0) for turn_data in self.zone_reservations.values())

                    # Tiebreak 3: Strict incremental counter acts as the final decision maker
                    counter += 1

                    heapq.heappush(priority_queue, (arrival, tiebreak, crowd_level, counter, next_zone))

        return []

    def _can_move(
        self, zone: str, next_zone: str, turn: int, arrival: int, waiting: bool
    ) -> bool:
        """Checks every capacity rule that applies to one candidate move."""
        if waiting:
            return self.is_zone_free(next_zone, arrival)

        # Restricted moves (2 turns) require the connection to be free on the transit turn
        if arrival - turn == 2:
            transit_turn = turn + 1
            return (
                self.is_connection_free(zone, next_zone, transit_turn)
                and self.is_zone_free(next_zone, arrival)
            )

        # Standard 1-turn move validation
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
