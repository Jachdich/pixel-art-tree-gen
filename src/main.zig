const std = @import("std");
const assert = std.debug.assert;
const RndGen = std.rand.DefaultPrng;
const Allocator = std.mem.Allocator;
const zigimg = @import("zigimg");
const sin = std.math.sin;
const cos = std.math.cos;
const pi = std.math.pi;
const sqrt = std.math.sqrt;

const Vec2 = struct {
    x: f64,
    y: f64,

    pub fn new(x: f64, y: f64) Vec2 {
        return Vec2{
            .x = x,
            .y = y,
        };
    }
    pub fn add(self: Vec2, other: Vec2) Vec2 {
        return Vec2.new(self.x + other.x, self.y + other.y);
    }
    pub fn addeq(self: *Vec2, other: Vec2) void {
        self.x += other.x;
        self.y += other.y;
    }
    pub fn sub(self: Vec2, other: Vec2) Vec2 {
        return Vec2.new(self.x - other.x, self.y - other.y);
    }
    pub fn subeq(self: *Vec2, other: Vec2) void {
        self.x -= other.x;
        self.y -= other.y;
    }
    pub fn scale(self: Vec2, f: f64) Vec2 {
        return Vec2.new(self.x * f, self.y * f);
    }
    pub fn scaleeq(self: *Vec2, f: f64) void {
        self.x *= f;
        self.y *= f;
    }
};

const Vec3 = struct {
    x: f64,
    y: f64,
    z: f64,

    pub fn new(x: f64, y: f64, z: f64) Vec3 {
        return Vec3{ .x = x, .y = y, .z = z };
    }

    pub fn vec2(v: Vec2, z: f64) Vec3 {
        return Vec3{ .x = v.x, .y = v.y, .z = z };
    }

    pub fn from_spherical(angles: Vec2) Vec3 {
        return Vec3{
            .x = sin(angles.x) * cos(angles.y),
            .y = sin(angles.x) * sin(angles.y),
            .z = cos(angles.x),
        };
    }

    pub fn xy(self: Vec3) Vec2 {
        return Vec2.new(self.x, self.y);
    }

    pub fn rotate(self: Vec3, angles: Vec2) Vec3 {
        const cosx = cos(angles.x);
        const sinx = sin(angles.x);
        const cosy = cos(angles.y);
        const siny = sin(angles.y);
        const x = self.x * cosy - self.y * siny;
        const y = self.x * siny + self.y * cosy;
        const z = self.z;

        return Vec3{
            .x = x,
            .y = y * cosx - z * sinx,
            .z = y * sinx + z * cosx,
        };
    }

    pub fn add(self: Vec3, other: Vec3) Vec3 {
        return Vec3.new(self.x + other.x, self.y + other.y, self.z + other.z);
    }
    pub fn addeq(self: *Vec3, other: Vec3) void {
        self.x += other.x;
        self.y += other.y;
        self.z += other.z;
    }
    pub fn sub(self: Vec3, other: Vec3) Vec3 {
        return Vec3.new(self.x - other.x, self.y - other.y, self.z - other.z);
    }
    pub fn subeq(self: *Vec3, other: Vec3) void {
        self.x -= other.x;
        self.y -= other.y;
        self.z -= other.z;
    }
    pub fn scale(self: Vec3, f: f64) Vec3 {
        return Vec3.new(self.x * f, self.y * f, self.z * f);
    }
    pub fn scaleeq(self: *Vec3, f: f64) void {
        self.x *= f;
        self.y *= f;
        self.z *= f;
    }
};

const LENGTH = 2;
const MAX_WIDTH = 8;
const BIAS_STRENGTH = 0.6;
const MAX_STRAIGHT_CHANCE = 0.97;
const MIN_STRAIGHT_CHANCE = 0.6;

const Section = struct {
    angles: Vec2,
    width: f64,
    bias: f64 = 0,
    pos: Vec3,
    end_pos: Vec3,
    children: [2]?*Section,

    pub fn new(width: f64, pos: Vec3, angles: Vec2) Section {
        return Section{
            .angles = angles,
            .width = width,
            .bias = 0,
            .children = .{ null, null },
            .end_pos = Vec3.from_spherical(angles).scale(LENGTH).add(pos),
        };
    }

    pub fn tree(self: *Section, inarow: usize, bias: Vec2, is_trunk: bool, rng: RndGen, alloc: Allocator) void {
        self.bias = bias;
        self.inarow = inarow;
        self.is_trunk = is_trunk;
        if (self.width < 1) {
            // make leaves
            return;
        }

        const bias_factor = @abs(self.angles.x - bias.x);
        var bias_input = Vec2.new(0, 0);
        if (bias_factor < pi / 3) {
            bias_input.x = 0;
        } else if (self.angles.x > bias.x) {
            bias_input.x = -bias_factor * BIAS_STRENGTH;
        } else {
            bias_input.x = bias_factor * BIAS_STRENGTH;
        }

        if (!std.math.isNan(bias.y)) {
            const bias_factor_y = @abs(self.angles.x - bias.x);
            if (bias_factor_y < pi / 3) {
                bias_input.x = 0;
            } else if (self.angles.y > bias.x) {
                bias_input.y = -bias_factor_y * BIAS_STRENGTH;
            } else {
                bias_input.y = bias_factor_y * BIAS_STRENGTH;
            }
        }

        var straight_chance = (self.width / (sqrt(1 / (MAX_STRAIGHT_CHANCE - MIN_STRAIGHT_CHANCE)) * MAX_WIDTH)) ** 2 + MIN_STRAIGHT_CHANCE;
        if (self.width >= 0.9 * MAX_WIDTH and inarow < 10) {
            straight_chance = 1;
        }
        const n = MAX_WIDTH;
        if (rng.random().float() > straight_chance or inarow > (-5 / (n - 1) * self.width + 5 / (n - 1) * n + 8)) {
            self.branch(bias_input, rng, alloc);
        } else {
            self.go_straight(bias_input, rng, alloc);
        }
    }
};

