import sys
sys.path.append("..")
from pyrocessing import *
from math import *
import random

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

class Section:
    def __init__(self, length, width, pos, angle, children):
        self.length = length
        self.width = width
        self.pos = pos
        self.angle = angle
        self.children = children

    def tree(self, inarow, bias=-pi/2):
        if self.width < 1:
            return
        end_pos = Vec2(cos(self.angle), sin(self.angle)) * self.length + self.pos
        bias_strength = 0.1
        bias_factor = abs(self.angle - bias)
        if bias_factor < pi/3:
            bias_input = 0
        elif self.angle > bias:
            bias_input = -bias_factor * bias_strength
        else:
            bias_input = bias_factor * bias_strength

        if random.random() < 0.15 or inarow > (-5/15*self.width + 5/15*16 + 6):
            if random.random() < 0.7:
                temp_angle = (random.random() - 0.5) * pi/6
                if temp_angle < 0:
                    temp_angle -= pi/5
                else:
                    temp_angle += pi/5
                angles = [
                    self.angle + (random.random() - 0.5 + bias_input) * pi/8,
                    self.angle + temp_angle
                ]
                main_width = random.random() * 0.7 * self.width
                widths = [
                    main_width,
                    self.width - main_width
                ]
                new_bias = [bias, 0]
                if angles[1] > -pi/2:
                    new_bias[1] = -pi/4
                else:
                    new_bias[1] = -3*pi/4
            else:
                angles = [
                    self.angle + (random.random() * pi/8 + pi/16),
                    self.angle - (random.random() * pi/8 + pi/16)
                ]

                width = (random.random() * 0.6 + 0.3) * self.width
                widths = [
                    width,
                    self.width - width 
                ]
                new_bias = [-pi/4 if angle > -pi/2 else -3*pi/4 for angle in angles]

            self.children = [Section(self.length, width, end_pos, angle, []) for width, angle in zip(widths, angles)]
            self.children[0].tree(0, bias=new_bias[0])
            self.children[1].tree(0, bias=new_bias[1])
        else:
            angle = self.angle + (random.random() - 0.5 + bias_input) * pi/8
            next = Section(self.length, self.width * 0.99, end_pos, angle, [])
            next.tree(inarow + 1, bias)
            self.children = [next]

    def draw(self):
        # stroke_width(int(self.width) * scl)
        stroke_width(1)
        stroke(255, 255, 255)
        fill(255, 255, 255)
        end_pos = Vec2(cos(self.angle), sin(self.angle)) * self.length + self.pos
        # line(self.pos.x * scl, self.pos.y * scl, end_pos.x* scl, end_pos.y * scl)
        for n in range(0, int(self.length)):
            end_pos = Vec2(cos(self.angle), sin(self.angle)) * n + self.pos
            actual_width = round(self.width / 16 * 3) + 1
            print(actual_width)
            for dx in range(actual_width):
                for dy in range(actual_width):
                    rect(int(end_pos.x + dx) * scl, int(end_pos.y + dy) * scl, scl, scl)
        for c in self.children:
            c.draw()

scl = 6
size(128*scl, 128*scl)

def loop():
    update()

@event
def on_mouse_button_down(_):
    root = Section(1, 16, Vec2(128 / 2.0, 128.0), -pi/2, [])
    root.tree(0)
    background(0, 0, 0)
    root.draw()

loop_on(loop)
