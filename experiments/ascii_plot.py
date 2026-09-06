from lazydata.plot.render_ascii import AsciiCanvasRenderer
from lazydata.plot.splot import SplotAx, SplotCanvas, SplotCoordSys2D, SplotLayout
from lazydata.plot.splot_elements import SplotLine2d, SplotMarker, SplotPoint2d

# points
points = [
    SplotPoint2d((1, 1)),
    SplotPoint2d((3, 1)),
    SplotPoint2d((5, 6), SplotMarker.CROSS),
    SplotPoint2d((18, 8), SplotMarker.STAR),
    SplotLine2d((7, 8), (18, 8)),
    SplotLine2d((5, 6), (10, 0)),
]

print("points")
for p in points:
    print(f"  {p}")

coords = SplotCoordSys2D((0, 20), (0, 10))

ax = SplotAx(coords)
ax.elements.extend(points)
canv = SplotCanvas(SplotLayout.single(ax))


out = AsciiCanvasRenderer()(canv)

print("\n")
print(out)
