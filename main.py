import pygame
from math import *
import random, time, colorsys, sys
import traceback

MAX_MEMBERS = int(sys.argv[1])

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def tup(self):
        return (self.x, self.y)

    def __add__(self, other):
        if type(other) == type(self):
            return Vec2(self.x + other.x, self.y + other.y)
        else:
            raise TypeError(f"Can't add type '{type(other)}' to Vec2")

    def __mul__(self, other):
        if not type(other) == int or type(other) == float:
            raise TypeError(f"Can't multiply type '{type(other)}' with Vec2")
        return Vec2(self.x * other, self.y * other)
    def __repr__(self):
        return f"Vec2({self.x}, {self.y})"

class Vec3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def xy(self) -> Vec2:
        return Vec2(self.x, self.y)

    def __add__(self, other):
        if type(other) == type(self):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            raise TypeError(f"Can't add type '{type(other)}' to Vec3")
    def __sub__(self, other):
        if type(other) == type(self):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            raise TypeError(f"Can't sub type '{type(other)}' to Vec3")

    def __mul__(self, other):
        if not type(other) == int and not type(other) == float:
            raise TypeError(f"Can't multiply type '{type(other)}' with Vec3")
        return Vec3(self.x * other, self.y * other, self.z * other)
    def __addeq__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
    def __repr__(self):
        return f"Vec2({self.x}, {self.y}, {self.z})"

def spherical(angles):
    return Vec3(
        sin(angles.x) * cos(angles.y),
        sin(angles.x) * sin(angles.y),
        cos(angles.x)
    )

def rotateX(coords, rad):
    cosa = cos(rad)
    sina = sin(rad)
    y = coords.y * cosa - coords.z * sina
    z = coords.y * sina + coords.z * cosa
    return Vec3(coords.x, y, z)

def rotateY(coords, rad):
    cosa = cos(rad)
    sina = sin(rad)
    z = coords.z * cosa - coords.x * sina
    x = coords.z * sina + coords.x * cosa
    return Vec3(x, coords.y, z)

def rotateZ(coords, rad):
    cosa = cos(rad)
    sina = sin(rad)
    x = coords.x * cosa - coords.y * sina
    y = coords.x * sina + coords.y * cosa
    return Vec3(x, y, coords.z)

class Octree:
    def __init__(self, origin: Vec3, rad: float):
        self.children = []
        self.points = []
        self.centre = origin
        self.rad = rad
        self.leaf = True
        
    def add(self, point: Vec3):
        if self.leaf:
            self.points.append(point)
            if len(self.points) > MAX_MEMBERS:# and self.rad > 1 * LEAF_RAD:
                self.subdivide()
        else:
            top   = int(point.x > self.centre.x)
            left  = int(point.y > self.centre.y)
            front = int(point.z > self.centre.z)
            index = top << 2 | left << 1 | front
            self.children[index].add(point)

    def subdivide(self):
        self.leaf = False
        r = self.rad / 2
        for i in range(8):
            top =   ((i >> 2) & 1) * 2 - 1
            left =  ((i >> 1) & 1) * 2 - 1
            front = ((i >> 0) & 1) * 2 - 1
            self.children.append(Octree(self.centre + Vec3(r * top, r * left, r * front), r))

        # re-add now we're no longer a leaf
        for point in self.points:
            self.add(point)

    def draw(self):
        vertices = []
        for i in range(8):
            top =   ((i >> 2) & 1) * 2 - 1
            left =  ((i >> 1) & 1) * 2 - 1
            front = ((i >> 0) & 1) * 2 - 1
            vertices.append(self.centre + Vec3(top, left, front) * self.rad)

        for a, b in [
            (0b000, 0b001), (0b000, 0b010), (0b000, 0b100),
            (0b001, 0b011), (0b001, 0b101), (0b101, 0b100),
            (0b101, 0b111), (0b010, 0b110), (0b010, 0b011),
            (0b011, 0b111), (0b110, 0b111), (0b110, 0b100),
        ]:
            pos_a = vertices[a]
            pos_b = vertices[b]
            a_ss = (rotateX(rotateZ(pos_a, ang.y), ang.x).xy() + ORIGIN) * scl
            b_ss = (rotateX(rotateZ(pos_b, ang.y), ang.x).xy() + ORIGIN) * scl
            pygame.draw.line(screen, (255, 0, 255), a_ss.tup(), b_ss.tup())

        # for c in self.children:
        #     c.draw()

    def query(self, pos) -> int:
        # self.draw()
        if self.leaf:
            count = 0
            for point in self.points:
                if pos == point:
                    continue
                dist = (point.x - pos.x) * (point.x - pos.x) +\
                       (point.y - pos.y) * (point.y - pos.y) +\
                       (point.z - pos.z) * (point.z - pos.z)
                if dist < LEAF_RAD * LEAF_RAD:
                    count += 1
            return count

        top   = int(pos.x > self.centre.x)
        left  = int(pos.y > self.centre.y)
        front = int(pos.z > self.centre.z)
        index = top << 2 | left << 1 | front
        # self.children[index].draw()
        return self.children[index].query(pos)

            

