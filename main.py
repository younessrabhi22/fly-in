import os
import sys
from map_parser import MapParser
from engine import SimulationEngine
from visualizer import visualize_simulation


def main() -> None:

    if len(sys.argv) < 2:
        print("Error: No argument provided!", file=sys.stderr)
        sys.exit(1)

    map_path: str = sys.argv[1]

    if not os.path.isfile(map_path):
        print(
            f"Error: The file '{map_path}' does not exist or is not a valid file."
        )
        sys.exit(1)

    try:
        map_parser = MapParser(map_path)
        graph, nb_drones = map_parser.parse()
    except ValueError as e:
        print(f"{e}")
        sys.exit(1)

    engine = SimulationEngine(graph, nb_drones)
    success = engine.run()

    if success:
        visualize_simulation(engine)


if __name__ == "__main__":
    main()
