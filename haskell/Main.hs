import Data.IORef
import Graphics.Rendering.OpenGL qualified as GL
import Control.Monad (forM_, forM, replicateM_, when)
import Graphics.UI.GLUT

canvasSize = 128

displayScale = 8

-- data Vec2 = Vec2 {v2x :: Float, v2y :: Float}

-- data Vec3 = Vec3 {v3x :: Float, v3y :: Float, v3z :: Float}

type Vec2 = (Float, Float)

type Vec3 = (Float, Float, Float)

x = fst

y = snd

z (a, b, c) = c

data Tree = Tree {branches :: Section, leaves :: [Vec3], pos :: Vec2}

data Section = Section {children :: [Section], width :: Float, angles :: Vec2}

data Model = Model
  { view_angles :: Vec2,
    tree :: Tree
  }

makeTree :: IO Tree
makeTree = undefined

initial = do Model (0, 0) <$> makeTree

main :: IO ()
main = do
  model <- initial
  getArgsAndInitialize
  initialDisplayMode $= [SingleBuffered, RGBMode]
  initialWindowSize $= Size (fromIntegral (canvasSize * displayScale)) (fromIntegral (canvasSize * displayScale))
  state <- newIORef model
  createWindow "Test"
  displayCallback $= draw state
  idleCallback $= Just (idle state)
  motionCallback $= Just (mouse state)
  mainLoop

draw :: IORef Model -> DisplayCallback
draw state = do
  clear [ColorBuffer]
  s <- get state
  drawModel s
  swapBuffers

idle :: IORef Model -> IdleCallback
idle state = do
  model <- get state
  postRedisplay Nothing

drawModel model = renderPrimitive Quads $ do
  forM_ [0..canvasSize] $ \i -> do
    vertex $ Vertex2 0 (x $ pos $ tree model)
    vertex $ Vertex2 0 (x $ pos $ tree model)
    vertex $ Vertex2 0 (x $ pos $ tree model)
    vertex $ Vertex2 0 (x $ pos $ tree model)

mouse :: IORef Model -> Position -> IO ()
mouse state (Position x y) = do
    model <- get state
    writeIORef state model