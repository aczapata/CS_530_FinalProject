#!/usr/bin/env python

# This example shows how to combine data from both the imaging and
# graphics pipelines. The vtkMergeFilter is used to merge the data
# from each together.

import vtk
from vtk.util.misc import vtkGetDataRoot
VTK_DATA_ROOT = vtkGetDataRoot()

import sys
import os

# Purdue CS530 - Introduction to Scientific Visualization
# Spring 2021

# Simple example showing how to use PyQt5 to manipulate
# a visualization

from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSlider, QGridLayout, QLabel, QPushButton, QTextEdit, QComboBox, QDateTimeEdit
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import argparse
import sys
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk.util.numpy_support
import colorbar
from pytwobodyorbit import TwoBodyOrbit
import math

frame_counter = 0
sunmu = 1.32712440041e20

#taken from https://gist.github.com/jiffyclub/1294443
def date_to_mjd(year,month,day):
    """
    Convert a date to Julian Day.
    
    Algorithm from 'Practical Astronomy with your Calculator or Spreadsheet', 
        4th ed., Duffet-Smith and Zwart, 2011.
    
    Parameters
    ----------
    year : int
        Year as integer. Years preceding 1 A.D. should be 0 or negative.
        The year before 1 A.D. is 0, 10 B.C. is year -9.
        
    month : int
        Month as integer, Jan = 1, Feb. = 2, etc.
    
    day : float
        Day, may contain fractional part.
    
    Returns
    -------
    jd : float
        Julian Day
        
    Examples
    --------
    Convert 6 a.m., February 17, 1985 to Julian Day
    
    >>> date_to_jd(1985,2,17.25)
    2446113.75
    
    """
    if month == 1 or month == 2:
        yearp = year - 1
        monthp = month + 12
    else:
        yearp = year
        monthp = month
    
    # this checks where we are in relation to October 15, 1582, the beginning
    # of the Gregorian calendar.
    if ((year < 1582) or
        (year == 1582 and month < 10) or
        (year == 1582 and month == 10 and day < 15)):
        # before start of Gregorian calendar
        B = 0
    else:
        # after start of Gregorian calendar
        A = math.trunc(yearp / 100.)
        B = 2 - A + math.trunc(A / 4.)
        
    if yearp < 0:
        C = math.trunc((365.25 * yearp) - 0.75)
    else:
        C = math.trunc(365.25 * yearp)
    D = math.trunc(30.6001 * (monthp + 1))
    jd = B + C + D + day + 1720994.5
    return jd - 2400000.5

class Planet():
	def __init__(self, physical_array, kepler_array):
		self.name = physical_array[0]
		self.equatorial_radius = float(physical_array[1]) *1000 #change km to meters
		self.mean_radius = float(physical_array[2]) *1000 #change km to meters
		self.texture_file = physical_array[11]
		self.a = float(kepler_array[1])*1.496e11 #change au to meters
		self.e = float(kepler_array[2])
		self.i = float(kepler_array[3])
		self.l = float(kepler_array[4])
		self.long_peri = float(kepler_array[5])
		self.long_node = float(kepler_array[6])

class Asteroid():
	def __init__(self, physical_array, kepler_array):
		self.name = physical_array[0]
		self.diameter = float(physical_array[3])*1000 #change km to meters
		self.texture_file = physical_array[7]
		self.epoch = int(kepler_array[2])
		self.a = float(kepler_array[3])*1.496e11 #change au to meters
		self.e = float(kepler_array[4])
		self.i = float(kepler_array[5])
		self.w = float(kepler_array[6])
		self.node = float(kepler_array[7])
		self.m = float(kepler_array[8])
		

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
		self.name = ""

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
		#print('Executing')
		output = vtk.vtkPolyData.GetData(outInfo)
		self.Update()
		output.ShallowCopy(self.sphere)

		#print('output\n{}'.format(output))

		return 1


