import arcade

class DroneVisualizer(arcade.Window):
    def __init__(self, engine):
        self.engine = engine
        self.zones = engine.graph.zones

        xs = [z.x for z in self.zones.values()]
        ys = [z.y for z in self.zones.values()]
        self.min_x, self.min_y = min(xs), min(ys)

        map_w = max(1, max(xs) - self.min_x)
        map_h = max(1, max(ys) - self.min_y)
        screen_w, screen_h = arcade.get_display_size()

        x_pixels_per_unit = (screen_w - 200) / map_w
        y_pixels_per_unit = (screen_h - 200) / map_h

        self.pixels_per_unit = int(min(120, x_pixels_per_unit, y_pixels_per_unit))
        self.pixels_per_unit = max(60, self.pixels_per_unit)

        win_width = min(screen_w, int(map_w * self.pixels_per_unit) + 200)
        win_height = min(screen_h, int(map_h * self.pixels_per_unit) + 200)
        super().__init__(win_width, win_height, "Space-Time Dijkstra Drone Simulation")

        self.turn = 0
        self.max_turn = max((path[-1][0] for path in engine.all_paths.values() if path), default=0)
        self.background_color = arcade.color.BLACK

    def get_zone_color(self, zone_name, zone):
        """Returns the color dynamically based on the zone.color attribute."""

        color_map = {
            "orange": arcade.color.ORANGE,
            "purple": arcade.color.PURPLE,
            "yellow": arcade.color.YELLOW,
            "lime": arcade.color.LIME_GREEN,
            "magenta": arcade.color.MAGENTA,
            "gold": arcade.color.GOLD,
            "brown": arcade.color.BROWN,
            "maroon": arcade.color.MAROON,
            "darkred": arcade.color.DARK_RED,
            "crimson": arcade.color.CRIMSON,
            "blue": arcade.color.BLUE,
            "cyan": arcade.color.CYAN,
            "gray": arcade.color.GRAY,
            "green": arcade.color.GREEN,
            "red": arcade.color.RED,
            "white": arcade.color.WHITE
        }

        zone_color_name = str(getattr(zone, 'color', 'gray')).lower()
        return color_map.get(zone_color_name, arcade.color.GRAY)

    def get_pos(self, zone_name):
        z = self.zones[zone_name]
        return (100 + (z.x - self.min_x) * self.pixels_per_unit,
                self.height - 100 - (z.y - self.min_y) * self.pixels_per_unit)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.RIGHT and self.turn < self.max_turn:
            self.turn += 1
        elif key == arcade.key.LEFT and self.turn > 0:
            self.turn -= 1

    def on_draw(self):
        self.clear()

        # Draw edges
        for z_name, conns in self.engine.graph.connections_map.items():
            for c in conns:
                x1, y1 = self.get_pos(z_name)
                x2, y2 = self.get_pos(c.zone_to)
                arcade.draw_line(x1, y1, x2, y2, arcade.color.GRAY, 3)

        # Draw zones using the dynamic color function
        for index, (z_name, zone) in enumerate(self.zones.items()):
            x, y = self.get_pos(z_name)

            # Fetch the color from our new function
            color = self.get_zone_color(z_name, zone)
            arcade.draw_circle_filled(x, y, 20, color)

            y_offset = 32 if index % 2 == 0 else 44
            arcade.draw_text(z_name, x, y - y_offset, arcade.color.WHITE, 8, anchor_x="center")

        # Draw drones
        for drone_id, path in self.engine.all_paths.items():
            loc = self.engine.get_location_at_time(path, self.turn)

            if not loc: continue

            if "-" in loc:
                p1, p2 = self.get_pos(loc.split("-")[0]), self.get_pos(loc.split("-")[1])
                dx, dy = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            else:
                dx, dy = self.get_pos(loc)

            arcade.draw_circle_filled(dx, dy, 12, arcade.color.ORANGE)
            arcade.draw_text(f"D{drone_id}", dx, dy, arcade.color.BLACK, 10, anchor_x="center", anchor_y="center")
        # Draw turn counter

        arcade.draw_text(f"Turn: {self.turn} / {self.max_turn}", 20, self.height - 30, arcade.color.WHITE, 16)

def visualize_simulation(engine):
    DroneVisualizer(engine)
    arcade.run()

