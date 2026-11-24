"""DDA wall renderer, depth-tested billboards and mobile HUD."""
from math import atan2, cos, hypot
import pygame
from .config import FOV, MAX_RAY_DISTANCE
from .entities import normalize_angle

WALL_COLORS = {
    1: (142, 94, 68),
    2: (85, 126, 150),
    3: (138, 132, 82),
    4: (100, 132, 94),
}


class Renderer:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.horizon = height // 2
        self.surface = pygame.Surface((width, height)).convert()
        self.depth = [MAX_RAY_DISTANCE] * width
        self.enemy = self._enemy_sprite()

    @staticmethod
    def _enemy_sprite():
        sprite = pygame.Surface((64, 88), pygame.SRCALPHA)
        pygame.draw.ellipse(sprite, (90, 35, 35), (9, 28, 46, 50))
        pygame.draw.ellipse(sprite, (155, 65, 55), (15, 10, 34, 32))
        for x in (25, 39):
            pygame.draw.circle(sprite, (255, 215, 110), (x, 24), 4)
        pygame.draw.line(sprite, (35, 15, 15), (24, 48), (40, 48), 3)
        pygame.draw.line(sprite, (65, 25, 20), (19, 57), (12, 78), 6)
        pygame.draw.line(sprite, (65, 25, 20), (45, 57), (52, 78), 6)
        return sprite

    def render(self, world, player, enemies):
        self.surface.fill((27, 37, 54), (0, 0, self.width, self.horizon))
        pygame.draw.rect(
            self.surface, (42, 39, 35),
            (0, self.horizon, self.width, self.height - self.horizon)
        )

        for column in range(self.width):
            camera_x = 2 * column / self.width - 1
            angle = player.angle + camera_x * FOV / 2
            hit = world.cast_ray(player.x, player.y, angle, MAX_RAY_DISTANCE)
            depth = max(0.035, hit.distance * cos(angle - player.angle))
            self.depth[column] = depth

            wall_height = min(self.height * 5, int(self.height * 0.92 / depth))
            top = max(0, self.horizon - wall_height // 2)
            bottom = min(self.height, self.horizon + wall_height // 2)
            base = WALL_COLORS.get(hit.tile, WALL_COLORS[1])
            fog = max(0.22, 1 - depth / MAX_RAY_DISTANCE * 0.78)
            shade = fog * (0.76 if hit.side else 1.0)
            if int(hit.wall_x * 8) % 4 == 0:
                shade *= 0.68
            color = tuple(int(channel * shade) for channel in base)
            self.surface.fill(color, (column, top, 1, max(1, bottom - top)))
            joint = tuple(int(channel * 0.62) for channel in color)
            for section in (1, 2, 3):
                y = top + (bottom - top) * section // 4
                if 0 <= y < self.height:
                    self.surface.set_at((column, y), joint)

        visible = []
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx, dy = enemy.x - player.x, enemy.y - player.y
            distance = hypot(dx, dy)
            relative = normalize_angle(atan2(dy, dx) - player.angle)
            if distance > 0.12 and abs(relative) < FOV * 0.62:
                visible.append((distance, relative, enemy))

        # Paint far billboards first. Per-column wall depth clips them behind walls.
        for distance, relative, enemy in sorted(visible, reverse=True, key=lambda item: item[0]):
            screen_x = int((0.5 + relative / FOV) * self.width)
            sprite_height = min(self.height * 2, int(self.height * 0.78 / max(0.1, distance)))
            sprite_width = max(1, int(sprite_height * 64 / 88))
            scaled = pygame.transform.scale(self.enemy, (sprite_width, sprite_height))
            if enemy.hit_flash > 0:
                scaled.fill((95, 25, 25, 0), special_flags=pygame.BLEND_RGBA_ADD)
            left = screen_x - sprite_width // 2
            top = self.horizon - sprite_height // 2
            for x in range(max(0, left), min(self.width, left + sprite_width)):
                if distance < self.depth[x]:
                    self.surface.blit(scaled, (x, top), (x - left, 0, 1, sprite_height))
        return self.surface

    def draw_hud(self, world, player, enemies, ammo, reloading):
        font = pygame.font.Font(None, 22)
        small = pygame.font.Font(None, 17)

        pygame.draw.rect(self.surface, (10, 12, 16), (10, 10, 142, 48), border_radius=5)
        pygame.draw.rect(self.surface, (70, 72, 78), (18, 22, 112, 12), border_radius=4)
        health_width = int(108 * player.health / max(1, player.max_health))
        if health_width:
            pygame.draw.rect(
                self.surface, (180, 55, 52), (20, 24, health_width, 8), border_radius=3
            )
        self.surface.blit(small.render(f"HP {player.health:03d}", True, (245, 240, 230)), (18, 39))
        self.surface.blit(
            font.render("RELOAD..." if reloading else f"AMMO {ammo:02d}", True, (235, 225, 190)),
            (self.width - 112, 15)
        )
        self.surface.blit(
            small.render(f"HOSTILES {len(enemies):02d}", True, (225, 170, 150)),
            (self.width - 112, 38)
        )

        center_x, center_y = self.width // 2, self.height // 2
        pygame.draw.line(self.surface, (235, 235, 220), (center_x - 7, center_y), (center_x - 2, center_y))
        pygame.draw.line(self.surface, (235, 235, 220), (center_x + 2, center_y), (center_x + 7, center_y))

        # Keep the minimap in the upper-right so it does not overlap touch buttons.
        map_x, map_y = self.width - 96, 70
        pygame.draw.rect(
            self.surface, (9, 12, 16),
            (map_x - 4, map_y - 4, world.width * 4 + 8, world.height * 4 + 8)
        )
        for y, row in enumerate(world.grid):
            for x, tile in enumerate(row):
                if tile:
                    pygame.draw.rect(self.surface, (84, 88, 94), (map_x + x * 4, map_y + y * 4, 4, 4))
        for enemy in enemies:
            if enemy.alive:
                pygame.draw.circle(
                    self.surface, (220, 70, 58),
                    (map_x + int(enemy.x * 4), map_y + int(enemy.y * 4)), 2
                )
        pygame.draw.circle(
            self.surface, (90, 220, 130),
            (map_x + int(player.x * 4), map_y + int(player.y * 4)), 3
        )

        if player.damage_flash > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((180, 15, 20, int(90 * player.damage_flash / 0.18)))
            self.surface.blit(overlay, (0, 0))

    def draw_touch_controls(
        self, fingers, joystick_center, joystick_radius,
        touch_forward, touch_strafe, touch_fire, touch_sprint
    ):
        """Overlay virtual controls; SDL finger events work alongside keyboard input."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        font = pygame.font.Font(None, 15)
        button_font = pygame.font.Font(None, 18)

        cx, cy = int(joystick_center[0]), int(joystick_center[1])
        pygame.draw.circle(overlay, (210, 220, 235, 46), (cx, cy), int(joystick_radius), 2)
        pygame.draw.circle(overlay, (210, 220, 235, 35), (cx, cy), int(joystick_radius * 0.55), 1)
        knob_x = int(cx + touch_strafe * joystick_radius * 0.72)
        knob_y = int(cy - touch_forward * joystick_radius * 0.72)
        pygame.draw.circle(overlay, (190, 210, 235, 105), (knob_x, knob_y), 16)

        fire_center = (self.width - 48, self.height - 56)
        reload_center = (self.width - 126, self.height - 42)
        sprint_center = (self.width - 54, self.height - 145)
        pygame.draw.circle(
            overlay, (230, 85, 65, 145 if touch_fire else 72), fire_center, 31
        )
        pygame.draw.circle(
            overlay, (210, 220, 235, 100), reload_center, 22, 2
        )
        pygame.draw.circle(
            overlay, (210, 220, 235, 125 if touch_sprint else 65), sprint_center, 21, 2
        )

        def centered(text, center, color=(245, 245, 245)):
            label = button_font.render(text, True, color)
            overlay.blit(label, label.get_rect(center=center))

        centered("FIRE", fire_center)
        centered("R", reload_center)
        centered("RUN", sprint_center)
        overlay.blit(font.render("MOVE", True, (220, 225, 235)), (cx - 17, cy + 53))
        overlay.blit(
            font.render("DRAG RIGHT TO LOOK", True, (220, 225, 235)),
            (self.width // 2 - 74, self.height - 18)
        )

        self.surface.blit(overlay, (0, 0))
