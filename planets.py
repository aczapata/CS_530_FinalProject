#!/usr/bin/env python

# This example shows how to combine data from both the imaging and
# graphics pipelines. The vtkMergeFilter is used to merge the data
# from each together.

import vtk
from vtk.util.misc import vtkGetDataRoot
VTK_DATA_ROOT = vtkGetDataRoot()


import sys


# Purdue CS530 - Introduction to Scientific Visualization
# Spring 2021

# Simple example showing how to use PyQt5 to manipulate
# a visualization

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import argparse
import sys
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk.util.numpy_support
import colorbar

frame_counter = 0

class MySphere(VTKPythonAlgorithmBase):
	def __init__(self):
		VTKPythonAlgorithmBase.__init__(self,
			  nInputPorts=0,
			  nOutputPorts=1, outputType='vtkPolyData')
		self.theta = 10
		self.phi = 10
		self.center = [ 0, 0, 0]
		self.radius = 1
		self.modified = True

	def ComputeLatitude(self):
		coords = vtk.util.numpy_support.vtk_to_numpy(self.sphere.GetPoints().GetData())
		values = coords[:,2]*90
		data = vtk.util.numpy_support.numpy_to_vtk(values)
		data.SetName('latitude')
		self.sphere.GetPointData().AddArray(data)
		self.sphere.GetPointData().SetActiveScalars('latitude')

	def Update(self):
		sphere_src = vtk.vtkSphereSource()
		sphere_src.SetCenter(self.center)
		sphere_src.SetRadius(self.radius)
		sphere_src.SetThetaResolution(self.theta)
		sphere_src.SetPhiResolution(self.phi)
		sphere_src.Update()
		self.sphere = sphere_src.GetOutput()
		self.ComputeLatitude()

	def SetThetaResolution(self, theta):
		self.theta = theta
		self.Modified()

	def SetPhiResolution(self, phi):
		self.phi = phi
		self.Modified()

	def SetCenter(self, center):
		self.center = center
		self.Modified()

	def SetRadius(self, radius):
		self.radius = radius
		self.Modified()

	def RequestData(self, request, inInfo, outInfo):
		print('Executing')
		output = vtk.vtkPolyData.GetData(outInfo)
		self.Update()
		output.ShallowCopy(self.sphere)

		print('output\n{}'.format(output))

		return 1


def save_frame(window, log):
	global frame_counter
	global args
	# ---------------------------------------------------------------
	# Save current contents of render window to PNG file
	# ---------------------------------------------------------------
	file_name = args.output + str(frame_counter).zfill(5) + ".png"
	image = vtk.vtkWindowToImageFilter()
	image.SetInput(window)
	png_writer = vtk.vtkPNGWriter()
	png_writer.SetInputConnection(image.GetOutputPort())
	png_writer.SetFileName(file_name)
	window.Render()
	png_writer.Write()
	frame_counter += 1
	if args.verbose:
		print(file_name + " has been successfully exported")
	log.insertPlainText('Exported {}\n'.format(file_name))

def print_camera_settings(camera, text_window, log):
	# ---------------------------------------------------------------
	# Print out the current settings of the camera
	# ---------------------------------------------------------------
	text_window.setHtml("<div style='font-weight:bold'>Camera settings:</div><p><ul><li><div style='font-weight:bold'>Position:</div> {0}</li><li><div style='font-weight:bold'>Focal point:</div> {1}</li><li><div style='font-weight:bold'>Up vector:</div> {2}</li><li><div style='font-weight:bold'>Clipping range:</div> {3}</li></ul>".format(camera.GetPosition(), camera.GetFocalPoint(),camera.GetViewUp(),camera.GetClippingRange()))
	log.insertPlainText('Updated camera info\n');

def make_sphere():
	# create and visualize sphere
	sphere_source = MySphere()
	sphere_source.SetRadius(1.0)
	sphere_source.SetCenter([0.0, 0.0, 0.0])
	sphere_source.SetThetaResolution(100)
	sphere_source.SetPhiResolution(100)

	# extract and visualize the edges
	#edge_extractor = vtk.vtkExtractEdges()
	#edge_extractor.SetInputConnection(sphere_source.GetOutputPort())
	#edge_tubes = vtk.vtkTubeFilter()
	#edge_tubes.SetRadius(0.001)
	#edge_tubes.SetInputConnection(edge_extractor.GetOutputPort())
	return sphere_source


