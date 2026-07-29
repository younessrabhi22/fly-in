from graph import Graph
from zone import Zone
from connection import Connection
import sys
from typing import Tuple, Dict, Any


class MapParser:
    def __init__(self, map_path: str) -> None:
        self.map_path = map_path
        self.lines = []
        try:
            with open(self.map_path, "r") as f:
                self.lines = f.readlines()
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f"Could not read the map file: {e}")

    def _parse_zone_data(
        self,
        data_str: str,
        line_index: int,
        graph: Graph,
        is_start_or_end: bool = False,
    ) -> Tuple[str, int, int, Dict[str, Any]]:
        """
        Helper function to extract name, x, y, and metadata from any zone line.
        """
        meta_dict: Dict[str, Any] = {"zone_type": "normal", "color": None, "max_drones": 1}

        # 1. Parse Metadata if it exists
        if "[" in data_str:
            if data_str.count("[") > 1 or data_str.count("]") > 1:
                raise ValueError(f"Error on line {line_index}: Invalid metadata format. Multiple brackets detected.")

            base_info, meta_str = data_str.split("[", 1)
            meta_str = meta_str.replace("]", "").strip()
            seen_keys = set()

            for item in meta_str.split():
                if "=" not in item:
                    raise ValueError(f"Error on line {line_index}: Invalid metadata syntax '{item}'. Expected key=value.")

                k, v = item.split("=", 1)

                if k in seen_keys:
                    raise ValueError(f"Error on line {line_index}: Duplicate metadata key '{k}' detected.")
                seen_keys.add(k)

                if not v.strip():
                    raise ValueError(f"Error on line {line_index}: Missing value for metadata '{k}'.")

                if k == "zone":
                    if v not in ["normal", "blocked", "restricted", "priority"]:
                        raise ValueError(f"Error on line {line_index}: Invalid zone type '{v}'.")
                    meta_dict["zone_type"] = v

                elif k == "color":
                    meta_dict["color"] = v

                elif k == "max_drones":
                    if is_start_or_end:
                        continue
                    try:
                        capacity = int(v)
                        if capacity <= 0:
                            raise ValueError
                        meta_dict["max_drones"] = capacity
                    except ValueError:
                        raise ValueError(f"Error on line {line_index}: 'max_drones' must be a positive integer.")
                else:
                    raise ValueError(f"Error on line {line_index}: Unknown metadata key '{k}' for zone.")
        else:
            base_info = data_str

        # 2. Parse Base Info (Name, X, Y)
        parts = base_info.split()
        if len(parts) != 3:
            raise ValueError(f"Error on line {line_index}: Invalid zone format. Expected '<name> <x> <y> [metadata]'.")

        name = parts[0]
        if "-" in name:
            raise ValueError(f"Error on line {line_index}: Zone names cannot contain dashes (-).")
        if name in graph.zones.keys():
            raise ValueError(f"Error on line {line_index}: Duplicate zone name '{name}'. Zone names must be unique.")

        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ValueError(f"Error on line {line_index}: Coordinates X and Y must be integers.")

        # 3. Check for overlapping coordinates
        for existing_zone in graph.zones.values():
            if existing_zone.x == x and existing_zone.y == y:
                raise ValueError(
                    f"Error on line {line_index}: Duplicate coordinates. "
                    f"Position ({x}, {y}) is already occupied by zone '{existing_zone.name}'."
                )

        return name, x, y, meta_dict


    def parse(self) -> tuple[Graph, int]:
        graph = Graph()
        nb_drones = 0

        for index, line in enumerate(self.lines):
            clean_line = line.split('#', 1)[0].strip()

            if not clean_line:
                continue

            if ":" not in clean_line:
                raise ValueError(f"Error on line {index + 1}: Invalid line format. Missing colon ':'.")

            keyword, data_str = clean_line.split(":", 1)
            keyword = keyword.strip()
            data_str = data_str.strip()

            if nb_drones == 0 and keyword != "nb_drones":
                raise ValueError(f"Error on line {index + 1}: The first valid line must define 'nb_drones'.")

            if keyword == "nb_drones":
                if nb_drones != 0:
                    raise ValueError(f"Error on line {index + 1}: Duplication error. 'nb_drones' is already defined.")
                try:
                    num = int(data_str)
                except ValueError:
                    raise ValueError(f"Error on line {index + 1}: Invalid input format. Expected a positive integer.")
                if num <= 0:
                    raise ValueError(f"Error on line {index + 1}: Invalid input. Number of drones must be greater than 0.")
                nb_drones = num

            elif keyword == "start_hub":
                if graph.start_zone is not None:
                    raise ValueError(f"Error on line {index + 1}: Duplication error. 'start_hub' is already defined.")

                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph, is_start_or_end=True)
                start_zone = Zone(
                    name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"]
                )
                graph.add_zone(start_zone, is_start=True)

            elif keyword == "end_hub":
                if graph.end_zone is not None:
                    raise ValueError(f"Error on line {index + 1}: Duplication error. 'end_hub' is already defined.")

                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph, is_start_or_end=True)
                end_zone = Zone(
                    name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"]
                )
                graph.add_zone(end_zone, is_end=True)

            elif keyword == "hub":
                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph)
                regular_zone = Zone(
                    name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"]
                )
                graph.add_zone(regular_zone)

            elif keyword == "connection":
                capacity = 1
                if "[" in data_str:
                    if data_str.count("[") > 1 or data_str.count("]") > 1:
                        raise ValueError(f"Error on line {index + 1}: Invalid metadata format in connection. Multiple brackets detected.")

                    base_info, meta_str = data_str.split("[", 1)
                    base_info = base_info.strip()
                    meta_str = meta_str.replace("]", "").strip()

                    seen_keys = set()
                    for item in meta_str.split():
                        if "=" not in item:
                            raise ValueError(f"Error on line {index + 1}: Invalid metadata syntax '{item}'.")

                        k, v = item.split("=", 1)

                        if k in seen_keys:
                            raise ValueError(f"Error on line {index + 1}: Duplicate metadata key '{k}' detected.")
                        seen_keys.add(k)

                        if k == "max_link_capacity":
                            try:
                                capacity = int(v)
                                if capacity <= 0:
                                    raise ValueError
                            except ValueError:
                                raise ValueError(f"Error on line {index + 1}: 'max_link_capacity' must be a positive integer.")
                        else:
                            raise ValueError(f"Error on line {index + 1}: Unknown metadata '{k}' for connection.")
                else:
                    base_info = data_str

                parts = base_info.split("-")
                if len(parts) != 2:
                    raise ValueError(f"Error on line {index + 1}: Invalid connection format. Expected '<zone1>-<zone2>'.")

                z1_name = parts[0].strip()
                z2_name = parts[1].strip()

                if z1_name not in graph.zones or z2_name not in graph.zones:
                    raise ValueError(f"Error on line {index + 1}: Unknown zone in connection '{z1_name}-{z2_name}'. Both zones must be defined first.")

                if z1_name == z2_name:
                    raise ValueError(f"Error on line {index + 1}: A zone cannot connect to itself ('{z1_name}-{z2_name}').")

                if graph.has_connection(z1_name, z2_name):
                    raise ValueError(f"Error on line {index + 1}: Duplicate connection between '{z1_name}' and '{z2_name}'.")

                connection_obj = Connection(z1_name, z2_name, capacity)
                graph.add_connection(connection_obj)

            else:
                raise ValueError(f"Error on line {index + 1}: Unknown keyword '{keyword}'.")

        # Hna kanderu l'validation f lkher bash nt2kdo bli start u end t-declarao
        if graph.start_zone is None:
            raise ValueError("Error: The map is missing a 'start_hub' zone. Exactly one start zone is required.")
        if graph.end_zone is None:
            raise ValueError("Error: The map is missing an 'end_hub' zone. Exactly one end zone is required.")

        return graph, nb_drones
