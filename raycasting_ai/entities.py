"""Player and enemy simulation, independent from Pygame."""
from dataclasses import dataclass, field
from math import cos, hypot, pi, sin
from .config import *

def normalize_angle(a):
    return (a+pi)%(2*pi)-pi

@dataclass(slots=True)
class Player:
    x: float=2.5
    y: float=2.5
    angle: float=0.0
    health: int=100
    max_health: int=100
    damage_flash: float=0.0

    def move(self, forward, strafe, dt, world, sprint=False):
        length=hypot(forward,strafe)
        if length>1: forward/=length; strafe/=length
        speed=PLAYER_MOVE_SPEED*(PLAYER_SPRINT_MULTIPLIER if sprint else 1)
        dx=(cos(self.angle)*forward-sin(self.angle)*strafe)*speed*dt
        dy=(sin(self.angle)*forward+cos(self.angle)*strafe)*speed*dt
        self.x,self.y=world.move_with_collision(self.x,self.y,dx,dy,PLAYER_RADIUS)

    def take_damage(self, amount):
        self.health=max(0,self.health-amount); self.damage_flash=0.18

    def update_timers(self,dt):
        self.damage_flash=max(0,self.damage_flash-dt)

@dataclass(slots=True)
class Enemy:
    x: float
    y: float
    health: int=100
    max_health: int=100
    speed: float=ENEMY_SPEED
    path: list=field(default_factory=list)
    repath_timer: float=0.0
    attack_timer: float=0.0
    hit_flash: float=0.0

    @property
    def alive(self): return self.health>0

    def update(self,dt,world,player):
        if not self.alive: return
        self.attack_timer=max(0,self.attack_timer-dt)
        self.hit_flash=max(0,self.hit_flash-dt)
        distance=hypot(player.x-self.x,player.y-self.y)
        if distance<=ENEMY_ATTACK_RANGE and world.has_line_of_sight((self.x,self.y),(player.x,player.y)):
            if self.attack_timer<=0:
                player.take_damage(ENEMY_ATTACK_DAMAGE); self.attack_timer=0.9
            return
        self.repath_timer-=dt
        if self.repath_timer<=0 or not self.path:
            self.path=world.find_path((self.x,self.y),(player.x,player.y))
            self.repath_timer=ENEMY_REPATH_INTERVAL
        if not self.path: return
        tx,ty=self.path[0]; dx,dy=tx-self.x,ty-self.y
        d=hypot(dx,dy)
        if d<0.12: self.path.pop(0); return
        step=min(self.speed*dt,d)
        self.x,self.y=world.move_with_collision(self.x,self.y,dx/d*step,dy/d*step,0.18)

    def take_damage(self,amount):
        self.health=max(0,self.health-amount); self.hit_flash=0.15
