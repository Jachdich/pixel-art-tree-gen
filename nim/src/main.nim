import nico
import std/math
import std/options
import std/random

const orgName = "cospox"
const appName = "pixel-art-tree-gen"

type Vec2 = object
    x: float
    y: float

type Vec3 = object
    x: float
    y: float
    z: float

func `+`(a: Vec2, b: Vec2): Vec2 = Vec2(x: a.x + b.x, y: a.y + b.y)
func `-`(a: Vec2, b: Vec2): Vec2 = Vec2(x: a.x - b.x, y: a.y - b.y)
proc `+=`(self: var Vec2, other: Vec2) =
    self.x += other.x
    self.y += other.y
proc `-=`(self: var Vec2, other: Vec2) =
    self.x -= other.x
    self.y -= other.y

func `*`(a: Vec2, b: float): Vec2 = Vec2(x: a.x * b, y: a.y * b)
func toVec2(x: (float32, float32)): Vec2 = Vec2(x: x[0], y: x[1])

func `+`(a: Vec3, b: Vec3): Vec3 = Vec3(x: a.x + b.x, y: a.y + b.y, z: a.z + b.z)
func `-`(a: Vec3, b: Vec3): Vec3 = Vec3(x: a.x - b.x, y: a.y - b.y, z: a.z - b.z)
func `*`(a: Vec3, b: float): Vec3 = Vec3(x: a.x * b, y: a.y * b, z: a.z * b)
proc `+=`(self: var Vec3, other: Vec3) =
    self.x += other.x
    self.y += other.y
    self.z += other.z
proc `-=`(self: var Vec3, other: Vec3) =
    self.x -= other.x
    self.y -= other.y
    self.z += other.z

func sphericalToCartesian(self: Vec2): Vec3 =
    Vec3(
        x: sin(self.x) * cos(self.y),
        y: sin(self.x) * sin(self.y),
        z: cos(self.x)
    )

func rotate(self: Vec3, angles: Vec2): Vec3 =
    let sinx = sin(angles.x)
    let siny = sin(angles.y)
    let cosx = cos(angles.x)
    let cosy = cos(angles.y)
    let x = self.x * cosy - self.y * siny
    let y = self.x * siny + self.y * cosy

    return Vec3(
        x: x,
        y: y * cosx - self.z * sinx,
        z: y * sinx + self.z * cosx,
    )

const LENGTH = 2
const BIAS_STRENGTH = 0.6
const MAX_WIDTH = 8
const MAX_STRAIGHT_CHANCE = 0.97
const MIN_STRAIGHT_CHANCE = 0.6
const MIN_TRUNK_WIDTH = 10
const MAX_BRANCH_CHANCE = 10

type Section = object
    width: float
    pos: Vec3
    angles: Vec2
    children: array[2, Option[ref Section]]

type Tree = object
    leaves: seq[Vec3]
    branches: Section

proc populateTree(self: var Section, inarow: int, bias: Vec2, is_trunk: bool): seq[Vec3] =
    if self.width < 1:
        return @[self.pos]

    let bias_factor = abs(self.angles.x - bias.x)
    var bias_input = Vec2(x: 0, y: 0)
    if bias_factor < PI/3:
        bias_input.x = 0
    elif self.angles.x > bias.x:
        bias_input.x = -bias_factor * BIAS_STRENGTH
    else:
        bias_input.x = bias_factor * BIAS_STRENGTH

    if not bias.y.isNaN:
        var bias_factor = abs(self.angles.y - bias.y)
        if bias_factor < PI/3:
            bias_input.y = 0
        elif self.angles.y > bias.y:
            bias_input.y = -bias_factor * BIAS_STRENGTH
        else:
            bias_input.y = bias_factor * BIAS_STRENGTH


    var straight_chance = pow(self.width/(sqrt(1/(MAX_STRAIGHT_CHANCE - MIN_STRAIGHT_CHANCE)) * MAX_WIDTH), 2) + MIN_STRAIGHT_CHANCE

    # make the trunk longer
    if self.width >= 0.9 * MAX_WIDTH and inarow < 10:
        straight_chance = 1

    let n = MAX_WIDTH
    if rand(1.0) > straight_chance or inarow > (-5/(n-1)*self.width + 5/(n-1)*n + 8):
        return self.branch(bias_input)
    else:
        return self.go_straight(bias_input)

func newSection(width: float = MAX_WIDTH, pos: Vec3 = Vec3(x: 0, y: 0, z: 0), angles: Vec2 = Vec2(x: 0, y: 0)): Section =
    Section(width: width, pos: pos, angles: angles, children: [none(ref Section), none(ref Section)])

proc makeTree(): Tree =
    var section = newSection()
    let leaf_pos = section.populateTree(0, Vec2(x: 0, y: NaN), true)
    var leaves: seq[Vec3] = @[]
    for pos in leaf_pos:
        leaves.add pos
    let tree = Tree(leaves: leaves, branches: section)
    tree


proc drawTree(tree: Tree) = discard 1


var view_angle = Vec2(x: 0, y: 0)
var tree = makeTree()


proc gameInit() = discard 1

proc gameUpdate(dt: float32) =
    if mousebtn(2):
        let delta = mouserel().toVec2() * 0.04
        view_angle += delta
    # if mousebtnup(0):
        
proc gameDraw() =
    cls()
    setColor(3)
    drawTree(tree)
    

nico.init(orgName, appName)
nico.createWindow(appName, 128, 128, 4, false)
nico.run(gameInit, gameUpdate, gameDraw)
