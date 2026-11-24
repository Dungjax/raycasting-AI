import unittest
from raycasting_ai.world import World

class WorldTests(unittest.TestCase):
    def setUp(self): self.world=World()
    def test_map_and_boundary(self):
        self.assertEqual((self.world.width,self.world.height),(20,16))
        self.assertEqual(self.world.tile_at(-1,0),1)
    def test_dda_hits_wall(self):
        hit=self.world.cast_ray(2.5,2.5,0.0)
        self.assertEqual(hit.tile,1); self.assertAlmostEqual(hit.distance,6.5,places=5)
    def test_vertical_ray(self):
        hit=self.world.cast_ray(2.5,2.5,1.5707963267948966)
        self.assertEqual(hit.tile,1); self.assertAlmostEqual(hit.distance,12.5,places=5)
    def test_wall_slide(self):
        x,y=self.world.move_with_collision(8.5,2.5,1.0,0.3,0.2)
        self.assertLess(x,9.0); self.assertGreater(y,2.5)
    def test_astar(self):
        path=self.world.find_path((2.5,2.5),(12.5,2.5))
        self.assertTrue(path); self.assertEqual(path[-1],(12.5,2.5))
        self.assertTrue(all(self.world.is_walkable(int(x),int(y)) for x,y in path))
    def test_line_of_sight(self):
        self.assertFalse(self.world.has_line_of_sight((2.5,2.5),(12.5,2.5)))
        self.assertTrue(self.world.has_line_of_sight((2.5,4.5),(7.5,4.5)))

if __name__ == "__main__": unittest.main()
