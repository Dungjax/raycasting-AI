"""Pygame game loop with desktop and Android touch controls."""
import os
import sys
from math import atan2, cos, hypot, sin, tau
import pygame
from .config import *
from .entities import Enemy, Player, normalize_angle
from .renderer import Renderer
from .world import World


def running_on_android():
    # Android/Pydroid environments do not all expose the same sys.platform value.
    return (
        sys.platform == "android"
        or any(name in os.environ for name in (
            "ANDROID_ARGUMENT", "ANDROID_ROOT", "ANDROID_DATA", "ANDROID_STORAGE"
        ))
        or os.path.isdir("/system/bin")
    )


class Game:
    def __init__(self):
        pygame.init()
        self.mobile = running_on_android()
        self.target_fps = MOBILE_TARGET_FPS if self.mobile else TARGET_FPS
        pygame.display.set_caption("Raycasting AI 2.1 — Touch / DDA / A*")

        flags = pygame.FULLSCREEN if self.mobile else pygame.RESIZABLE
        try:
            self.window = (
                pygame.display.set_mode((0, 0), flags)
                if self.mobile else pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
            )
        except pygame.error:
            self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)

        self.clock = pygame.time.Clock()
        self.world = World()
        self.player = Player()

        # Match the internal render target to the device aspect ratio. This avoids
        # stretching round buttons into ovals on extra-wide phone screens.
        display_width, display_height = self.window.get_size()
        if self.mobile and display_width > 0:
            render_height = max(180, round(RENDER_WIDTH * display_height / display_width))
        else:
            render_height = RENDER_HEIGHT
        self.renderer = Renderer(RENDER_WIDTH, render_height)
        self.enemies = [Enemy(15.5, 2.5), Enemy(17.5, 12.5), Enemy(4.5, 13.5)]

        self.ammo = WEAPON_MAGAZINE
        self.cooldown = 0.0
        self.reload_timer = 0.0
        self.running = True

        # SDL finger IDs let a player move, aim and fire with different fingers.
        self.fingers = {}
        self.joystick_center = (self.renderer.width * 0.16, self.renderer.height * 0.79)
        self.joystick_radius = self.renderer.height * 0.125
        self.touch_forward = 0.0
        self.touch_strafe = 0.0
        self.touch_sprint = False
        self.touch_fire = False

        self.captured = not self.mobile
        if not self.mobile:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(False)

    @staticmethod
    def _inside_button(x, y, center, radius):
        return (x - center[0]) ** 2 + (y - center[1]) ** 2 <= radius ** 2

    def _touch_down(self, event):
        x = event.x * self.renderer.width
        y = event.y * self.renderer.height
        finger_id = event.finger_id

        fire_center = (self.renderer.width - 48, self.renderer.height - 56)
        reload_center = (self.renderer.width - 126, self.renderer.height - 42)
        sprint_center = (self.renderer.width - 54, self.renderer.height - 145)

        if self._inside_button(x, y, fire_center, 34):
            kind = "fire"
            self.touch_fire = True
        elif self._inside_button(x, y, reload_center, 25):
            kind = "reload"
            if self.ammo < WEAPON_MAGAZINE and self.reload_timer <= 0:
                self.reload_timer = WEAPON_RELOAD_TIME
        elif self._inside_button(x, y, sprint_center, 25):
            kind = "sprint"
            self.touch_sprint = True
        elif x < self.renderer.width * 0.46:
            kind = "move"
        else:
            kind = "look"

        self.fingers[finger_id] = {"kind": kind, "x": x, "y": y}
        if kind == "move":
            self._update_joystick(x, y)

    def _update_joystick(self, x, y):
        cx, cy = self.joystick_center
        radius = self.joystick_radius
        dx = max(-1.0, min(1.0, (x - cx) / radius))
        dy = max(-1.0, min(1.0, (y - cy) / radius))
        if hypot(dx, dy) < 0.13:
            dx = dy = 0.0
        self.touch_strafe = dx
        self.touch_forward = -dy

    def _touch_motion(self, event):
        state = self.fingers.get(event.finger_id)
        if state is None:
            return
        x = event.x * self.renderer.width
        y = event.y * self.renderer.height

        if state["kind"] == "move":
            self._update_joystick(x, y)
        elif state["kind"] == "look":
            delta_x = x - state["x"]
            self.player.angle = (self.player.angle + delta_x * 0.006) % tau

        state["x"], state["y"] = x, y

    def _touch_up(self, event):
        state = self.fingers.pop(event.finger_id, None)
        if state is None:
            return
        if state["kind"] == "move":
            self.touch_forward = self.touch_strafe = 0.0
        elif state["kind"] == "fire":
            self.touch_fire = any(item["kind"] == "fire" for item in self.fingers.values())
        elif state["kind"] == "sprint":
            self.touch_sprint = any(item["kind"] == "sprint" for item in self.fingers.values())

    def fire(self):
        if self.reload_timer > 0 or self.cooldown > 0 or self.ammo <= 0:
            return
        self.cooldown = WEAPON_COOLDOWN
        self.ammo -= 1

        wall = self.world.cast_ray(
            self.player.x, self.player.y, self.player.angle, WEAPON_RANGE
        )
        best = min(WEAPON_RANGE, wall.distance)
        target = None
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx, dy = enemy.x - self.player.x, enemy.y - self.player.y
            distance = hypot(dx, dy)
            rel = normalize_angle(atan2(dy, dx) - self.player.angle)
            depth = distance * cos(rel)
            if 0 < depth < best and abs(distance * sin(rel)) < 0.34:
                best, target = depth, enemy
        if target is not None:
            target.take_damage(WEAPON_DAMAGE)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    if self.ammo < WEAPON_MAGAZINE and self.reload_timer <= 0:
                        self.reload_timer = WEAPON_RELOAD_TIME
                elif event.key == pygame.K_TAB and not self.mobile:
                    self.captured = not self.captured
                    pygame.event.set_grab(self.captured)
                    pygame.mouse.set_visible(not self.captured)
            elif event.type == pygame.FINGERDOWN:
                self._touch_down(event)
            elif event.type == pygame.FINGERMOTION:
                self._touch_motion(event)
            elif event.type == pygame.FINGERUP:
                self._touch_up(event)
            elif event.type == pygame.MOUSEMOTION and self.captured:
                self.player.angle += event.rel[0] * MOUSE_SENSITIVITY
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.mobile:
                self.fire()
            elif event.type == pygame.VIDEORESIZE and not self.mobile:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)

    def update(self, dt):
        keys = pygame.key.get_pressed()
        keyboard_forward = float(keys[pygame.K_w] or keys[pygame.K_UP]) - float(
            keys[pygame.K_s] or keys[pygame.K_DOWN]
        )
        keyboard_strafe = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
        forward = max(-1.0, min(1.0, keyboard_forward + self.touch_forward))
        strafe = max(-1.0, min(1.0, keyboard_strafe + self.touch_strafe))

        if keys[pygame.K_q]:
            self.player.angle -= 1.8 * dt
        if keys[pygame.K_e]:
            self.player.angle += 1.8 * dt

        sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or self.touch_sprint
        self.player.move(forward, strafe, dt, self.world, sprint)
        self.player.update_timers(dt)

        self.cooldown = max(0.0, self.cooldown - dt)
        if self.reload_timer > 0:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer == 0:
                self.ammo = WEAPON_MAGAZINE

        if self.touch_fire or (not self.mobile and pygame.mouse.get_pressed(3)[0]):
            self.fire()

        for enemy in self.enemies:
            enemy.update(dt, self.world, self.player)
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(self.target_fps) / 1000.0, 0.05)
                self.events()
                self.update(dt)

                frame = self.renderer.render(self.world, self.player, self.enemies)
                self.renderer.draw_hud(
                    self.world, self.player, self.enemies,
                    self.ammo, self.reload_timer > 0
                )
                self.renderer.draw_touch_controls(
                    self.fingers, self.joystick_center,
                    self.joystick_radius, self.touch_forward,
                    self.touch_strafe, self.touch_fire, self.touch_sprint
                )
                self.window.blit(
                    pygame.transform.scale(frame, self.window.get_size()), (0, 0)
                )

                if self.player.health <= 0 or not self.enemies:
                    message = (
                        "YOU WERE DOWNED — BACK TO EXIT"
                        if self.player.health <= 0 else "AREA CLEARED"
                    )
                    font = pygame.font.Font(None, 64)
                    label = font.render(message, True, (255, 225, 210))
                    self.window.blit(label, label.get_rect(center=self.window.get_rect().center))

                pygame.display.flip()
        finally:
            pygame.quit()
