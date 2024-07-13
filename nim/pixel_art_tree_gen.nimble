# Package

version = "0.1.0"
author = "cospox"
description = "pixel_art_tree_gen"
license = "?"

# Deps
requires "nim >= 1.2.0"
requires "nico >= 0.2.5"

srcDir = "src"

import strformat

const releaseOpts = "-d:danger"
const debugOpts = "-d:debug"

task runr, "Runs pixel_art_tree_gen for current platform":
 exec &"nim c -r {releaseOpts} -o:pixel_art_tree_gen src/main.nim"

task rund, "Runs debug pixel_art_tree_gen for current platform":
 exec &"nim c -r {debugOpts} -o:pixel_art_tree_gen src/main.nim"

task release, "Builds pixel_art_tree_gen for current platform":
 exec &"nim c {releaseOpts} -o:pixel_art_tree_gen src/main.nim"

task debug, "Builds debug pixel_art_tree_gen for current platform":
 exec &"nim c {debugOpts} -o:pixel_art_tree_gen_debug src/main.nim"

task deps, "Downloads dependencies":
 if defined(windows):
  if not fileExists("SDL2.dll"):
   if not fileExists("SDL2_x64.zip"):
    exec "curl https://www.libsdl.org/release/SDL2-2.0.20-win32-x64.zip -o SDL2_x64.zip"
   if findExe("tar") != "":
    exec "tar -xf SDL2_x64.zip SDL2.dll"
   else:
    exec "unzip SDL2_x64.zip SDL2.dll"
  if fileExists("SDL2_x64.zip"):
   rmFile("SDL2_x64.zip")
 elif defined(macosx) and findExe("brew") != "":
  exec "brew list sdl2 || brew install sdl2"
 else:
  echo "I don't know how to install SDL on your OS! 😿"