BRANCH_BIAS = 2*pi/5
BIAS_STRENGTH = 0.6
correct = True

leaves = []
bush_positions = []

def frange(x, y, jump):
  while x < y:
    yield x
    x += jump

def lerp(a, b, t):
    return a + (b-a) * t

class Section:
    def __init__(self, length, width, pos, angles):
        self.length = length
        self.width = width
        self.pos = pos
        self.angles = angles
        self.children = []
        self.bias = 0
        self.end_pos = spherical(self.angles) * self.length + self.pos

    def tree(self, inarow, bias: Vec2, is_trunk):
        self.bias = bias
        self.inarow = inarow
        self.is_trunk = is_trunk
        if self.width < 1:
            bush_positions.append(self.pos)
            return

        bias_factor = abs(self.angles.x - bias.x)
        bias_input = Vec2(0, 0)
        if bias_factor < pi/6:
            bias_input.x = 0
        elif self.angles.x > bias.x:
            bias_input.x = -bias_factor * BIAS_STRENGTH
        else:
            bias_input.x = bias_factor * BIAS_STRENGTH

        if bias.y is not None:
            bias_factor = abs(self.angles.y - bias.y)
            if bias_factor < pi/6:
                bias_input.y = 0
            elif self.angles.y > bias.y:
                bias_input.y = -bias_factor * BIAS_STRENGTH
            else:
                bias_input.y = bias_factor * BIAS_STRENGTH

        MAX_STRAIGHT_CHANCE = 0.97
        MIN_STRAIGHT_CHANCE = 0.6
        
        straight_chance = (self.width/(sqrt(1/(MAX_STRAIGHT_CHANCE - MIN_STRAIGHT_CHANCE)) * MAX_WIDTH)) ** 2 + MIN_STRAIGHT_CHANCE
    
        # make the trunk longer
        if self.width >= 0.9 * MAX_WIDTH and inarow < 10:
            straight_chance = 1
        
        n = MAX_WIDTH
        if random.random() > straight_chance or inarow > (-5/(n-1)*self.width + 5/(n-1)*n + 8):
            self.branch(bias_input)
        else:
            self.go_straight(bias_input)

    def straight_branch_angles(self, bias_input: Vec2):
        return Vec2(
            self.angles.x + random.gauss(bias_input.x, pi/18),
            self.angles.y + random.gauss(bias_input.y, pi/18),
        )
    
    def go_straight(self, bias_input: Vec2):
        # angles.x = bias # TODO Temp
        angles = self.straight_branch_angles(bias_input)
        next = Section(self.length, self.width * 0.98, self.end_pos, angles)
        next.tree(self.inarow + 1, self.bias, self.is_trunk)
        self.children = [next]

    def branch(self, bias_input: Vec2):
        if correct:
            MIN_TRUNK_WIDTH = MAX_WIDTH * 0.3
        else:
            MIN_TRUNK_WIDTH = 10
        MAX_BRANCH_CHANCE = 1
        
        if self.width > MIN_TRUNK_WIDTH:
            branch_chance = (log(self.width-MIN_TRUNK_WIDTH)/log(MAX_WIDTH-MIN_TRUNK_WIDTH)+1)/2 * MAX_BRANCH_CHANCE
        else:
            branch_chance = 0

        if random.random() < branch_chance and self.is_trunk:
            angles, widths, biases, trunks = self.branch_off_trunk(bias_input)
        else:
            angles, widths, biases, trunks = self.branch_equally()
        
        self.children = [Section(self.length, width, self.end_pos, angle) for width, angle in zip(widths, angles)]
        self.children[0].tree(0, biases[0], trunks[0])
        self.children[1].tree(0, biases[1], trunks[1])
        
    def branch_off_trunk(self, bias_input):
        angles = [
            self.straight_branch_angles(bias_input),
            Vec2(
                self.angles.x + random.uniform(pi/8, pi/2 - self.angles.x),
                self.angles.y + random.uniform(-pi, pi),
            )
        ]
        main_width = (random.random() * 0.4 + 0.5) * self.width
        widths = [
            main_width,
            self.width - main_width
        ]

        biases = [Vec2(0, None), Vec2(BRANCH_BIAS, angles[1].y)]
        trunks = [True, False]

        return angles, widths, biases, trunks

    def branch_equally(self):
        if self.angles.x < pi/8:
            angles = self.get_fork_angles()
        else:
            # TODO bias towards going in the same direction or something
            angles = [
                Vec2(
                    self.angles.x + random.gauss(pi/16, pi/32),
                    self.angles.y + random.gauss(3*pi/8, pi/10),
                ),
                Vec2(
                    self.angles.x - random.gauss(pi/16, pi/32),
                    self.angles.y - random.gauss(3*pi/8, pi/10),
                )
            ]

        if self.is_trunk and self.width > 0.3 * MAX_WIDTH: # TEMP: figure out a better heuristic for when to branch into 2 trunks
            biases = [Vec2(angles[0].x, None), Vec2(angles[1].x, None)]
            trunks = [True, True]
        else:
            biases = [Vec2(BRANCH_BIAS, angles[0].y), Vec2(BRANCH_BIAS, angles[1].y)]
            # biases = [angles[0].x, angles[1].x]
            trunks = [False, False]

        def clamp(x):
            if x.x > pi/4:
                x.x = pi/4
            if x.x < -pi/4:
                x.x = -pi/4
            return x
        biases = [clamp(b) for b in biases]
        # TODO different branching logic for big vs small branches
        # big branches should aim to get away from the others (bias branches to go away from the centre) and be relatively long

        # when branching, consider the current angle to decide what kind of yaw/azimuth the branch can be at. if going relatively up, any yaw angle is permitted, if going sideways, bias towards that direction.
        # punish getting too far from the tree, or too close ot other branches
        width = random.gauss(0.5, 0.1) * self.width
        widths = [
            width * 1.2,
            (self.width - width) * 1.2
        ]

        return angles, widths, biases, trunks

    def get_fork_angles(self):
        # make sure branches are somewhat different direction to eachother
        azimuth_difference = random.uniform(pi/2, 3*pi/2)
        azimuth_a = random.uniform(0, 2*pi)
        azimuth_b = azimuth_a + azimuth_difference

        elevation_a = abs(random.gauss(self.angles.x, pi/4) + pi/7)
        elevation_b = abs(random.gauss(self.angles.x, pi/4) + pi/7)
        
        return [
            Vec2(elevation_a, azimuth_a),
            Vec2(elevation_b, azimuth_b),
        ]

    def draw(self, ang: Vec2):
        global buf
        # stroke_width(int(self.width) * scl)
        if DRAW_LINE:
            end_pos = spherical(self.angles) * self.length + self.pos
            end_pos = rotateX(rotateZ(end_pos, ang.y), ang.x)
            start_pos = rotateX(rotateZ(self.pos, ang.y), ang.x)
            hue = 0.5 if self.is_trunk else 0.0
            value = (-end_pos.z + 30) / 60
            if value > 1: value = 1
            if value < 0: value = 0
            r, g, b = colorsys.hsv_to_rgb(hue, 1, value)
            col = (int(r*255), int(g*255), int(b*255))

            end_pos = end_pos.xy() + ORIGIN
            start_pos = start_pos.xy() + ORIGIN
            pygame.draw.line(screen, col, (start_pos.x * scl, start_pos.y * scl), (end_pos.x* scl, end_pos.y * scl))
        if DRAW_PX:
            for n in range(0, int(self.length)):
                end_pos = spherical(self.angles) * n + self.pos
                end_pos_ss = rotateX(rotateZ(end_pos, ang.y), ang.x)
                actual_width = round(self.width / MAX_WIDTH * 2.8) + 1

                
                for dx in range(actual_width):
                    # for dy in range(round(self.length)):
                        dy = 0
                        x = int(end_pos_ss.x + dx - actual_width/2) + ORIGIN.x
                        y = int(end_pos_ss.y + dy - actual_width/2) + ORIGIN.y
                        depth = buf[y * resolution + x][1]
                        if end_pos_ss.z < depth:
                            pixel_ws = rotateZ(rotateX(Vec3(x, y, end_pos_ss.z) - Vec3(ORIGIN.x, ORIGIN.y, 0), -ang.x), -ang.y)
                            
                            light = raycast(pixel_ws)
                            col = TRUNK_COLOURS[int(light * (len(TRUNK_COLOURS) - 1))]
                            buf[y*resolution+x] = [col, end_pos_ss.z, False]
        for c in self.children:
            c.draw(ang)

