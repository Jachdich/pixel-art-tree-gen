import pygame
from math import *
import random, time, colorsys
import traceback

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

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

BRANCH_BIAS = 2*pi/5
BIAS_STRENGTH = 0.6

leaves = []

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
            # TODO leaf clumping??
            max_radius = random.uniform(4, 10)
            leaf_bundle = []
            for i in range(random.randint(400, 800)):
                azimuth = random.uniform(-pi, pi)
                elevation = random.uniform(0, pi/2)
                dir = spherical(Vec2(elevation, azimuth))
                radius = random.uniform(max_radius - 2, max_radius)
                offset = dir * radius
                pos = self.pos + offset
                leaf_bundle.append(pos)
            leaves.append((leaf_bundle, self.pos, max_radius + 1))
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
            elif self.angles.x > bias.x:
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
        MIN_TRUNK_WIDTH = 10
        MAX_BRANCH_CHANCE = 10
        # branch_chance = MAX_BRANCH_CHANCE / (MAX_WIDTH - MIN_TRUNK_WIDTH) * (self.width - MIN_TRUNK_WIDTH)
        
        if self.width > MIN_TRUNK_WIDTH:
            branch_chance = (log(self.width-MIN_TRUNK_WIDTH)/log(MAX_WIDTH-MIN_TRUNK_WIDTH)+1)/2 * MAX_BRANCH_CHANCE
        else:
            branch_chance = 0

        if random.random() < branch_chance and self.is_trunk == 0:
            angles, widths, biases, trunks = self.branch_off_trunk(bias_input)
        else:
            angles, widths, biases, trunks = self.branch_equally()
        
        self.children = [Section(self.length, width, self.end_pos, angle) for width, angle in zip(widths, angles)]
        self.children[0].tree(0, biases[0], trunks[0])
        self.children[1].tree(0, biases[1], trunks[1])
        
    def branch_off_trunk(self, bias_input):
        angles = [
            straight_branch_angles(bias_input),
            Vec2(
                self.angles.x + (random.random() * pi/8 + pi/8),
                self.angles.y + ((random.random() - 0.5) * pi/7),
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
            if x.x > pi/2:
                x.x = pi/2
            if x.x < -pi/2:
                x.x = -pi/2
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
                    for dy in range(round(self.length)):
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
DRAW_LINE = True
DRAW_PX = False
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

LEAF_COLOURS = ["354341", "446d4d", "78944b", "abae54"]

TRUNK_COLOURS = [
    "353130", "4d403d", "64534b", "8a6b58", "b0945e",
]

def parse_html(code):
    code = code.strip("#")
    return int(code[0:2], 16), int(code[2:4], 16), int(code[4:6], 16)

LEAF_COLOURS = [parse_html(col) for col in LEAF_COLOURS]
TRUNK_COLOURS = [parse_html(col) for col in TRUNK_COLOURS]

# random.seed(1719787185677640004)
# random.seed(1720197045754790405)
# random.seed(1720202971045046679)
# random.seed(1720203587067500479)
random.seed(1720622865091475633)

root = Section(LENGTH, MAX_WIDTH, Vec3(0.0, 0.0, 0.0), Vec2(0.0, 0.0))
root.tree(0, Vec2(0, None), True)
def mkbuf():
    return [[[0, 0, 0], 255, False] for i in range(resolution * resolution)]

buf = mkbuf()

def raycast(pos):
    ray = Vec3(pos.x, pos.y, pos.z) + LIGHT_DIR * LEAF_RAD;
    light = 1
    for i in range(40):
        col = (0, 0, 255)
        for leaf_bundle, bundlepos, bundlerad in leaves:
            bundle_dist = (bundlepos.x - ray.x) * (bundlepos.x - ray.x) + (bundlepos.y - ray.y) * (bundlepos.y - ray.y) + (bundlepos.z - ray.z) * (bundlepos.z - ray.z)
            if bundle_dist > bundlerad * bundlerad:
                continue
            for leaf2 in leaf_bundle:
                if leaf2 == pos:
                    continue
                # delta = leaf2 - ray
                dist = (leaf2.x - ray.x) * (leaf2.x - ray.x) + (leaf2.y - ray.y) * (leaf2.y - ray.y) + (leaf2.z - ray.z) * (leaf2.z - ray.z)
                if dist < LEAF_RAD**2:
                    light *= 0.999
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
        for leaf_bundle in leaves:
            for leaf in leaf_bundle[0]:
                pos = rotateX(rotateZ(leaf, ang.y), ang.x)
                idx = int(pos.y + ORIGIN.y) * resolution + int(pos.x + ORIGIN.x)
                if pos.z < buf[idx][1]:
                    buf[idx] = (leaf, pos.z)
    else:
        leaf = leaves[0][0][sel_leaf]
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
        pygame.image.save(screen, f"frame{frame_number:04d}.png")
        frame_number += 1
    else:
        for leaf_bundle in leaves:
            for leaf in leaf_bundle[0]:
                pos = rotateX(rotateZ(leaf, ang.y), ang.x)

                hue = 0.3
                value = (-pos.z + 30) / 60
                if value > 1: value = 1
                if value < 0: value = 0
                r, g, b = colorsys.hsv_to_rgb(hue, 1, value)
                col = (int(r*255), int(g*255), int(b*255))
                pos = pos.xy() + ORIGIN
                idx = int(pos.y) * resolution + int(pos.x)
                pygame.draw.circle(screen, col, (pos.x * scl, pos.y * scl), LEAF_RAD)
    pygame.display.flip()
    time.sleep(1/60.0)
    # ang.y += 0.05

ang = Vec2(pi/2, 0)
sel_leaf = 100

def on_mouse_button_down(e):
    global root
    global scl
    global sel_leaf
    if e.button == 1:
        leaves.clear()
        seed = time.time_ns()
        print(seed)
        random.seed(seed)
        root = Section(LENGTH, MAX_WIDTH, Vec3(0.0, 0.0, 0.0), Vec2(0.0, 0.0))
        root.tree(0, Vec2(0, None), True)
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
    global DRAW_LINE
    if e.key == pygame.K_t:
        if DRAW_PX:
            DRAW_PX = False
            DRAW_LINE = True
        else:
            DRAW_PX = True
            DRAW_LINE = False

def main():
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
            loop()
        except Exception as e:
            print(traceback.format_exc())
            break

if __name__ == "__main__":
    main()
