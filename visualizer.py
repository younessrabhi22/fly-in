import math
import pygame


def visualize_simulation(engine):
    """Launches a Pygame window that plays the drone simulation automatically."""
    pygame.init()

    zones = engine.graph.zones
    if not zones:
        print("Error: No zones to visualize.")
        pygame.quit()
        return

    SCALE = 140
    MARGIN = 100
    ZONE_RADIUS = 18

    min_x = min(z.x for z in zones.values())
    max_x = max(z.x for z in zones.values())
    min_y = min(z.y for z in zones.values())
    max_y = max(z.y for z in zones.values())

    map_units_x = max(1, max_x - min_x)
    map_units_y = max(1, max_y - min_y)


    screen_info = pygame.display.Info()
    max_width = screen_info.current_w - 100
    max_height = screen_info.current_h - 150
    max_scale_x = (max_width - 2 * MARGIN) / map_units_x
    max_scale_y = (max_height - 2 * MARGIN) / map_units_y
    SCALE = max(20, int(min(SCALE, max_scale_x, max_scale_y)))

    WIDTH = max(500, map_units_x * SCALE + 2 * MARGIN)
    HEIGHT = max(400, map_units_y * SCALE + 2 * MARGIN)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space-Time A* Drone Simulation")

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    BLUE = (100, 150, 255)
    CYAN = (80, 220, 220)
    RED = (255, 50, 50)
    GREEN = (50, 200, 50)
    DRONE_COLOR = (255, 165, 0)

    font = pygame.font.SysFont(None, 30)

    label_font_size = max(10, min(18, SCALE // 7))
    small_font = pygame.font.SysFont(None, label_font_size)

    max_turn = max([path[-1][0] for path in engine.all_paths.values() if path] or [0])
    current_turn = 0

    def get_screen_pos(zone_name):
        """Kat7owel (x,y) dyal l'fichier l (x,y) dyal Pygame f l'écran."""
        z = zones[zone_name]
        x = int(MARGIN + (z.x - min_x) * SCALE)
        y = int(MARGIN + (z.y - min_y) * SCALE)
        return (x, y)

    zones_by_x = sorted(zones.keys(), key=lambda name: get_screen_pos(name)[0])
    stagger = {name: (i % 2) for i, name in enumerate(zones_by_x)}

    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and current_turn < max_turn:
                    current_turn += 1
                elif event.key == pygame.K_LEFT and current_turn > 0:
                    current_turn -= 1

        screen.fill(BLACK)


        drawn_conns = set()
        for z_name, conns in engine.graph.connections_map.items():
            pos_a = get_screen_pos(z_name)
            for c in conns:
                other = c.zone_to if c.zone_from == z_name else c.zone_from
                pair = tuple(sorted([z_name, other]))

                if pair not in drawn_conns:
                    pos_b = get_screen_pos(other)
                    pygame.draw.line(screen, GRAY, pos_a, pos_b, 3)
                    drawn_conns.add(pair)

        for z_name, z in zones.items():
            pos = get_screen_pos(z_name)

            if z.zone_type == "restricted":
                color = BLUE
            elif z.zone_type == "priority":
                color = CYAN
            elif z.zone_type == "blocked":
                color = GRAY
            else:
                color = GREEN

            if z_name == engine.graph.start.name:
                color = WHITE
            if z_name == engine.graph.end.name:
                color = RED

            pygame.draw.circle(screen, color, pos, ZONE_RADIUS)

            label = small_font.render(z_name, True, WHITE)
            extra_gap = stagger[z_name] * (label_font_size + 2)
            label_y = pos[1] + ZONE_RADIUS + 4 + extra_gap
            screen.blit(label, (pos[0] - label.get_width() // 2, label_y))


        drones_by_position = {}
        for drone_id, path in engine.all_paths.items():
            location = engine.get_location_at_time(path, current_turn)
            if location is None:
                continue

            if "-" in location:
                z1, z2 = location.split("-")
                p1, p2 = get_screen_pos(z1), get_screen_pos(z2)
                pos = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            else:
                pos = get_screen_pos(location)

            drones_by_position.setdefault(pos, []).append(drone_id)

        SPREAD_RADIUS = 16
        for pos, drone_ids in drones_by_position.items():
            count = len(drone_ids)
            for i, drone_id in enumerate(drone_ids):
                if count == 1:
                    draw_pos = pos
                else:
                    angle = 2 * math.pi * i / count
                    draw_pos = (
                        pos[0] + int(SPREAD_RADIUS * math.cos(angle)),
                        pos[1] + int(SPREAD_RADIUS * math.sin(angle)),
                    )

                pygame.draw.circle(screen, DRONE_COLOR, draw_pos, 12)
                d_label = small_font.render(f"D{drone_id}", True, BLACK)
                screen.blit(d_label, (draw_pos[0] - 10, draw_pos[1] - 8))

        text = font.render(f"Turn: {current_turn} / {max_turn}", True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()

    pygame.quit()