class Ui_MainWindow(object):
	def setupUi(self, MainWindow):
		MainWindow.setObjectName('The Main Window')
		MainWindow.setWindowTitle('VTK + PyQt5 + vtkPythonAlgorithm Example')
		# in Qt, windows are made of widgets.
		# centralWidget will contains all the other widgets
		self.centralWidget = QWidget(MainWindow)
		# we will organize the contents of our centralWidget
		# in a grid / table layout
		# Here is a screenshot of the layout:
		# https://www.cs.purdue.edu/~cs530/projects/img/PyQtGridLayout.png
		self.gridlayout = QGridLayout(self.centralWidget)
		# vtkWidget is a widget that encapsulates a vtkRenderWindow
		# and the associated vtkRenderWindowInteractor. We add
		# it to centralWidget.
		self.vtkWidget = QVTKRenderWindowInteractor(self.centralWidget)
		# Sliders
		self.slider_theta = QSlider()
		#self.slider_phi = QSlider()
		#self.slider_radius = QSlider()
		# Push buttons
		self.push_screenshot = QPushButton()
		self.push_screenshot.setText('Save screenshot')
		self.push_camera = QPushButton()
		self.push_camera.setText('Update camera info')
		self.push_quit = QPushButton()
		self.push_quit.setText('Quit')
		# Text windows
		self.camera_info = QTextEdit()
		self.camera_info.setReadOnly(True)
		self.camera_info.setAcceptRichText(True)
		self.camera_info.setHtml("<div style='font-weight: bold'>Camera settings</div>")
		self.log = QTextEdit()
		self.log.setReadOnly(True)
		# We are now going to position our widgets inside our
		# grid layout. The top left corner is (0,0)
		# Here we specify that our vtkWidget is anchored to the top
		# left corner and spans 3 rows and 4 columns.
		self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
		self.gridlayout.addWidget(QLabel("Scale"), 4, 0, 1, 1)
		self.gridlayout.addWidget(self.slider_theta, 4, 1, 1, 1)
		#self.gridlayout.addWidget(QLabel("Phi resolution"), 5, 0, 1, 1)
		#self.gridlayout.addWidget(self.slider_phi, 5, 1, 1, 1)
		#self.gridlayout.addWidget(QLabel("Edge radius"), 4, 2, 1, 1)
		#self.gridlayout.addWidget(self.slider_radius, 4, 3, 1, 1)
		self.gridlayout.addWidget(self.push_screenshot, 0, 5, 1, 1)
		self.gridlayout.addWidget(self.push_camera, 1, 5, 1, 1)
		self.gridlayout.addWidget(self.camera_info, 2, 4, 1, 2)
		self.gridlayout.addWidget(self.log, 3, 4, 1, 2)
		self.gridlayout.addWidget(self.push_quit, 5, 5, 1, 1)
		MainWindow.setCentralWidget(self.centralWidget)

