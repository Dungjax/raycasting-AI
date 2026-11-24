"""DDA wall renderer and depth-tested billboard enemies."""
from math import atan2, cos, hypot
import pygame
from .config import FOV, MAX_RAY_DISTANCE
from .entities import normalize_angle

WALL_COLORS={1:(142,94,68),2:(85,126,150),3:(138,132,82),4:(100,132,94)}

class Renderer:
    def __init__(self,width,height):
        self.width,self.height=width,height
        self.horizon=height//2
        self.surface=pygame.Surface((width,height)).convert()
        self.depth=[MAX_RAY_DISTANCE]*width
        self.enemy=self._enemy_sprite()

    @staticmethod
    def _enemy_sprite():
        s=pygame.Surface((64,88),pygame.SRCALPHA)
        pygame.draw.ellipse(s,(90,35,35),(9,28,46,50))
        pygame.draw.ellipse(s,(155,65,55),(15,10,34,32))
        for x in (25,39): pygame.draw.circle(s,(255,215,110),(x,24),4)
        pygame.draw.line(s,(35,15,15),(24,48),(40,48),3)
        pygame.draw.line(s,(65,25,20),(19,57),(12,78),6)
        pygame.draw.line(s,(65,25,20),(45,57),(52,78),6)
        return s

    def render(self,world,player,enemies):
        self.surface.fill((27,37,54),(0,0,self.width,self.horizon))
        pygame.draw.rect(self.surface,(42,39,35),(0,self.horizon,self.width,self.height-self.horizon))
        for col in range(self.width):
            camera=2*col/self.width-1
            angle=player.angle+camera*FOV/2
            hit=world.cast_ray(player.x,player.y,angle,MAX_RAY_DISTANCE)
            depth=max(.035,hit.distance*cos(angle-player.angle))
            self.depth[col]=depth
            height=min(self.height*5,int(self.height*.92/depth))
            top=max(0,self.horizon-height//2); bottom=min(self.height,self.horizon+height//2)
            base=WALL_COLORS.get(hit.tile,WALL_COLORS[1])
            fog=max(.22,1-depth/MAX_RAY_DISTANCE*.78)
            shade=fog*(.76 if hit.side else 1)*(0.68 if int(hit.wall_x*8)%4==0 else 1)
            color=tuple(int(c*shade) for c in base)
            self.surface.fill(color,(col,top,1,max(1,bottom-top)))
            joint=tuple(int(c*.62) for c in color)
            for n in (1,2,3):
                y=top+(bottom-top)*n//4
                if 0<=y<self.height: self.surface.set_at((col,y),joint)
        visible=[]
        for enemy in enemies:
            if not enemy.alive: continue
            dx,dy=enemy.x-player.x,enemy.y-player.y
            dist=hypot(dx,dy); rel=normalize_angle(atan2(dy,dx)-player.angle)
            if dist>.12 and abs(rel)<FOV*.62: visible.append((dist,rel,enemy))
        for dist,rel,enemy in sorted(visible,reverse=True,key=lambda item:item[0]):
            sx=int((.5+rel/FOV)*self.width)
            sh=min(self.height*2,int(self.height*.78/max(.1,dist))); sw=max(1,int(sh*64/88))
            sprite=pygame.transform.scale(self.enemy,(sw,sh))
            if enemy.hit_flash>0: sprite.fill((95,25,25,0),special_flags=pygame.BLEND_RGBA_ADD)
            left=sx-sw//2; top=self.horizon-sh//2
            for x in range(max(0,left),min(self.width,left+sw)):
                if dist<self.depth[x]:
                    self.surface.blit(sprite,(x,top),(x-left,0,1,sh))
        return self.surface

    def draw_hud(self,world,player,enemies,ammo,reloading):
        font=pygame.font.Font(None,22); small=pygame.font.Font(None,17)
        pygame.draw.rect(self.surface,(10,12,16),(10,10,142,48),border_radius=5)
        pygame.draw.rect(self.surface,(70,72,78),(18,22,112,12),border_radius=4)
        width=int(108*player.health/max(1,player.max_health))
        if width: pygame.draw.rect(self.surface,(180,55,52),(20,24,width,8),border_radius=3)
        self.surface.blit(small.render(f"HP {player.health:03d}",True,(245,240,230)),(18,39))
        self.surface.blit(font.render("RELOAD..." if reloading else f"AMMO {ammo:02d}",True,(235,225,190)),(self.width-112,15))
        self.surface.blit(small.render(f"HOSTILES {len(enemies):02d}",True,(225,170,150)),(self.width-112,38))
        cx,cy=self.width//2,self.height//2
        pygame.draw.line(self.surface,(235,235,220),(cx-7,cy),(cx-2,cy))
        pygame.draw.line(self.surface,(235,235,220),(cx+2,cy),(cx+7,cy))
        mx,my=self.width-96,self.height-72
        pygame.draw.rect(self.surface,(9,12,16),(mx-4,my-4,world.width*4+8,world.height*4+8))
        for y,row in enumerate(world.grid):
            for x,tile in enumerate(row):
                if tile: pygame.draw.rect(self.surface,(84,88,94),(mx+x*4,my+y*4,4,4))
        for e in enemies:
            if e.alive: pygame.draw.circle(self.surface,(220,70,58),(mx+int(e.x*4),my+int(e.y*4)),2)
        pygame.draw.circle(self.surface,(90,220,130),(mx+int(player.x*4),my+int(player.y*4)),3)
        if player.damage_flash>0:
            overlay=pygame.Surface((self.width,self.height),pygame.SRCALPHA)
            overlay.fill((180,15,20,int(90*player.damage_flash/.18)))
            self.surface.blit(overlay,(0,0))