scl = 12
DRAW_LINE = False
DRAW_PX = True
MAX_WIDTH = 8
LENGTH = 2
resolution = 100
w, h = resolution*scl, resolution*scl
pygame.init()
screen = pygame.display.set_mode((w, h))

ORIGIN = Vec2(resolution//2, resolution//4*3)
LEAF_RAD = 3
LIGHT_DIR = Vec3(0, 1/sqrt(2), 1/sqrt(2)) * 1
# LEAF_COLOURS = [
# "#1F2E52",
# "#223D54",
# "#2E5C6B",
# "#36777A",
# "#50AB76",
# "#69C976",
# "#A0DE85",
# "#CFF291",
# ]

# LEAF_COLOURS = [
# "#2f4d2f", 
# "#44702d",
# "#819447",
# "#a6b04f",
# ]

# LEAF_COLOURS = [
#     "#19332d",
#     "#25562e",
#     "#468232",
#     "#75a743",
#     "#a8ca58",
# ]

# LEAF_COLOURS = ["354341", "446d4d", "78944b", "abae54"]

random.seed(1720987585756419465)

MAX_HUE_SHIFT = 0.2
NUM_COLOURS = 5
MIN_VALUE = 0.2
MAX_VALUE = 0.9

def qerp(a, b, c, t):
    return (1-t)**2*a+2*(1-t)*t*b+t**2*c

def generate_palette(init_hue):
    palette = []
    for i in range(NUM_COLOURS):
        hue_shift = qerp(MAX_HUE_SHIFT, -MAX_HUE_SHIFT, -MAX_HUE_SHIFT, i/(NUM_COLOURS-1))
        value = lerp(MIN_VALUE, MAX_VALUE, i/(NUM_COLOURS-1))
        saturation = qerp(0.2, 0.5, 0.5, i/(NUM_COLOURS-1))
        r,g,b = colorsys.hsv_to_rgb(init_hue + hue_shift, saturation, value)
        palette.append([int(r * 255), int(g * 255), int(b * 255)])
    return palette

LEAF_COLOURS = generate_palette(0.38)
TRUNK_COLOURS = [
    "353130", "4d403d", "64534b", "8a6b58", "b0945e",
]

def parse_html(code):
    code = code.strip("#")
    return int(code[0:2], 16), int(code[2:4], 16), int(code[4:6], 16)

# LEAF_COLOURS = [parse_html(col) for col in LEAF_COLOURS]
TRUNK_COLOURS = [parse_html(col) for col in TRUNK_COLOURS]

def make_leaves():
    for bush_pos in bush_positions:
        # # TODO leaf clumping??
        # for i in range(random.randint(200, 400)):
        #     azimuth = random.uniform(-pi, pi)
        #     elevation = random.uniform(0, pi/2)
        #     dir = spherical(Vec2(elevation, azimuth))
        #     radius = random.uniform(max_radius - 1, max_radius)
        #     offset = dir * radius
        #     pos = self.pos + offset
        #     leaves.append(pos)

        max_radius = random.uniform(4, 10)
        for elevation in frange(0, 3*pi/5, 0.8 / max_radius):
            for azimuth in frange(-pi, pi, lerp(3.0, 0.3, elevation / (3*pi/5)) / max_radius):
                radius = random.uniform(max_radius - 4, max_radius)
                dir = spherical(Vec2(elevation, azimuth))
                offset = dir * radius
                pos = bush_pos + offset
                leaves.append(pos)

root = None
leaf_octree = None
def make_tree():
    global root, leaf_octree
    leaves.clear()
    bush_positions.clear()
    root = Section(LENGTH, MAX_WIDTH, Vec3(0.0, 0.0, 0.0), Vec2(0.0, 0.0))
    root.tree(0, Vec2(0, None), True)

    make_leaves()
    
    avg = lambda xs: sum(xs) / len(xs)
    o = Vec3(avg([l.x for l in leaves]), avg([l.y for l in leaves]), avg([l.z for l in leaves]))
    rad = max([max(abs(l.x - o.x), abs(l.y - o.y), abs(l.z - o.z)) for l in leaves]) + 0.1 # for good luck
    leaf_octree = Octree(o, rad)
    for leaf in leaves:
        leaf_octree.add(leaf)

make_tree()

def mkbuf():
    return [[[0, 0, 0], 255, False] for i in range(resolution * resolution)]

buf = mkbuf()

def raycast(pos):
    ray = Vec3(pos.x, pos.y, pos.z) + LIGHT_DIR * LEAF_RAD;
    light = 1
    for i in range(30):
        col = (0, 0, 255)
        leaves_hit = leaf_octree.query(ray)
        if leaves_hit > 0:
            light *= 0.98 ** leaves_hit
            col = (255, 0, 0)

        if DRAW_LINE:
            start = (rotateX(rotateZ(ray, ang.y), ang.x).xy() + ORIGIN) * scl
            end = (rotateX(rotateZ(ray + LIGHT_DIR, ang.y), ang.x).xy() + ORIGIN) * scl
            pygame.draw.line(screen, col, (start.x, start.y), (end.x, end.y))
        ray += LIGHT_DIR
    return light

def draw_leaf(leaf):
    pos = rotateX(rotateZ(leaf, ang.y), ang.x)
    idx = int(pos.y + ORIGIN.y) * resolution + int(pos.x + ORIGIN.x)
    if pos.z <= buf[idx][1]:
        light = raycast(leaf)
        col = LEAF_COLOURS[int(light * (len(LEAF_COLOURS) - 1))]
        buf[idx] = (col, pos.z)
        return col

frame_number = 0
def loop():
    global buf
    global frame_number
    screen.fill((0, 0, 0))
    buf = mkbuf()
    root.draw(ang)

    if DRAW_PX:
        for leaf in leaves:
            pos = rotateX(rotateZ(leaf, ang.y), ang.x)
            idx = int(pos.y + ORIGIN.y) * resolution + int(pos.x + ORIGIN.x)
            if pos.z < buf[idx][1]:
                buf[idx] = (leaf, pos.z)
    else:
        pass
        leaf = leaves[sel_leaf]
        draw_leaf(leaf)
    
    if DRAW_PX:
        # offset = int(w * (scl/8 - 1) / 2)
        for x in range(resolution):
            for y in range(resolution):
                val = buf[y * resolution + x]
                if val[1] != 255:
                    # if val[0] is None:
                    #     hue = 0
                    #     saturation = 0
                    # else:
                    #     hue = val[0] / 360
                    #     if hue > 1: hue = 1
                    #     if hue < 0: hue = 0
                    #     saturation = 1

                    # value = (-val[1] + 20) / 40
                    # if value > 1: value = 1
                    # if value < 0: value = 0
                    
                    # r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                    # fill(int(r*255),int(g*255),int(b*255))
                    if type(val[0]) == Vec3:
                        col = draw_leaf(val[0])
                    else:
                        col = val[0]
                    r, g, b = col
                    if g > 255:
                        g = 255
                    if g < 0:
                        g = 0
                    
                    z = val[1]
                    # factor = (-z + 20) / 40
                    # if factor < 0:
                    #     factor = 0
                    # if factor > 1:
                    #     factor = 1
                    factor = 1
                    col = (int(r*factor), int(g*factor), int(b*factor))
                    pygame.draw.rect(screen, col, (x * scl, y * scl - scl/2, round(scl), round(scl)))
        # pygame.image.save(screen, f"frame{frame_number:04d}.png")
        frame_number += 1
    else:
        pass
        # leaf_octree.draw()
        # for leaf in leaves:
        #     pos = rotateX(rotateZ(leaf, ang.y), ang.x)

        #     hue = 0.3
        #     value = (-pos.z + 30) / 60
        #     if value > 1: value = 1
        #     if value < 0: value = 0
        #     r, g, b = colorsys.hsv_to_rgb(hue, 1, value)
        #     col = (int(r*255), int(g*255), int(b*255))
        #     pos = pos.xy() + ORIGIN
        #     idx = int(pos.y) * resolution + int(pos.x)
        #     pygame.draw.circle(screen, col, (pos.x * scl, pos.y * scl), LEAF_RAD)
    pygame.display.flip()
    # ang.y += 0.08

ang = Vec2(pi/2, 0)
sel_leaf = 1
last_seed = 1720987585756419465

def on_mouse_button_down(e):
    global root
    global scl
    global sel_leaf, last_seed
    if e.button == 1:
        seed = time.time_ns()
        print(seed)
        last_seed = seed
        random.seed(seed)
        make_tree()
    elif e.button == 5:
        sel_leaf += 1
    elif e.button == 4:
        sel_leaf -= 1

def on_mouse_motion(e):
    if e.buttons[2] == 1:
        ang.x += e.rel[1] * 0.04
        ang.y += e.rel[0] * 0.04


import pygame
def on_keydown(e):
    global DRAW_PX
    global DRAW_LINE, correct
    if e.key == pygame.K_t:
        if DRAW_PX:
            DRAW_PX = False
            DRAW_LINE = True
        else:
            DRAW_PX = True
            DRAW_LINE = False
    if e.key == pygame.K_e:
        correct = not correct
        random.seed(last_seed)
        make_tree()
        print(correct)
        

def main():
    total = 0
    # for i in range(50):
    # init_hue = 0.5
    # global LEAF_COLOURS
    while True:
        try:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    on_mouse_button_down(event)
                elif event.type == pygame.MOUSEMOTION:
                    on_mouse_motion(event)
                elif event.type == pygame.KEYDOWN:
                    on_keydown(event)
                elif event.type == pygame.QUIT:
                    return
            a = time.time()
            loop()
            b = time.time()
            rate = 1/(b-a)
            total += rate

            # init_hue += 0.01
            # LEAF_COLOURS = generate_palette(init_hue)
        except Exception as e:
            print(traceback.format_exc())
            break
    print(total / 50)

if __name__ == "__main__":
    main()
