from typing import Dict, List, Optional

from src.algorithm.pathfinder import Path, Pathfinder
from src.models.graph import Graph

class SimulationEngine:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder(graph)

        self.all_paths: Dict[int, Path] = {}

    def run(self) -> bool:
        """Plans a path for every drone, one after another, then prints it."""
        for drone_id in range(1, self.nb_drones + 1):
            path = self.pathfinder.find_path()

            if not path:
                print(f"Error: Could not find a path for Drone D{drone_id}!")
                return False

            self.all_paths[drone_id] = path
            self.register_path(path)

        self.print_simulation()
        return True

    def register_path(self, path: Path) -> None:
        """Books every zone and connection this drone will use, turn by
        turn, so the next drone's search knows about the traffic."""
        for turn, zone in path:
            self._reserve_zone(zone, turn)

        for (prev_turn, prev_zone), (turn, zone) in zip(path, path[1:]):
            if zone == prev_zone:
                continue
            connection_turn = turn if turn - prev_turn == 1 else prev_turn + 1
            self._reserve_connection(prev_zone, zone, connection_turn)

    def _reserve_zone(self, zone: str, turn: int) -> None:
        if zone in (self.graph.start.name, self.graph.end.name):
            return

        turn_zones = self.pathfinder.zone_reservations.setdefault(turn, {})
        turn_zones[zone] = turn_zones.get(zone, 0) + 1

    def _reserve_connection(self, zone_a: str, zone_b: str, turn: int) -> None:
        key = self.pathfinder.connection_key(zone_a, zone_b)
        turn_conns = self.pathfinder.connection_reservations.setdefault(turn, {})
        turn_conns[key] = turn_conns.get(key, 0) + 1

    def get_location_at_time(self, path: Path, target_time: int) -> Optional[str]:
        """Where is the drone at `target_time`?

        Returns a zone name, or -- if `target_time` falls in the middle of
        a restricted-zone move -- "zoneA-zoneB" for the connection it's
        currently crossing.
        """
        last_zone: Optional[str] = None

        for index, (turn, zone) in enumerate(path):
            if turn == target_time:
                return zone

            if turn > target_time:
                previous_zone = path[index - 1][1]
                return f"{previous_zone}-{zone}"

            last_zone = zone
        return last_zone

    def print_simulation(self) -> None:
        """Prints one line per turn, listing every drone that moved that turn."""
        if not self.all_paths:
            return

        max_turn = max(path[-1][0] for path in self.all_paths.values() if path)

        for current_turn in range(1, max_turn + 1):
            moves_this_turn: List[str] = []
            
            for drone_id, path in self.all_paths.items():
                previous_location = self.get_location_at_time(path, current_turn - 1)
                current_location = self.get_location_at_time(path, current_turn)

                # Drones that waited, or already reached the goal, are omitted.
                if current_location and current_location != previous_location:
                    moves_this_turn.append(f"D{drone_id}-{current_location}")

            if moves_this_turn:
                print(" ".join(moves_this_turn))