def save_frame(window, log):
	global frame_counter
	global args
	# ---------------------------------------------------------------
	# Save current contents of render window to PNG file
	# ---------------------------------------------------------------

	if not os.path.exists('screenshots'):
		os.makedirs('screenshots')

	file_name = "screenshots/picture_" + str(frame_counter).zfill(5) + ".png"
	image = vtk.vtkWindowToImageFilter()
	image.SetInput(window)
	png_writer = vtk.vtkPNGWriter()
	png_writer.SetInputConnection(image.GetOutputPort())
	png_writer.SetFileName(file_name)
	window.Render()
	png_writer.Write()
	frame_counter += 1
	log.insertPlainText('Exported {}\n'.format(file_name))


def make_sphere(textureFile, center, radius):
	
	# create and visualize sphere
	sphere_source = MySphere()
	sphere_source.SetRadius(radius)
	sphere_source.SetCenter(center)
	sphere_source.SetThetaResolution(100)
	sphere_source.SetPhiResolution(100)

	reader = vtk.vtkJPEGReader()
	reader.SetFileName(textureFile)

	texture = vtk.vtkTexture()
	texture.SetInputConnection(reader.GetOutputPort())
	texture.InterpolateOn()

	text_to_sphere = vtk.vtkTextureMapToSphere()
	text_to_sphere.SetInputConnection(sphere_source.GetOutputPort())
	text_to_sphere.PreventSeamOff()
	
	mapper = vtk.vtkPolyDataMapper()
	mapper.SetInputConnection(text_to_sphere.GetOutputPort())
	mapper.ScalarVisibilityOff()

	triang = vtk.vtkActor()
	triang.SetMapper(mapper)
	triang.SetTexture(texture)

	return triang, sphere_source


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
		self.slider_scale = QSlider()
		self.slider_orbit = QSlider()
		
		#Date Picker
		self.date_textbox = QDateTimeEdit()
		self.date_textbox.setCalendarPopup(True)
		self.date_textbox.setMinimumDate(QDate(2020, 12, 17))
		self.date_textbox.setMaximumDate(QDate(2050, 12, 31))
		self.date_textbox.setDate(QDate.currentDate())
		
		#Combo box
		self.obj_focus = QComboBox()
		# Push buttons
		self.push_screenshot = QPushButton()
		self.push_screenshot.setText('Save screenshot')
		self.push_quit = QPushButton()
		self.push_quit.setText('Quit')
		# Text windows
		self.log = QTextEdit()
		self.log.setReadOnly(True)
		# We are now going to position our widgets inside our
		# grid layout. The top left corner is (0,0)
		# Here we specify that our vtkWidget is anchored to the top
		# left corner and spans 3 rows and 4 columns.
		self.gridlayout.addWidget(self.vtkWidget, 0, 0, 4, 4)
		self.gridlayout.addWidget(QLabel("Scale"), 4, 0, 1, 1)
		self.gridlayout.addWidget(self.slider_scale, 4, 1, 1, 1)
		self.gridlayout.addWidget(QLabel("Try moving the planets!"), 5, 0, 1, 1)
		self.gridlayout.addWidget(self.slider_orbit, 5, 1, 1, 1)
		self.gridlayout.addWidget(QLabel("Enter Date"),4,2,1,1)
		self.gridlayout.addWidget(self.date_textbox,5,2,1,1)
		#self.gridlayout.addWidget(self.push_date,6,2,1,1)
		self.gridlayout.addWidget(QLabel("Select Object To Center Camera"),4,3,1,1)
		self.gridlayout.addWidget(self.obj_focus,5,3,1,1)
		#self.gridlayout.addWidget(QLabel("Edge radius"), 4, 2, 1, 1)
		#self.gridlayout.addWidget(self.slider_radius, 4, 3, 1, 1)
		self.gridlayout.addWidget(self.push_screenshot, 0, 5, 1, 1)
		self.gridlayout.addWidget(self.log, 1, 4, 1, 2)
		self.gridlayout.addWidget(self.push_quit, 5, 5, 1, 1)
		MainWindow.setCentralWidget(self.centralWidget)

