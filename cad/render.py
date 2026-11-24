"""Off-screen VTK renders (trimmed from the LF-01 tooling, LineFollowerRobot cad/buildtools.py)."""
from __future__ import annotations

import os

import export3mf

COLORS = {
    "graphite": (0.21, 0.22, 0.25),     # the ring (PETG, dark)
    "livery": (1.00, 0.80, 0.00),       # logo inlay, house yellow #FFCC00
    "spool": (0.66, 0.68, 0.71),        # the customer's spool (illustration)
    "filament": (0.05, 0.62, 0.78),     # filament on the spool (illustration)
    "bed": (0.78, 0.79, 0.80),          # build plate (light, for contrast)
    "roller": (0.55, 0.57, 0.60),
}

_POLY = {}


def _matrix(loc):
    import vtk
    t = loc.wrapped.Transformation()
    mat = vtk.vtkMatrix4x4()
    for i in range(3):
        for j in range(4):
            mat.SetElement(i, j, t.Value(i + 1, j + 1))
    return mat


def _poly(shape, tol):
    import numpy as np
    import vtk
    from vtk.util import numpy_support as ns
    key = (id(shape), tol)
    if key not in _POLY:
        verts, tris = export3mf.mesh(shape, tol, 0.2)
        pts = vtk.vtkPoints()
        pts.SetData(ns.numpy_to_vtk(np.asarray(verts, dtype=np.float64), deep=True))
        t = np.asarray(tris, dtype=np.int64).reshape(-1, 3)
        conn = np.hstack([np.full((len(t), 1), 3, dtype=np.int64), t]).ravel()
        cells = vtk.vtkCellArray()
        cells.SetCells(len(t), ns.numpy_to_vtkIdTypeArray(conn, deep=True))
        pd = vtk.vtkPolyData()
        pd.SetPoints(pts)
        pd.SetPolys(cells)
        nf = vtk.vtkPolyDataNormals()
        nf.SetInputData(pd)
        nf.SetFeatureAngle(32)
        nf.SplittingOn()
        nf.Update()
        _POLY[key] = (shape, nf.GetOutput(), pd)
    return _POLY[key][1], _POLY[key][2]


def render(items, path, cam, focal, size=(1600, 1100), zoom=1.0, up=(0, 0, 1), edges=True,
           bg=((0.97, 0.97, 0.98), (0.82, 0.85, 0.89)), tol=None):
    """items: list of (shape, cq.Location or None, colour key). Light gradient background."""
    import vtk
    ren = vtk.vtkRenderer()
    ren.GradientBackgroundOn()
    ren.SetBackground(*bg[1])
    ren.SetBackground2(*bg[0])
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.AddRenderer(ren)
    for shape, loc, ckey in items:
        t = tol or (0.03 if shape.BoundingBox().DiagonalLength < 60 else 0.06)
        pd, welded = _poly(shape, t)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(pd)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        if loc is not None:
            actor.SetUserMatrix(_matrix(loc))
        pr = actor.GetProperty()
        pr.SetColor(*COLORS[ckey])
        pr.SetAmbient(0.30)
        pr.SetDiffuse(0.80)
        pr.SetSpecular(0.18)
        pr.SetSpecularPower(20)
        ren.AddActor(actor)
        if edges:
            fe = vtk.vtkFeatureEdges()
            fe.SetInputData(welded)
            fe.BoundaryEdgesOff()
            fe.ManifoldEdgesOff()
            fe.NonManifoldEdgesOff()
            fe.FeatureEdgesOn()
            fe.SetFeatureAngle(38)
            em = vtk.vtkPolyDataMapper()
            em.SetInputConnection(fe.GetOutputPort())
            em.ScalarVisibilityOff()
            ea = vtk.vtkActor()
            ea.SetMapper(em)
            if loc is not None:
                ea.SetUserMatrix(_matrix(loc))
            ea.GetProperty().SetColor(0.05, 0.05, 0.06)
            ea.GetProperty().SetOpacity(0.35)
            ea.GetProperty().SetLineWidth(1.0)
            ren.AddActor(ea)
    c = ren.GetActiveCamera()
    c.SetFocalPoint(*focal)
    c.SetPosition(*cam)
    c.SetViewUp(*up)
    ren.ResetCamera()
    c.SetFocalPoint(*focal)
    c.Zoom(zoom)
    ren.ResetCameraClippingRange()
    key = vtk.vtkLight()
    key.SetLightTypeToCameraLight()
    key.SetPosition(0.6, 0.8, 1.0)
    key.SetIntensity(0.75)
    ren.AddLight(key)
    fill = vtk.vtkLight()
    fill.SetLightTypeToSceneLight()
    fill.SetPosition(-1500, -800, 2500)
    fill.SetFocalPoint(*focal)
    fill.SetIntensity(0.40)
    ren.AddLight(fill)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wr = vtk.vtkPNGWriter()
    wr.SetFileName(path)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()