class PyQtDemo(QMainWindow):

	def __init__(self, imageFile, parent = None):
		QMainWindow.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.scale = 0.1

		'''
		#luminance = vtk.vtkImageLuminance()
		#luminance.SetInputConnection(reader.GetOutputPort())
		#geometry = vtk.vtkImageDataGeometryFilter()
		#geometry.SetInputConnection(luminance.GetOutputPort())
		readerEle = vtk.vtkXMLPolyDataReader()
		readerEle.SetFileName(elevationFile)

		

		merge = vtk.vtkMergeFilter()
		merge.SetGeometryConnection(self.sphere.GetOutputPort())
		merge.SetScalarsConnection(readerEle.GetOutputPort())
		
		self.warp = vtk.vtkWarpScalar()
		self.warp.SetInputConnection(readerEle.GetOutputPort())
		#self.warp.XYPlaneOn()
		#self.warp.UseNormalOn()
		#self.warp.SetNormal(0,0,1)
		#self.warp.SetInputConnection(self.xform.GetOutputPort())
		self.warp.SetScaleFactor(self.scale)

		# Use vtkMergeFilter to combine the original image with the warped
		# geometry.
		#merge = vtk.vtkMergeFilter()
		#merge.SetGeometryConnection(self.warp.GetOutputPort())
		#merge.SetScalarsConnection(readerEle.GetOutputPort())
		'''

		self.sphere = make_sphere()

		reader = vtk.vtkJPEGReader()
		reader.SetFileName(imageFile)

		texture = vtk.vtkTexture()
		texture.SetInputConnection(reader.GetOutputPort())
		texture.InterpolateOn()
		
		mapper = vtk.vtkDataSetMapper()
		mapper.SetInputConnection(self.sphere.GetOutputPort())
		#mapper.SetInputConnection(readerEle.GetOutputPort())
		mapper.ScalarVisibilityOff()
		#mapper.SetScalarRange(-255, 255)

		triang = vtk.vtkActor()
		triang.SetMapper(mapper)
		triang.SetTexture(texture)

		
		'''
		contour = vtk.vtkContourFilter()
		contour.SetInputConnection(readerEle.GetOutputPort())
		contour.GenerateValues(18,-10000,8000)

		
		self.tubeWarp = vtk.vtkWarpScalar()
		self.tubeWarp.SetInputConnection(contour.GetOutputPort())
		self.tubeWarp.SetScaleFactor(self.scale)

		stripper = vtk.vtkStripper()
		stripper.SetInputConnection(self.tubeWarp.GetOutputPort())

		self.tube = vtk.vtkTubeFilter()
		self.tube.SetNumberOfSides(50)
		self.radius = 10000
		self.tube.SetRadius(self.radius)
		self.tube.SetInputConnection(stripper.GetOutputPort())
		self.tube.Update()
		'''

		ctf = vtk.vtkColorTransferFunction()
		ctf.AddRGBPoint(-10000,0,0,1)
		#ctf.AddRGBPoint(0.1, 1, 1, 1)
		ctf.AddRGBPoint(0, 1, 1, 1)
		#ctf.AddRGBPoint(-0.1, 1, 1, 1)
		ctf.AddRGBPoint(8000, 1, 1, 0)
	

		bar = colorbar.colorbar(ctf)
		bar.set_label(nlabels=7, size=10)
		bar.set_position([0.9, 0.5])
		bar.set_size(width=80, height=300)
		bar.set_title(title="Elevation", size=10)

		'''
		mapperTube = vtk.vtkDataSetMapper()
		mapperTube.SetInputConnection(self.tube.GetOutputPort())
		mapperTube.SetLookupTable(ctf)
		actor = vtk.vtkActor()
		actor.SetMapper(mapperTube)
		actor.GetProperty().SetColor(1,0,0)
		'''



		# Create the Renderer
		self.ren = vtk.vtkRenderer()
		self.ren.AddActor(triang)
		#self.ren.AddActor(actor)
		self.ren.AddActor2D(bar.get())
		
		self.ren.GradientBackgroundOn()  # Set gradient for background
		self.ren.SetBackground(0.75, 0.75, 0.75)  # Set background to silver

		'''
		cam1 = self.ren.GetActiveCamera()
		cam1.SetPosition(-9490969.44074634, 26511189.024747908, 16490507.766397746)
		#cam1.SetFocalPoint(19967962.0, 9983981.0, 129.9000244140625)
		cam1.SetViewUp(0,-1,0)
		cam1.SetClippingRange(8261883.54280564, 50580834.84176244)
		'''

		self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
		self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()

		# Setting up widgets
		def slider_setup(slider, val, bounds, interv):
			slider.setOrientation(QtCore.Qt.Horizontal)
			slider.setValue(float(val))
			slider.setTracking(False)
			slider.setTickInterval(interv)
			slider.setTickPosition(QSlider.TicksAbove)
			slider.setRange(bounds[0], bounds[1])

		slider_setup(self.ui.slider_theta, self.scale, [1, 255], 20)

	def theta_callback(self, val):
		self.theta = val
		self.scale = val
		self.radius = val
		#self.sphere.SetThetaResolution(self.theta)
		#self.sphere.SetThetaResolution(self.scale)
		#self.tubeWarp.SetScaleFactor(self.scale)
		#self.warp.SetScaleFactor(self.scale)
		#self.ui.log.insertPlainText('Theta resolution set to {}\n'.format(self.theta))
		self.ui.log.insertPlainText('Scale set to {}\n'.format(self.radius))
		self.ui.vtkWidget.GetRenderWindow().Render()

	def screenshot_callback(self):
		save_frame(self.ui.vtkWidget.GetRenderWindow(), self.ui.log)

	def camera_callback(self):
		print_camera_settings(self.ren.GetActiveCamera(), self.ui.camera_info, self.ui.log)

	def quit_callback(self):
		sys.exit()

if __name__=="__main__":

	#elevationFile = sys.argv[1]
	#imageFile = sys.argv[2]
	imageFile = "Data/world.topo.bathy.200408.medium.jpg"

	'''
	global args

	parser = argparse.ArgumentParser(
		description='Illustrate the use of PyQt5 with VTK')
	parser.add_argument('-r', '--resolution', type=int, metavar='int', nargs=2, help='Image resolution', default=[1024, 768])
	parser.add_argument('-o', '--output', type=str, metavar='filename', help='Base name for screenshots', default='frame_')
	parser.add_argument('-v', '--verbose', action='store_true', help='Toggle on verbose output')

	args = parser.parse_args()
	'''

	app = QApplication(sys.argv)
	window = PyQtDemo(imageFile)
	window.ui.vtkWidget.GetRenderWindow().SetSize(1024, 768)
	#window.ui.log.insertPlainText('Set render window resolution to {}\n'.format(args.resolution))
	window.show()
	window.setWindowState(Qt.WindowMaximized)  # Maximize the window
	window.iren.Initialize() # Need this line to actually show
	# the render inside Qt

	window.ui.slider_theta.valueChanged.connect(window.theta_callback)
	window.ui.push_screenshot.clicked.connect(window.screenshot_callback)
	window.ui.push_camera.clicked.connect(window.camera_callback)
	window.ui.push_quit.clicked.connect(window.quit_callback)
	sys.exit(app.exec_())