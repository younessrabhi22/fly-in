*This project has been created as part of the 42 curriculum by yrabhi.*

# Fly-in — Space-Time Drone Routing Simulation

## Description

Fly-in is a drone routing and simulation system that moves a fleet of drones
from a shared start zone to a shared end zone across a network of connected
zones, in the fewest possible simulation turns.

The map (zones, connections, zone types, and capacities) is loaded from a
custom text format. Each drone is routed independently through a space-time
pathfinding search that treats capacity constraints (zone occupancy, link
capacity, restricted-zone transit time) as first-class rules, not
after-the-fact checks — so the resulting schedule never violates them. The
simulation is fully object-oriented, statically typed, and does not rely on
any third-party graph library (no `networkx`, no `graphlib`): the graph,
search, and reservation logic are all implemented from scratch.

A Pygame-based visual interface plays the simulation back turn by turn, so
the routing decisions can be inspected visually instead of only as raw
`D<id>-<zone>` output lines.

## Instructions

**Requirements:** Python 3.10+, Pygame.

```bash
make install   # installs dependencies (pygame)
make run       # runs the simulation on a sample map
make debug     # runs the simulation under pdb
make lint      # runs flake8 and mypy
make clean     # removes __pycache__ / .mypy_cache
```

Or directly, without the Makefile:

```bash
pip install -r requirements.txt
python3 main.py maps/easy/01_linear_path.txt
```

Any map file that follows the format described in the subject (`nb_drones`,
`start_hub`, `end_hub`, `hub`, `connection` lines) can be passed as the
argument. Sample maps of increasing difficulty are provided under `maps/`.

Once the simulation finishes computing every drone's route, a window opens
showing the map and the drones' positions turn by turn — see
[Visual Representation](#visual-representation) below for the controls.

## Algorithm Choices and Implementation Strategy

**Parsing.** `MapParser` reads the map file line by line, validates every
zone, connection, and metadata block against the rules in the subject
(unique names, no dashes, positive integer capacities, valid zone types,
no duplicate connections, etc.), and builds a `Graph` of `Zone` and
`Connection` objects. Any malformed line stops the program with a message
naming the line and the exact problem.

**Pathfinding.** Each drone's route is computed by `Pathfinder.find_path()`,
a Dijkstra-style search over *(turn, zone)* states rather than zones alone.
Searching over time as well as space is what makes it possible to treat a
zone or connection as "busy" only during the specific turns it's actually
occupied, instead of for the whole simulation — which is what lets several
drones share the same map without colliding.

At every state, the search considers three kinds of moves: moving to a
neighboring zone, waiting in place, and (for restricted zones specifically)
a two-turn move during which the drone is "in transit" on the connection
and cannot be redirected or made to wait. Every candidate move is checked
against the zone's remaining capacity and the connection's remaining
capacity at the exact turn(s) it would use them, before it's added to the
search frontier.

Ties between equally-fast routes are broken by: (1) preferring priority
zones, as required by the subject; (2) a load-balancing heuristic that
prefers less-crowded zones, to spread drones across alternative paths
instead of funneling them through the same corridor; and (3) a strict
insertion-order counter as a final tiebreaker, so the search never depends
on incidental string/hash ordering.

**Multi-drone scheduling.** `SimulationEngine` plans drones one at a time,
in order. After each drone's path is found, every zone and connection it
will use — turn by turn — is booked into a shared reservation table before
the next drone searches. This turns "route N drones at once without
collisions" into a sequence of N single-drone searches, each aware of the
traffic already committed by the ones before it, which keeps the algorithm
simple to reason about while still respecting every capacity constraint
from the subject.

**Complexity.** Each single-drone search is a standard Dijkstra over
*(turn, zone)* states: `O(E log V)` in the size of the expanded space-time
graph, where the number of turns explored is bounded by a safety cap to
avoid runaway searches on unsolvable or heavily congested maps. Paths are
computed once per drone and not recomputed afterward — the reservation
tables are the only state carried between drones, so memory usage grows
with the number of turns and zones actually reserved, not with the number
of drones squared.

## Visual Representation

The `visualizer.py` module opens a Pygame window once every drone's route
has been computed, and renders:

- every zone as a circle, colored by its type (normal, restricted,
  priority, blocked), with the start zone in white and the end zone in red;
- every connection as a line between the zones it links;
- every drone as a small marker, positioned at its zone for a given turn,
  or at the midpoint of a connection while it is mid-transit through a
  restricted zone; drones sharing the same zone at the same turn are
  spread out in a small circle instead of overlapping, so none of them are
  hidden.

The window title bar shows the current turn out of the total. Playback is
controlled with the arrow keys: **RIGHT** advances one turn, **LEFT** goes
back one turn — this makes it possible to step through a specific conflict
or bottleneck at your own pace, which is more useful for inspecting a
routing decision than a fixed-speed autoplay would be. The window also
auto-scales the map to fit the screen, so the same code renders both a
6-zone easy map and the 40+-zone challenger map legibly.

## Resources

- Python `heapq` documentation — used for the priority queue in the
  pathfinding search.
- Python `typing` and `mypy` documentation — used to keep the project
  fully typed per the subject's constraints.
- Pygame documentation — used for the visual representation window,
  drawing primitives, and event/keyboard handling.
- Classic references on Dijkstra's algorithm and space-time / "cooperative
  pathfinding" search, used as background for treating time as part of the
  search state when routing multiple agents.

**AI usage:** AI assistance (Claude) was used throughout this project for:
reviewing and debugging the pathfinding and reservation logic (in
particular, catching a connection-capacity bug where the connection
capacity was checked and reserved on mismatched turns); discussing design
tradeoffs between simplicity and strict subject compliance for the
space-time search; iterating on the Pygame visualizer (auto-scaling to the
screen, spreading overlapping drones, fixing zone-label overlap); and
cleaning up `flake8`/`mypy` violations across the codebase without changing
program logic, which was verified by regression-testing every provided map
and several hand-written edge-case maps before and after each change. All
AI-suggested code was reviewed, tested, and understood before being kept.
