import argparse
import os
import sys
from src.parser.map_parser import MapParser

def main() -> None:

    parser = argparse.ArgumentParser(
        description="Fly-in: Drone Routing Simulation",
    )

    parser.add_argument(
        "map_file",
        type=str,
        help="Path to the map file (.map or .txt)"
    )

    args = parser.parse_args()
    map_path = args.map_file

    if not os.path.isfile(map_path):
        print(f"Error: The file '{map_path}' does not exist or is not a valid file.", file=sys.stderr)
        sys.exit(1)

    map_parser = MapParser(map_path)




if __name__ == "__main__":
    main()
