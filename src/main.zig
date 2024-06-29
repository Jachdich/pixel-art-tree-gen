const std = @import("std");
const assert = std.debug.assert;
const RndGen = std.rand.DefaultPrng;
const Allocator = std.mem.Allocator;
const zigimg = @import("zigimg");

const Section = struct {
    x: f64,
    y: f64,
    angle: f64,
    width: f64,
    length: f64,
    children: [2]?*Section,
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
    // const stdout_file = std.io.getStdOut().writer();
    // var bw = std.io.bufferedWriter(stdout_file);
    // const stdout = bw.writer();

    // try stdout.print("Run `zig build test` to run the tests.\n", .{});

    // try bw.flush(); // don't forget to flush!

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

test "simple test" {
    var list = std.ArrayList(i32).init(std.testing.allocator);
    defer list.deinit(); // try commenting this out and see if zig detects the memory leak!
    try list.append(42);
    try std.testing.expectEqual(@as(i32, 42), list.pop());
}
