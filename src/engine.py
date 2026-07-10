"""Runs the drone simulation: plans one drone at a time, then prints it."""

from typing import Dict, List, Optional

from src.algorithm.pathfinder import Path, Pathfinder
from src.models.graph import Graph


class SimulationEngine:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder(graph)

        # drone_id -> its full planned route
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
                continue  # waiting in place: no connection crossed

            # Normal/priority move: the connection is crossed on arrival.
            # Restricted move (2-turn gap): it's crossed the turn before.
            connection_turn = turn if turn - prev_turn == 1 else prev_turn + 1
            self._reserve_connection(prev_zone, zone, connection_turn)

    def _reserve_zone(self, zone: str, turn: int) -> None:
        if zone in (self.graph.start.name, self.graph.end.name):
            return  # unlimited capacity, nothing to book

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



# from typing import Dict, List, Tuple, Optional
# from src.models.graph import Graph
# from src.algorithm.pathfinder import Pathfinder
# # from src.pathfinding.pathfinder import Pathfinder # Import the Class we built above

# class SimulationEngine:
#     def __init__(self, graph: 'Graph', nb_drones: int) -> None:
#         self.graph: 'Graph' = graph
#         self.nb_drones: int = nb_drones

#         # 1. Create our Pathfinder instance
#         self.pathfinder = Pathfinder(graph)

#         # 2. Dictionary to store the Path for each drone ID
#         # Format: Drone ID -> List[(Time, Zone)]
#         self.all_paths: Dict[int, List[Tuple[int, str]]] = {}

#     def run(self) -> bool:
#         """The main loop that iterates through each drone one by one."""

#         for drone_id in range(1, self.nb_drones + 1):
#             path: List[Tuple[int, str]] = self.pathfinder.find_path()

#             # B. If the algorithm gets stuck and cannot find a path (Deadlock)
#             if not path:
#                 print(f"Error: Could not find a path for Drone D{drone_id}!")
#                 return False

#             # C. Store the path
#             self.all_paths[drone_id] = path

#             # D. Register this path in the reservation table so the next drone knows about the traffic!
#             self.register_path(path)

#         # Once all drones are processed, print the simulation result
#         self.print_simulation()
#         return True

#     def register_path(self, path: List[Tuple[int, str]]) -> None:
#         """Fills the Pathfinder's Reservation Table with the zones the drone will pass through."""

#         for time, zone_name in path:
#             # Start and end zones always have unlimited capacity, so we don't register them
#             if zone_name not in [self.graph.start_zone.name, self.graph.end_zone.name]:

#                 # If the reservation table is empty for this time, create it
#                 if time not in self.pathfinder.zone_reservations:
#                     self.pathfinder.zone_reservations[time] = {}

#                 # If the zone is empty at this time, initialize it to 0
#                 if zone_name not in self.pathfinder.zone_reservations[time]:
#                     self.pathfinder.zone_reservations[time][zone_name] = 0

#                 # Add 1 (One drone reserved a spot)
#                 self.pathfinder.zone_reservations[time][zone_name] += 1

#     def get_zone_at_time(self, path: List[Tuple[int, str]], target_time: int) -> Optional[str]:
#         """Retrieves the zone where the drone is located at a specific given turn."""
#         last_zone = None
#         for time, zone in path:
#             if time == target_time:
#                 return zone
#             if time > target_time:
#                 break
#             last_zone = zone
#         return last_zone

#     def print_simulation(self) -> None:
#         """Prints the simulation result turn by turn using the required format."""
#         if not self.all_paths:
#             return

#         # 1. Find the total number of turns (the maximum time reached by the last drone)
#         max_time: int = 0
#         for path in self.all_paths.values():
#             if path:
#                 max_time = max(max_time, path[-1][0])

#         # 2. Print from Turn 1 to the end (Turn 0 is when they are at the start)
#         for current_time in range(1, max_time + 1):
#             moves_in_this_turn: List[str] = []

#             for drone_id, path in self.all_paths.items():

#                 prev_zone = self.get_zone_at_time(path, current_time - 1)
#                 curr_zone = self.get_zone_at_time(path, current_time)

#                 # The subject states: "Drones that do not move in a given turn are omitted from that line"
#                 # Meaning if the drone stays in place (Wait action), we do not print it
#                 # And once it reaches the goal, it is no longer tracked
#                 if curr_zone and curr_zone != prev_zone:
#                     moves_in_this_turn.append(f"D{drone_id}-{curr_zone}")

#             if moves_in_this_turn:
#                 print(" ".join(moves_in_this_turn))
