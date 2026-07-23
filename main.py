import os
import sys
from src.parser.map_parser import MapParser
from src.engine import SimulationEngine
from visualizer import visualize_simulation

def main():


    map_path: str = None
    try:
        map_path = sys.argv[1]
    except IndexError:
        print("Error: No argument provided!")
        sys.exit(1)

    if not os.path.isfile(map_path):
        print(f"Error: The file '{map_path}' does not exist or is not a valid file.", file=sys.stderr)
        sys.exit(1)

    map_parser = MapParser(map_path)
    graph, nb_drones = map_parser.parse()

    engine = SimulationEngine(graph, nb_drones)
    success = engine.run()

    if success:
        visualize_simulation(engine)


if __name__ == "__main__":
    main()
