import vtk

class colorbar_param:
    def __init__(self, title="No Title",
                 title_color=[1,1,1],
                 label_color=[1,1,1],
                 pos=[0.9,0.5],
                 width=80,
                 height=400,
                 nlabels=4,
                 font_size=22,
                 title_offset=20):
        self.title = title
        self.title_color = title_color
        self.label_color = label_color
        self.pos = pos
        self.width = width
        self.height = height
        self.nlabels = nlabels
        self.font_size = font_size
        self.title_offset = title_offset

class colorbar:
    def __init__(self, ctf, param=colorbar_param(), is_float=True):
        self.param = param
        self.scalarbar = vtk.vtkScalarBarActor()
        self.scalarbar.SetLookupTable(ctf)
        self.scalarbar.SetPosition(param.pos[0], param.pos[1])
        self.set_size(width=param.width, height=param.height)
        self.set_title(title=param.title, size=param.font_size, color=param.title_color)
        self.scalarbar.SetVerticalTitleSeparation(param.title_offset)

        # label properties
        self.set_label(nlabels=param.nlabels, color=param.label_color,
                       size=param.font_size, is_float=is_float)

    def get(self):
        return self.scalarbar

    # functions to override the parameters provided to the constructor
    def set_position(self, pos):
        self.scalarbar.SetPosition(pos[0], pos[1])

    def set_lookup_table(self, ctf):
        self.scalarbar.SetLookupTable(ctf)

    def set_size(self, width, height):
        self.scalarbar.SetMaximumWidthInPixels(width)
        self.scalarbar.SetMaximumHeightInPixels(height)

    def set_title(self, title='', size=22, color=[1,1,1], offset=20):
        self.scalarbar.SetTitle(title)
        self.scalarbar.GetTitleTextProperty().SetColor(color[0],
                                                       color[1],
                                                       color[2])
        self.scalarbar.GetTitleTextProperty().ShadowOff()
        self.scalarbar.GetTitleTextProperty().SetFontSize(size)
        self.scalarbar.GetTitleTextProperty().BoldOn()
        self.scalarbar.SetVerticalTitleSeparation(offset)

    def set_label(self, nlabels=4, color=[1,1,1], size=22, is_float=True):
        self.scalarbar.SetNumberOfLabels(nlabels)
        self.scalarbar.SetLabelFormat("%0.2f" if is_float else "%0.0f")
        self.scalarbar.GetLabelTextProperty().SetColor(color[0],
                                                       color[1],
                                                       color[2])
        self.scalarbar.GetLabelTextProperty().SetFontSize(size)
        self.scalarbar.GetLabelTextProperty().BoldOff()
        self.scalarbar.GetLabelTextProperty().ShadowOff()

if __name__ == "__main__":
    import numpy as np
    import vtk.util.numpy_support
    import math

    # testing
    ctf = vtk.vtkColorTransferFunction()
    ctf.AddRGBPoint(-1, 0, 0, 1)
    ctf.AddRGBPoint(0, 1, 1, 1)
    ctf.AddRGBPoint(1, 1, 0, 0)

    bar = colorbar(ctf)
    bar.set_title("Test")

    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(0,0,0)
    plane.SetPoint1(1,0,0)
    plane.SetPoint2(0,1,0)
    plane.SetResolution(100, 100)

    values = np.zeros((10000,), dtype=float)
    for i in range(100):
        for j in range(100):
            values[i*100+j] = math.sin(i/10) + math.cos(j/10)

    vals = vtk.util.numpy_support.numpy_to_vtk(values)
    vals.SetName('values')
    plane.Update()
    aplane = plane.GetOutput()
    aplane.GetPointData().AddArray(vals)
    aplane.GetPointData().SetActiveScalars('values')

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(aplane)
    mapper.SetLookupTable(ctf)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.AddActor2D(bar.get())
    renderer.SetBackground(0,0,0)
    window = vtk.vtkRenderWindow()
    window.SetSize(1024, 1024)
    window.AddRenderer(renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(window)
    interactor.Initialize()
    window.Render()
    interactor.Start()