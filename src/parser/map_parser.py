from src.models.graph import Graph
from src.models.zone import Zone
from src.models.connection import Connection
import sys

class MapParser:
    def __init__(self, map_path: str) -> None:
        self.map_path = map_path
        self.lines = []
        try:
            with open(self.map_path, "r") as f:
                self.lines = f.readlines()
        except (FileNotFoundError, PermissionError) as e:
            raise ValueError(f"Could not read the map file: {e}")

    def _parse_zone_data(self, data_str: str, line_index: int, graph, is_start_or_end: bool = False) -> tuple:
        """
        Helper function to extract name, x, y, and metadata from any zone line.
        """
        meta_dict = {"zone_type": "normal", "color": None, "max_drones": 1}

        if "[" in data_str:
            if data_str.count("[") > 1 or data_str.count("]") > 1:
                print(f"Error on line {line_index}: Invalid metadata format. Multiple brackets detected.")
                sys.exit(1)

            base_info, meta_str = data_str.split("[", 1)
            meta_str = meta_str.replace("]", "").strip()

            while " =" in meta_str or "= " in meta_str:
                meta_str = meta_str.replace(" =", "=").replace("= ", "=")

            seen_keys = set()

            for item in meta_str.split():
                if "=" not in item:
                    print(f"Error on line {line_index}: Invalid metadata syntax '{item}'. Expected key=value.")
                    sys.exit(1)

                k, v = item.split("=", 1)

                if k in seen_keys:
                    print(f"Error on line {line_index}: Duplicate metadata key '{k}' detected.")
                    sys.exit(1)
                seen_keys.add(k)

                if not v.strip():
                    print(f"Error on line {line_index}: Missing value for metadata '{k}'.")
                    sys.exit(1)

                if k == "zone":
                    if v not in ["normal", "blocked", "restricted", "priority"]:
                        print(f"Error on line {line_index}: Invalid zone type '{v}'.")
                        sys.exit(1)

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
                        print(f"Error on line {line_index}: 'max_drones' must be a positive integer.")
                        sys.exit(1)
                else:
                    print(f"Error on line {line_index}: Unknown metadata key '{k}' for zone.")
                    sys.exit(1)
        else:
            base_info = data_str

        parts = base_info.split()
        if len(parts) != 3:
            print(f"Error on line {line_index}: Invalid zone format. Expected '<name> <x> <y> [metadata]'.")
            sys.exit(1)

        name = parts[0]
        if "-" in name:
            print(f"Error on line {line_index}: Zone names cannot contain dashes (-).")
            sys.exit(1)

        if name in graph.zones:
            print(f"Error on line {line_index}: Duplicate zone name '{name}'. Zone names must be unique.")
            sys.exit(1)

        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            print(f"Error on line {line_index}: Coordinates X and Y must be integers.")
            sys.exit(1)

        if x < 0 or y < 0:
            print(f"Error on line {line_index}: Invalid coordinates ({x}, {y}) for zone '{name}'. Coordinates must be positive or zero.")
            sys.exit(1)

        for existing_zone in graph.zones.values():
            if existing_zone.x == x and existing_zone.y == y:
                print(f"Error on line {line_index}: Duplicate coordinates. Position ({x}, {y}) is already occupied by zone '{existing_zone.name}'.")
                sys.exit(1)

        return name, x, y, meta_dict

    def parse(self) -> tuple[Graph, int]:

        graph = Graph()
        nb_drones = 0
        start_hub = False
        end_hub = False

        for line in self.lines:
            clean_line = line.split('#', 1)[0].strip()
            if not clean_line:
                continue

            if ":" in clean_line:
                keyword = clean_line.split(":", 1)[0].strip()
                if keyword == "start_hub":
                    start_hub = True
                elif keyword == "end_hub":
                    end_hub = True

        if not start_hub:
            print("Error: The map is missing a 'start_hub' zone. Exactly one start zone is required.")
            sys.exit(1)
        if not end_hub:
            print("Error: The map is missing an 'end_hub' zone. Exactly one end zone is required.")
            sys.exit(1)

        for index, line in enumerate(self.lines):

            clean_line = line.split('#', 1)[0].strip()

            if not clean_line:
                continue

            if ":" not in clean_line:
                print(f"Error on line {index + 1}: Invalid line format. Missing colon ':'.")
                sys.exit(1)

            keyword, data_str = clean_line.split(":", 1)
            keyword = keyword.strip()
            data_str = data_str.strip()

            if nb_drones == 0 and keyword != "nb_drones":
                print(f"Error on line {index + 1}: The first valid line must define 'nb_drones'.")
                sys.exit(1)

            if keyword == "nb_drones":
                if nb_drones != 0:
                    print(f"Error on line {index + 1}: Duplication error. 'nb_drones' is already defined.")
                    sys.exit(1)

                try:
                    num = int(data_str)
                except ValueError:
                    print(f"Error on line {index + 1}: Invalid input format. Expected a positive integer.")
                    sys.exit(1)

                if num <= 0:
                    print(f"Error on line {index + 1}: Invalid input. Number of drones must be greater than 0.")
                    sys.exit(1)
                nb_drones = num

            elif keyword == "start_hub":
                if graph.start_zone is not None:
                    print(f"Error on line {index + 1}: Duplication error. 'start_hub' is already defined.")
                    sys.exit(1)

                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph, is_start_or_end=True)
                start_zone = Zone(name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"])
                graph.add_zone(start_zone, is_start=True)

            elif keyword == "end_hub":
                if graph.end_zone is not None:
                    print(f"Error on line {index + 1}: Duplication error. 'end_hub' is already defined.")
                    sys.exit(1)

                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph, is_start_or_end=True)
                end_zone = Zone(name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"])
                graph.add_zone(end_zone, is_end=True)

            elif keyword == "hub":
                name, x, y, meta = self._parse_zone_data(data_str, index + 1, graph)
                regular_zone = Zone(name=name, x=x, y=y, zone_type=meta["zone_type"], color=meta["color"], max_drones=meta["max_drones"])
                graph.add_zone(regular_zone)

            elif keyword == "connection":
                capacity = 1

                if "[" in data_str:
                    if data_str.count("[") > 1 or data_str.count("]") > 1:
                        print(f"Error on line {index + 1}: Invalid metadata format in connection. Multiple brackets detected.")
                        sys.exit(1)
                    base_info, meta_str = data_str.split("[", 1)
                    base_info = base_info.strip()
                    meta_str = meta_str.replace("]", "").strip()

                    while " =" in meta_str or "= " in meta_str:
                        meta_str = meta_str.replace(" =", "=").replace("= ", "=")

                    seen_keys = set()

                    for item in meta_str.split():
                        if "=" not in item:
                            print(f"Error on line {index + 1}: Invalid metadata syntax '{item}'.")
                            sys.exit(1)

                        k, v = item.split("=", 1)

                        if k in seen_keys:
                            print(f"Error on line {index + 1}: Duplicate metadata key '{k}' detected.")
                            sys.exit(1)
                        seen_keys.add(k)

                        if k == "max_link_capacity":
                            try:
                                capacity = int(v)
                                if capacity <= 0:
                                    raise ValueError
                            except ValueError:
                                print(f"Error on line {index + 1}: 'max_link_capacity' must be a positive integer.")
                                sys.exit(1)
                        else:
                            print(f"Error on line {index + 1}: Unknown metadata '{k}' for connection.")
                            sys.exit(1)
                else:
                    base_info = data_str

                parts = base_info.split("-")

                if len(parts) != 2:
                    print(f"Error on line {index + 1}: Invalid connection format. Expected '<zone1>-<zone2>'.")
                    sys.exit(1)

                z1_name = parts[0].strip()
                z2_name = parts[1].strip()

                if z1_name not in graph.zones or z2_name not in graph.zones:
                    print(f"Error on line {index + 1}: Unknown zone in connection '{z1_name}-{z2_name}'. Both zones must be defined first.")
                    sys.exit(1)

                if z1_name == z2_name:
                    print(f"Error on line {index + 1}: A zone cannot connect to itself ('{z1_name}-{z2_name}').")
                    sys.exit(1)

                if graph.has_connection(z1_name, z2_name):
                    print(f"Error on line {index + 1}: Duplicate connection between '{z1_name}' and '{z2_name}'.")
                    sys.exit(1)

                connection_obj = Connection(z1_name, z2_name, capacity)
                graph.add_connection(connection_obj)

            else:
                print(f"Error on line {index + 1}: Unknown keyword '{keyword}'.")
                sys.exit(1)

        return graph, nb_drones