fn end_pos(root: *Section) struct { f64, f64 } {
    const end_x = root.length * std.math.cos(root.angle);
    const end_y = root.length * std.math.sin(root.angle);
    return .{ end_x + root.x, end_y + root.y };
}

fn tree(root: *Section, rng: *RndGen, alloc: Allocator) !void {
    assert(root.children[0] == null);
    assert(root.children[1] == null);
    if (root.width < 1) {
        return;
    }
    const branch = rng.random().intRangeAtMost(usize, 1, 2) == 1;
    const end_x, const end_y = end_pos(root);
    if (branch) {
        var left_angle: f64 = 0.0;
        var right_angle: f64 = 0.0;
        var left_width: f64 = 0.0;
        var right_width: f64 = 0.0;
        const branch_mode = rng.random().float(f64);
        if (branch_mode < 0.7) {
            // one branch goes to the left/right
            // this one is the one that carries on
            left_angle = root.angle + (rng.random().float(f64) * (std.math.pi / 8.0) - std.math.pi / 16.0);
            // this one goes to one direction or the other
            var right_angle_temp = root.angle + (rng.random().float(f64) - 0.5) * (std.math.pi / 6.0);
            if (right_angle_temp < 0) {
                right_angle_temp -= std.math.pi / 5.0;
            } else {
                right_angle_temp += std.math.pi / 5.0;
            }
            right_angle = right_angle_temp;

            right_width = (rng.random().float(f64) * 0.3);
            left_width = root.width - right_width;
        } else {
            // branches split equally ish
            left_angle = root.angle + (rng.random().float(f64) * (std.math.pi / 6.0) + std.math.pi / 12.0);
            right_angle = root.angle - (rng.random().float(f64) * (std.math.pi / 6.0) + std.math.pi / 12.0);

            const min_ratio = 0.4;
            left_width = (rng.random().float(f64) * (1 - min_ratio) + min_ratio / 2.0) * root.width;
            right_width = root.width - left_width;
        }

        const extra = 1.2;
        const left = try alloc.create(Section);
        const right = try alloc.create(Section);

        left.* = Section{ .x = end_x, .y = end_y, .angle = left_angle, .length = @round(left_width * 2), .width = left_width * extra, .children = .{ null, null } };
        right.* = Section{ .x = end_x, .y = end_y, .angle = right_angle, .length = @round(right_width * 2), .width = right_width * extra, .children = .{ null, null } };
        try tree(left, rng, alloc);
        try tree(right, rng, alloc);
        root.children[0] = left;
        root.children[1] = right;
    } else {
        const angle = root.angle + (rng.random().float(f64) * (std.math.pi / 8.0) - std.math.pi / 16.0);
        const next = try alloc.create(Section);
        next.* = Section{ .x = end_x, .y = end_y, .angle = angle, .length = root.length, .width = root.width, .children = .{ null, null } };
        try tree(next, rng, alloc);
        root.children[0] = next;
    }
}

fn draw(root: *Section, buffer: []u8) void {
    for (0..@intFromFloat(root.length)) |n| {
        std.debug.print("{} {} {}\n", .{ n, root.angle, @as(f64, @floatFromInt(n)) * std.math.sin(root.angle) });
        const end_x: f64 = @as(f64, @floatFromInt(n)) * std.math.cos(root.angle);
        const end_y: f64 = @as(f64, @floatFromInt(n)) * std.math.sin(root.angle);
        const ex = @as(i16, @intFromFloat(end_x + root.x));
        const ey = @as(i16, @intFromFloat(end_y + root.y));
        // for (0..@intFromFloat(root.width)) |bx| {
        //     for (0..@intFromFloat(root.width)) |by| {
        const bx2: i16 = 0; // @intCast(bx);
        const by2: i16 = 0; // @intCast(by);
        if (ey + by2 >= 128 or ex + bx2 >= 1280 or ey + by2 < 0 or ex + bx2 < 0) {
            continue;
        }
        buffer[@as(usize, @intCast(ey + by2)) * 1280 + @as(usize, @intCast(ex + bx2))] = 255; //@intFromFloat(255.0 / 8.0 * root.width);
        //     }
        // }
    }
    if (root.children[0]) |child| {
        draw(child, buffer);
    }
    if (root.children[1]) |child| {
        draw(child, buffer);
    }
}

pub fn main() !void {
    var rnd = RndGen.init(0);

    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var buffer: [128 * 128 * 10]u8 = undefined;
    @memset(&buffer, 0);

    for (0..10) |n| {
        var root = Section{ .x = 128.0 * @as(f64, @floatFromInt(n)) + 64.0, .y = 100, .angle = -std.math.pi / 2.0, .width = 4, .children = .{ null, null }, .length = 2 };
        tree(&root, &rnd, allocator) catch {
            std.debug.print("Out of memory", .{});
        };
        draw(&root, &buffer);
    }

    var image = try zigimg.Image.fromRawPixels(allocator, 128 * 10, 128, buffer[0..], .grayscale8);
    defer image.deinit();
    try image.writeToFilePath("image.png", .{ .png = .{} });
}
