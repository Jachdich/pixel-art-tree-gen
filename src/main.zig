const std = @import("std");
const assert = std.debug.assert;
const RndGen = std.rand.DefaultPrng;
const Random = std.Random;
const Allocator = std.mem.Allocator;
const zigimg = @import("zigimg");
const sin = std.math.sin;
const cos = std.math.cos;
const pi = std.math.pi;
const sqrt = std.math.sqrt;
const pow = std.math.pow;

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
    bias: Vec2,
    pos: Vec3,
    end_pos: Vec3,
    children: [2]?*Section,

    pub fn new(width: f64, pos: Vec3, angles: Vec2) Section {
        return Section{
            .angles = angles,
            .width = width,
            .bias = Vec2.new(0, 0),
            .children = .{ null, null },
            .end_pos = Vec3.from_spherical(angles).scale(LENGTH).add(pos),
            .pos = pos,
        };
    }

    pub fn tree(self: *Section, inarow: usize, bias: Vec2, is_trunk: bool, rng: Random, alloc: Allocator) !void {
        self.bias = bias;
        // self.inarow = inarow;
        // self.is_trunk = is_trunk;
        _ = is_trunk;
        if (self.width < 1) {
            // make leaves
            return;
        }

        const bias_factor = @abs(self.angles.x - bias.x);
        var bias_input = Vec2.new(0, 0);
        if (bias_factor < pi / 3.0) {
            bias_input.x = 0;
        } else if (self.angles.x > bias.x) {
            bias_input.x = -bias_factor * BIAS_STRENGTH;
        } else {
            bias_input.x = bias_factor * BIAS_STRENGTH;
        }

        if (!std.math.isNan(bias.y)) {
            const bias_factor_y = @abs(self.angles.x - bias.x);
            if (bias_factor_y < pi / 3.0) {
                bias_input.x = 0;
            } else if (self.angles.y > bias.x) {
                bias_input.y = -bias_factor_y * BIAS_STRENGTH;
            } else {
                bias_input.y = bias_factor_y * BIAS_STRENGTH;
            }
        }

        var straight_chance = pow(f64, self.width / (sqrt(1.0 / (MAX_STRAIGHT_CHANCE - MIN_STRAIGHT_CHANCE)) * MAX_WIDTH), 2) + MIN_STRAIGHT_CHANCE;
        if (self.width >= 0.9 * MAX_WIDTH and inarow < 10) {
            straight_chance = 1;
        }
        const n = MAX_WIDTH;
        if (rng.float(f64) > straight_chance or @floatFromInt(inarow) > (-5 / (n - 1) * self.width + 5 / (n - 1) * n + 8)) {
            try self.branch(bias_input, rng, alloc);
        } else {
            try self.go_straight(bias_input, rng, alloc);
        }
    }

    fn straight_branch_angles(self: *Section, bias_input: Vec2, rng: Random) Vec2 {
        return Vec2.new(
            self.angles.x + rng.floatNorm(f64) * pi / 18 + bias_input.x,
            self.angles.y + rng.floatNorm(f64) * pi / 18 + bias_input.y,
        );
    }

    fn go_straight(self: *Section, bias_input: Vec2, rng: std.Random, alloc: Allocator) !void {
        const angles = self.straight_branch_angles(bias_input, rng);
        _ = .{ self, rng, alloc, angles };
    }
    fn branch(self: *Section, bias_input: Vec2, rng: std.Random, alloc: Allocator) !void {
        _ = .{ self, rng, alloc, bias_input };
    }
};

// fn end_pos(root: *Section) struct { f64, f64 } {
//     const end_x = root.length * std.math.cos(root.angle);
//     const end_y = root.length * std.math.sin(root.angle);
//     return .{ end_x + root.x, end_y + root.y };
// }

// fn draw(root: *Section, buffer: []u8) void {
//     for (0..@intFromFloat(root.length)) |n| {
//         std.debug.print("{} {} {}\n", .{ n, root.angle, @as(f64, @floatFromInt(n)) * std.math.sin(root.angle) });
//         const end_x: f64 = @as(f64, @floatFromInt(n)) * std.math.cos(root.angle);
//         const end_y: f64 = @as(f64, @floatFromInt(n)) * std.math.sin(root.angle);
//         const ex = @as(i16, @intFromFloat(end_x + root.x));
//         const ey = @as(i16, @intFromFloat(end_y + root.y));
//         // for (0..@intFromFloat(root.width)) |bx| {
//         //     for (0..@intFromFloat(root.width)) |by| {
//         const bx2: i16 = 0; // @intCast(bx);
//         const by2: i16 = 0; // @intCast(by);
//         if (ey + by2 >= 128 or ex + bx2 >= 1280 or ey + by2 < 0 or ex + bx2 < 0) {
//             continue;
//         }
//         buffer[@as(usize, @intCast(ey + by2)) * 1280 + @as(usize, @intCast(ex + bx2))] = 255; //@intFromFloat(255.0 / 8.0 * root.width);
//         //     }
//         // }
//     }
//     if (root.children[0]) |child| {
//         draw(child, buffer);
//     }
//     if (root.children[1]) |child| {
//         draw(child, buffer);
//     }
// }

pub fn main() !void {
    var rnd = RndGen.init(0);

    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();

    var buffer: [128 * 128 * 10]u8 = undefined;
    @memset(&buffer, 0);

    for (0..10) |n| {
        var root = Section.new(MAX_WIDTH, Vec3.new(@as(f64, @floatFromInt(n)) * 128.0 + 64.0, 0.0, 0.0), Vec2.new(0.0, 0.0));
        root.tree(0, Vec2.new(0, std.math.nan(f64)), true, rnd.random(), allocator) catch {
            std.debug.print("Out of memory", .{});
        };
        // draw(&root, &buffer);
    }

    var image = try zigimg.Image.fromRawPixels(allocator, 128 * 10, 128, buffer[0..], .grayscale8);
    defer image.deinit();
    try image.writeToFilePath("image.png", .{ .png = .{} });
}
