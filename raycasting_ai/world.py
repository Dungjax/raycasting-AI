"""Grid world, DDA ray casting and A* path finding."""
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import atan2, cos, inf, sin, hypot
from typing import Iterable

MAP_LAYOUT = (
"####################",
"#........#.........#",
"#........#.........#",
"#........#....##...#",
"#..................#",
"#..###.............#",
"#..#...............#",
"#..#......####.....#",
"#..............#...#",
"#......##......#...#",
"#..............#...#",
"#....####..........#",
"#..................#",
"#...........#......#",
"#..................#",
"####################",
)

@dataclass(frozen=True, slots=True)
class RayHit:
    distance: float
    tile: int
    side: int
    wall_x: float

class World:
    def __init__(self, rows: Iterable[str] = MAP_LAYOUT):
        rows = tuple(rows)
        if not rows or not rows[0] or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError("Map must be non-empty and rectangular")
        if any(c not in "# .123456789" for r in rows for c in r):
            raise ValueError("Unsupported map character")
        self.height, self.width = len(rows), len(rows[0])
        self.grid = tuple(tuple(1 if c == "#" else int(c) if c.isdigit() else 0 for c in r) for r in rows)

    def tile_at(self, x, y):
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return 1
        return self.grid[y][x]

    def is_walkable(self, x, y):
        return self.tile_at(x, y) == 0

    def can_stand(self, x, y, radius=0.2):
        return all(self.is_walkable(int(x+ox), int(y+oy)) for ox,oy in
                   ((-radius,-radius),(radius,-radius),(-radius,radius),(radius,radius)))

    def move_with_collision(self, x, y, dx, dy, radius=0.2):
        nx = x + dx
        if self.can_stand(nx, y, radius): x = nx
        ny = y + dy
        if self.can_stand(x, ny, radius): y = ny
        return x, y

    def cast_ray(self, x, y, angle, max_distance=24.0):
        dx, dy = cos(angle), sin(angle)
        mx, my = int(x), int(y)
        ddx = abs(1/dx) if abs(dx) > 1e-12 else inf
        ddy = abs(1/dy) if abs(dy) > 1e-12 else inf
        if dx < 0: sx, side_x = -1, (x-mx)*ddx
        else: sx, side_x = 1, (mx+1-x)*ddx
        if dy < 0: sy, side_y = -1, (y-my)*ddy
        else: sy, side_y = 1, (my+1-y)*ddy
        side, distance = 0, 0.0
        for _ in range(self.width*self.height*2):
            if side_x < side_y:
                side_x += ddx; mx += sx; side = 0; distance = side_x-ddx
            else:
                side_y += ddy; my += sy; side = 1; distance = side_y-ddy
            if distance > max_distance: break
            tile = self.tile_at(mx,my)
            if tile:
                hx, hy = x+dx*distance, y+dy*distance
                coord = hy if side == 0 else hx
                return RayHit(max(distance,1e-6),tile,side,coord-int(coord))
        return RayHit(max_distance,0,side,0.0)

    def has_line_of_sight(self, start, end):
        dx,dy=end[0]-start[0],end[1]-start[1]
        distance=hypot(dx,dy)
        if distance <= 1e-6: return True
        hit=self.cast_ray(start[0],start[1],atan2(dy,dx),distance+0.05)
        return hit.distance >= distance-0.08

    def find_path(self, start, goal):
        start=(int(start[0]),int(start[1])); goal=(int(goal[0]),int(goal[1]))
        if not self.is_walkable(*start) or not self.is_walkable(*goal) or start == goal: return []
        h=lambda p: abs(p[0]-goal[0])+abs(p[1]-goal[1])
        serial=count(); frontier=[(h(start),next(serial),start)]
        came={start:None}; cost={start:0}
        while frontier:
            _,_,cur=heappop(frontier)
            if cur == goal: break
            for ox,oy in ((1,0),(-1,0),(0,1),(0,-1)):
                nxt=(cur[0]+ox,cur[1]+oy)
                if not self.is_walkable(*nxt): continue
                nc=cost[cur]+1
                if nc < cost.get(nxt,10**9):
                    cost[nxt]=nc; came[nxt]=cur
                    heappush(frontier,(nc+h(nxt),next(serial),nxt))
        if goal not in came: return []
        path=[]; cur=goal
        while cur != start:
            path.append(cur); cur=came[cur]
        path.reverse()
        return [(x+0.5,y+0.5) for x,y in path]
