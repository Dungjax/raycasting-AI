"""Pygame game loop and controls."""
from math import atan2, cos, hypot, sin
import pygame
from .config import *
from .entities import Enemy, Player, normalize_angle
from .renderer import Renderer
from .world import World

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Raycasting AI 2.0 — DDA / A*")
        self.window=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.RESIZABLE)
        self.clock=pygame.time.Clock()
        self.world=World(); self.player=Player()
        self.renderer=Renderer(RENDER_WIDTH,RENDER_HEIGHT)
        self.enemies=[Enemy(15.5,2.5),Enemy(17.5,12.5),Enemy(4.5,13.5)]
        self.ammo=WEAPON_MAGAZINE; self.cooldown=0.; self.reload_timer=0.
        self.running=True; self.captured=True
        pygame.event.set_grab(True); pygame.mouse.set_visible(False)

    def fire(self):
        if self.reload_timer>0 or self.cooldown>0 or self.ammo<=0: return
        self.cooldown=WEAPON_COOLDOWN; self.ammo-=1
        wall=self.world.cast_ray(self.player.x,self.player.y,self.player.angle,WEAPON_RANGE)
        best=min(WEAPON_RANGE,wall.distance); target=None
        for enemy in self.enemies:
            if not enemy.alive: continue
            dx,dy=enemy.x-self.player.x,enemy.y-self.player.y
            distance=hypot(dx,dy); rel=normalize_angle(atan2(dy,dx)-self.player.angle)
            depth=distance*cos(rel)
            if 0<depth<best and abs(distance*sin(rel))<.34:
                best,target=depth,enemy
        if target: target.take_damage(WEAPON_DAMAGE)

    def events(self):
        for e in pygame.event.get():
            if e.type==pygame.QUIT: self.running=False
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: self.running=False
                elif e.key==pygame.K_r and self.ammo<WEAPON_MAGAZINE and self.reload_timer<=0:
                    self.reload_timer=WEAPON_RELOAD_TIME
                elif e.key==pygame.K_TAB:
                    self.captured=not self.captured
                    pygame.event.set_grab(self.captured); pygame.mouse.set_visible(not self.captured)
            elif e.type==pygame.MOUSEMOTION and self.captured:
                self.player.angle+=e.rel[0]*MOUSE_SENSITIVITY
            elif e.type==pygame.MOUSEBUTTONDOWN and e.button==1: self.fire()
            elif e.type==pygame.VIDEORESIZE:
                self.window=pygame.display.set_mode(e.size,pygame.RESIZABLE)

    def update(self,dt):
        keys=pygame.key.get_pressed()
        forward=float(keys[pygame.K_w] or keys[pygame.K_UP])-float(keys[pygame.K_s] or keys[pygame.K_DOWN])
        strafe=float(keys[pygame.K_d])-float(keys[pygame.K_a])
        if keys[pygame.K_q]: self.player.angle-=1.8*dt
        if keys[pygame.K_e]: self.player.angle+=1.8*dt
        self.player.move(forward,strafe,dt,self.world,keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        self.player.update_timers(dt)
        self.cooldown=max(0,self.cooldown-dt)
        if self.reload_timer>0:
            self.reload_timer=max(0,self.reload_timer-dt)
            if self.reload_timer==0: self.ammo=WEAPON_MAGAZINE
        if pygame.mouse.get_pressed(3)[0]: self.fire()
        for enemy in self.enemies: enemy.update(dt,self.world,self.player)
        self.enemies=[e for e in self.enemies if e.alive]

    def run(self):
        try:
            while self.running:
                dt=min(self.clock.tick(TARGET_FPS)/1000,0.05)
                self.events(); self.update(dt)
                frame=self.renderer.render(self.world,self.player,self.enemies)
                self.renderer.draw_hud(self.world,self.player,self.enemies,self.ammo,self.reload_timer>0)
                self.window.blit(pygame.transform.scale(frame,self.window.get_size()),(0,0))
                if self.player.health<=0 or not self.enemies:
                    msg="YOU WERE DOWNED — ESC TO EXIT" if self.player.health<=0 else "AREA CLEARED"
                    font=pygame.font.Font(None,64)
                    label=font.render(msg,True,(255,225,210))
                    self.window.blit(label,label.get_rect(center=self.window.get_rect().center))
                pygame.display.flip()
        finally: pygame.quit()