class PyQtDemo(QMainWindow):

	def __init__(self, parent = None):
		QMainWindow.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.obj_sphere = 0
		# Create the Renderer
		self.ren = vtk.vtkRenderer()

		planets_file = open("Data/planets_physical_characteristics.csv", "r")
		planets_keplerian_file = open("Data/planets_keplerian_elements.csv", "r")

		asteroids_file = open("Data/asteroids_physical_characteristics.csv", "r")
		asteroids_keplerian_file = open("Data/asteroids_keplerian_elements.csv", "r")

		self.planet_spheres = []
		self.planet_objs = []
		self.planet_orbits = []

		self.asteroid_spheres = []
		self.asteroid_objs = []
		self.asteroid_orbits = []

		#make the sun
		self.sun_actor, self.sun_source = make_sphere("Data/2k_sun.jpg", [0,0,0], 696340000)
		self.ren.AddActor(self.sun_actor)

		color_scale = [	[255, 0, 0], #red
						[255,127, 0], #orange
						[255, 255, 0], #yellow
						[0, 255, 0], #green
						[0, 255, 255], #cyan*
						[0, 127, 255], #blue*
						[127, 0, 255], #purple*
						[255, 0, 255],	#magenta
						[255, 0, 127], #rose
						#Asteroids
						[150, 255, 90], 
						[255, 150, 90], 
						[255, 255, 255], 
						[90, 150, 255], 
						[255, 100, 255], 
						]		
		index = 0
		#Create all actors for planets

		for p, k in zip(planets_file.readlines()[1:], planets_keplerian_file.readlines()[1:]):
			
			#Read attributes from file
			planet = Planet(p.strip("\n").split(","), k.strip("\n").split(","))
			
			#Create orbit
			orbit = TwoBodyOrbit(planet.name, mu=sunmu)
			t0 = 59200 * 86400                                      
			orbit.setOrbKepl(t0, planet.a, planet.e, planet.i, planet.long_node, planet.long_peri,  0)
			pos, vel = orbit.posvelatt(t0)
			xs, ys, zs, times = orbit.points(1000)
			points = vtk.vtkPoints()
			self.planet_orbits.append(orbit)
			
			# Setup the colors array
			colors = vtk.vtkUnsignedCharArray()
			colors.SetNumberOfComponents(3)
			colors.SetName("Colors")

			colors.InsertNextTypedTuple(color_scale[index])
			index+=1
			#Draw orbit from points
			for i in range(1000):
				points.InsertPoint(i, xs[i], ys[i], zs[i])
			
			lines = vtk.vtkCellArray()
			lines.InsertNextCell(1000)

			for i in range(1000):
				lines.InsertCellPoint(i)

			polyData = vtk.vtkPolyData()
			polyData.SetPoints(points)
			polyData.SetLines(lines)
			polyData.GetCellData().SetScalars(colors)

			# Create a mapper
			planet_orbit_mapper = vtk.vtkPolyDataMapper()
			planet_orbit_mapper.SetInputData(polyData)
			planet_orbit_mapper.ScalarVisibilityOn()
			
			# Create an actor
			planet_orbit_actor = vtk.vtkActor()
			planet_orbit_actor.SetMapper(planet_orbit_mapper)
			self.ren.AddActor(planet_orbit_actor)

			sphere_actor, sphere_source = make_sphere(planet.texture_file, pos, planet.equatorial_radius)
			self.planet_spheres.append(sphere_source)
			self.planet_objs.append(planet)
			print(pos)
			self.ren.AddActor(sphere_actor)

		#Create all actors for Asteroids
		for a, k in zip(asteroids_file.readlines()[1:], asteroids_keplerian_file.readlines()[1:]):
			
			#Read attributes from file
			asteroid = Asteroid(a.strip("\n").split(","), k.strip("\n").split(","))
			
			#Create orbit
			orbit = TwoBodyOrbit(asteroid.name, mu=sunmu)
			t0 = asteroid.epoch * 86400                                   
			orbit.setOrbKepl(t0, asteroid.a, asteroid.e, asteroid.i, asteroid.node, asteroid.w,  asteroid.m)
			pos, vel = orbit.posvelatt(t0)
			xs, ys, zs, times = orbit.points(100)
			points = vtk.vtkPoints()
			self.asteroid_orbits.append(orbit)
			
			# Setup the colors array
			colors = vtk.vtkUnsignedCharArray()
			colors.SetNumberOfComponents(3)
			colors.SetName("Colors")

			colors.InsertNextTypedTuple(color_scale[index])
			index+=1

			#Draw orbit from points
			for i in range(100):
				points.InsertPoint(i, xs[i], ys[i], zs[i])
			
			lines = vtk.vtkCellArray()
			lines.InsertNextCell(100)

			for i in range(100):
				lines.InsertCellPoint(i)

			polyData = vtk.vtkPolyData()
			polyData.SetPoints(points)
			polyData.SetLines(lines)
			polyData.GetCellData().SetScalars(colors)

			# Create a mapper
			asteroid_orbit_mapper = vtk.vtkPolyDataMapper()
			asteroid_orbit_mapper.SetInputData(polyData)
			asteroid_orbit_mapper.ScalarVisibilityOn()
			
			# Create an actor
			asteroid_orbit_actor = vtk.vtkActor()
			asteroid_orbit_actor.SetMapper(asteroid_orbit_mapper)
			self.ren.AddActor(asteroid_orbit_actor)

			sphere_actor, sphere_source = make_sphere(asteroid.texture_file, pos, asteroid.diameter/2)
			self.asteroid_spheres.append(sphere_source)
			self.asteroid_objs.append(asteroid)
			#print(pos)
			self.ren.AddActor(sphere_actor)

		objects = ["Sun","Mercury","Venus","Earth","Mars","Ceres","Vesta","Pallas","Hygiea","Interamnia","Jupiter","Saturn","Uranus","Neptune","Pluto"]
		self.ui.obj_focus.addItems(objects)

		self.ren.GradientBackgroundOn()  # Set gradient for background
		self.ren.SetBackground(0.25, 0.25, 0.25)  # Set background to silver

		
		cam1 = self.ren.GetActiveCamera()
		cam1.SetPosition(-1195762253824.0, 649975300096.0, -26201048247886.45)
		cam1.SetFocalPoint(0,0, 0)
		cam1.SetViewUp(0,1,0)
		
		self.ren.ResetCameraClippingRange()
		
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

		slider_setup(self.ui.slider_scale, 0, [0, 50000], 1000)
		slider_setup(self.ui.slider_orbit, 0, [59200, 70000], 1000)


	def scale_callback(self, val):
		for i in range(len(self.planet_objs)):
			#print(val)
			if i >= 4 and val > 2500 and i != 8:
				self.planet_spheres[i].SetRadius(self.planet_objs[i].equatorial_radius * 2500)
				continue
			elif i < 4 and val > 3800:
				self.planet_spheres[i].SetRadius(self.planet_objs[i].equatorial_radius * 3500)
				continue
			self.planet_spheres[i].SetRadius(self.planet_objs[i].equatorial_radius * val)
		
		for i in range(len(self.asteroid_objs)):
			#print(val)
			self.asteroid_spheres[i].SetRadius(self.asteroid_objs[i].diameter* val/2 )
		
		if val < 25:
			self.sun_source.SetRadius(696340000 * val)
		else:
			self.sun_source.SetRadius(696340000 * 25)

		#self.ui.log.insertPlainText('Scale set to {}\n'.format(val))
		self.ui.vtkWidget.GetRenderWindow().Render()

	def date_callback(self,val):
		mjd = date_to_mjd(val.year(), val.month(), val.day())
		for i in range(len(self.planet_orbits)):
			#print(val)
			pos, vel = self.planet_orbits[i].posvelatt(mjd * 86400)
			self.planet_spheres[i].SetCenter(pos)
			#print (pos, vel)
		
		for i in range(len(self.asteroid_objs)):
			#print(val)
			pos, vel = self.asteroid_orbits[i].posvelatt(mjd * 86400)
			self.asteroid_spheres[i].SetCenter(pos)

		self.ui.log.insertPlainText('Date set to {}\n'.format(self.ui.date_textbox.text()))
		
		if self.obj_sphere != 0:
			cam1 = self.ren.GetActiveCamera()
			cam1.SetFocalPoint(self.obj_sphere.center)
			self.ren.ResetCameraClippingRange()

		self.ui.vtkWidget.GetRenderWindow().Render()

	def focus_callback(self, val):
		print(val)
		objects = ["Sun","Mercury","Venus","Earth","Mars","Ceres","Vesta","Pallas","Hygiea","Interamnia","Jupiter","Saturn","Uranus","Neptune","Pluto"]
		if val == 0:

			cam1 = self.ren.GetActiveCamera()
			#cam1.SetPosition(-1195762253824.0, 649975300096.0, -26201048247886.45)
			cam1.SetFocalPoint(0, 0, 0)
			cam1.SetViewUp(0,1,0)
			self.ren.ResetCameraClippingRange()
			self.ui.vtkWidget.GetRenderWindow().Render()
			return

		switcher = {
			1 : self.planet_spheres[0],
			2 : self.planet_spheres[1],
			3 : self.planet_spheres[2],
			4 : self.planet_spheres[3],
			5 : self.asteroid_spheres[0],
			6 : self.asteroid_spheres[1],
			7 : self.asteroid_spheres[2],
			8 : self.asteroid_spheres[3],
			9 : self.asteroid_spheres[4],
			10 : self.planet_spheres[4],
			11 : self.planet_spheres[5],
			12 : self.planet_spheres[6],
			13 : self.planet_spheres[7],
			14 : self.planet_spheres[8]
		}

		self.obj_sphere = switcher.get(val)
		cam1 = self.ren.GetActiveCamera()
		cam1.SetFocalPoint(self.obj_sphere.center)
		self.ren.ResetCameraClippingRange()
		self.ui.vtkWidget.GetRenderWindow().Render()

	def orbit_callback(self, val):
		for i in range(len(self.planet_orbits)):
			#print(val)
			pos, vel = self.planet_orbits[i].posvelatt(val * 86400)
			self.planet_spheres[i].SetCenter(pos)
			#print (pos, vel)
		
		for i in range(len(self.asteroid_objs)):
			#print(val)
			pos, vel = self.asteroid_orbits[i].posvelatt(val * 86400)
			self.asteroid_spheres[i].SetCenter(pos)

		
		if self.obj_sphere != 0:
			cam1 = self.ren.GetActiveCamera()
			cam1.SetFocalPoint(self.obj_sphere.center)
			self.ren.ResetCameraClippingRange()

		self.ui.vtkWidget.GetRenderWindow().Render()

		

	def scale_release(self, val):
		self.ui.log.insertPlainText('Scale set to {}\n'.format(val))
		self.ui.log.insertPlainText('Sun Scale Max: 25\nInner Solar System Scale Max: 3800\nOuter Solar System Scale Max: 2500\nAsteroids and Pluto Scale Max: 50000\n')

	def screenshot_callback(self):
		save_frame(self.ui.vtkWidget.GetRenderWindow(), self.ui.log)

	def quit_callback(self):
		sys.exit()

if __name__=="__main__":
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
	window = PyQtDemo()
	window.ui.vtkWidget.GetRenderWindow().SetSize(1024, 768)
	#window.ui.log.insertPlainText('Set render window resolution to {}\n'.format(args.resolution))
	window.show()
	window.setWindowState(Qt.WindowMaximized)  # Maximize the window
	window.iren.Initialize() # Need this line to actually show
	# the render inside Qt

	window.ui.slider_scale.sliderMoved.connect(window.scale_callback)
	window.ui.slider_scale.valueChanged.connect(window.scale_release)
	window.ui.slider_orbit.sliderMoved.connect(window.orbit_callback)
	window.ui.obj_focus.currentIndexChanged.connect(window.focus_callback)
	window.ui.push_screenshot.clicked.connect(window.screenshot_callback)
	window.ui.push_quit.clicked.connect(window.quit_callback)
	window.ui.date_textbox.dateChanged.connect(window.date_callback)
	sys.exit(app.exec_())