#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
gsup_gauge.py - GeigerLog gauge code

include in programs with:
    include gsup_gauge
"""

###############################################################################
#    This file is part of GeigerLog.
#
#    GeigerLog is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    GeigerLog is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with GeigerLog.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

__author__          = "ullix"
__copyright__       = "Copyright 2016, 2017, 2018, 2019, 2020, 2021, 2022"
__credits__         = ["""The original code is from here:
                        https://github.com/StefanHol/AnalogGaugeWidgetPyQt
                        and modified
                        """]
__license__         = "GPL3"

from   gsup_utils       import *


class AnalogGaugeWidget(QWidget):
    """A log value gauge"""

    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(AnalogGaugeWidget, self).__init__(parent)

        self.use_timer_event = False
        self.black = QColor(0, 0, 0, 255)

        self.logflag = True

        # self.valueColor = QColor(50, 50, 50, 255)
        # self.set_valueColor(50, 50, 50, 255)
        # self.NeedleColor = QColor(50, 50, 50, 255)
        self.set_NeedleColor(50, 50, 50, 255)
        self.NeedleColorReleased = self.NeedleColor
        # self.NeedleColorDrag = QColor(255, 0, 00, 255)
        self.set_NeedleColorDrag(255, 0, 00, 255)

        self.set_ScaleValueColor(50, 50, 50, 255)
        self.set_DisplayValueColor(50, 50, 50, 255)

        # self.CenterPointColor = QColor(50, 50, 50, 255)
        self.set_CenterPointColor(50, 50, 50, 255)

        # self.valueColor = black
        # self.black = QColor(0, 0, 0, 255)

        self.value_needle_count = 1 # what for? not used in code
        self.value_needle = QObject
        self.change_value_needle_style([QPolygon([
            QPoint(4, 4),
            QPoint(-4, 4),
            QPoint(-3, -120),
            QPoint(0, -126),
            QPoint(3, -120)
        ])])

        if not self.logflag:
            self.value_min = 0
            self.value_max = 1000
            self.value = self.value_min
            self.value_offset = 0
            self.value_needle_snapzone = 0.05
            self.last_value = 0
        else: #logflag==True
            self.value_min = np.log10(0.5)
            self.value_max = np.log10(50000)
            self.value = 0.5
            self.value_offset = 0
            self.value_needle_snapzone = 0.05
            self.last_value = 0.5

        # print("gauge init: value: ", self.value)

        # self.value2 = 0
        # self.value2Color = QColor(0, 0, 0, 255)

        self.gauge_color_outer_radius_factor = 1
        self.gauge_color_inner_radius_factor = 0.95
        self.center_horizontal_value = 0    # isn't used for anything
        self.center_vertical_value = 0      # isn't used for anything
        self.debug1 = None
        self.debug2 = None
        self.scale_angle_start_value = 135
        self.scale_angle_size = 270
        self.angle_offset = 0

        self.set_scala_main_count(5)
        self.scala_subdiv_count = 5

        self.pen = QPen(QColor(0, 0, 0))
        self.font = QFont('Decorative', 20)

        # self.scale_polygon_colors = []
        # self.set_scale_polygon_colors([[.00, Qt.red],
        #                              [.1, Qt.yellow],
        #                              [.15, Qt.green],
        #                              [1, Qt.transparent]])

        self.scale_polygon_colors = []
        self.set_scale_polygon_colors([
                                      [.00, Qt.red],
                                      [.2, Qt.yellow],
                                      [.6, Qt.green],
                                      [1, Qt.transparent]
                                      ])

        # self.set_scale_polygon_colors(None)

        # initialize Scale value text
        # self.enable_scale_text = True
        self.set_enable_ScaleText(True)
        self.scale_fontname = "Decorative"
        self.initial_scale_fontsize = 15
        self.scale_fontsize = self.initial_scale_fontsize

        # initialize Main value text
        self.enable_value_text = True
        self.value_fontname = "Decorative"
        self.initial_value_fontsize = 40
        self.value_fontsize = self.initial_value_fontsize
        self.text_radius_factor = 0.85

        # En/disable scale / fill
        # self.enable_barGraph = True
        self.set_enable_barGraph(True)

        # self.enable_filled_Polygon = True
        self.set_enable_filled_Polygon(True)


        self.enable_CenterPoint = True
        self.enable_fine_scaled_marker = True
        self.enable_big_scaled_marker = True

        self.needle_scale_factor = 0.8
        self.enable_Needle_Polygon = True

        # necessary for resize
        self.setMouseTracking(False)

        # QTimer sorgt für neu Darstellung alle X ms
        # evtl performance hier verbessern mit self.update() und self.use_timer_event = False
        # todo: self.update als default ohne ueberpruefung, ob self.use_timer_event gesetzt ist oder nicht
        # Timer startet alle 10ms das event paintEvent
        if self.use_timer_event:
            timer = QTimer(self)
            timer.timeout.connect(self.update)
            timer.start(10)
        else:
            # self.update()
            # mod
            self.update_value(self.value)

        self.setWindowTitle("Analog Gauge")

        # self.connect(self, SIGNAL("resize()"), self.rescaleMethod)

        self.resize(300 , 300)
        self.rescale_method()

        self.setMinimumWidth(self.width() + 50)
        self.setMinimumHeight(self.height())

        # print("gauge init: value: ", self.value)


    def rescale_method(self):
        # print("slotMethod")
        if self.width() <= self.height():
            self.widget_diameter = self.width()
        else:
            self.widget_diameter = self.height()

        self.change_value_needle_style([QPolygon([
            QPoint(4, 30),
            QPoint(-4, 30),
            QPoint(-2, int(- self.widget_diameter / 2 * self.needle_scale_factor)),
            QPoint(0, int(- self.widget_diameter / 2 * self.needle_scale_factor - 6)),
            QPoint(2, int(- self.widget_diameter / 2 * self.needle_scale_factor))
            ])])

        # needle = [QPolygon([
        #     QPoint(4, 4),
        #     QPoint(-4, 4),
        #     QPoint(-3, -120),
        #     QPoint(0, -126),
        #     QPoint(3, -120)])]
        # print(str(type(needle)).split("'")[1])
        #
        # needle = [2]
        # print(str(type(needle[0])).split("'")[1])

        self.scale_fontsize = self.initial_scale_fontsize * self.widget_diameter / 400
        self.value_fontsize = self.initial_value_fontsize * self.widget_diameter / 400

        # print("slotMethod end")
        pass

    def change_value_needle_style(self, design):
        # prepared for multiple needle instrument
        self.value_needle = []
        for i in design:
            self.value_needle.append(i)
        if not self.use_timer_event:
            self.update()

    def update_value(self, value, mouse_controlled = False):
        # if not mouse_controlled:
        #     self.value = value
        #
        # if mouse_controlled:
        #     self.valueChanged.emit(int(value))

        if not self.logflag:
            if value <= self.value_min:
                self.value = self.value_min
            elif value >= self.value_max:
                self.value = self.value_max
            else:
                self.value = value
        else:
            newlogval = np.log10(value)
            if newlogval <= self.value_min:
                self.value = self.value_min
            elif newlogval >= self.value_max:
                self.value = self.value_max
            else:
                self.value =newlogval
        # print("value, self.value: ", value, self.value)

        # self.paintEvent("")
        self.valueChanged.emit(int(value))
        # print(self.value)

        # ohne timer: aktiviere self.update()
        if not self.use_timer_event:
            self.update()

    def update_angle_offset(self, offset):
        self.angle_offset = offset
        if not self.use_timer_event:
            self.update()

    def center_horizontal(self, value):
        self.center_horizontal_value = value
        # print("horizontal: " + str(self.center_horizontal_value))

    def center_vertical(self, value):
        self.center_vertical_value = value
        # print("vertical: " + str(self.center_vertical_value))

    ###############################################################################################
    # Set Methods
    ###############################################################################################
    def set_NeedleColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.NeedleColor = QColor(R, G, B, Transparency)
        self.NeedleColorReleased = self.NeedleColor

        if not self.use_timer_event:
            self.update()

    def set_NeedleColorDrag(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.NeedleColorDrag = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    def set_ScaleValueColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.ScaleValueColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    def set_DisplayValueColor(self, R=50, G=50, B=50, Transparency=255):
        # Red: R = 0 - 255
        # Green: G = 0 - 255
        # Blue: B = 0 - 255
        # Transparency = 0 - 255
        self.DisplayValueColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    def set_CenterPointColor(self, R=50, G=50, B=50, Transparency=255):
        self.CenterPointColor = QColor(R, G, B, Transparency)

        if not self.use_timer_event:
            self.update()

    def set_enable_Needle_Polygon(self, enable = True):
        self.enable_Needle_Polygon = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_ScaleText(self, enable = True):
        self.enable_scale_text = enable

        if not self.use_timer_event:
            self.update()


    def set_enable_barGraph(self, enable = True):
        self.enable_barGraph = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_value_text(self, enable = True):
        self.enable_value_text = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_CenterPoint(self, enable = True):
        self.enable_CenterPoint = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_filled_Polygon(self, enable = True):
        self.enable_filled_Polygon = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_big_scaled_grid(self, enable = True):
        self.enable_big_scaled_marker = enable

        if not self.use_timer_event:
            self.update()

    def set_enable_fine_scaled_marker(self, enable = True):
        self.enable_fine_scaled_marker = enable

        if not self.use_timer_event:
            self.update()

    def set_scala_main_count(self, count):
        if count < 1:
            count = 1
        self.scala_main_count = count

        if not self.use_timer_event:
            self.update()

    def set_MinValue(self, min):
        if self.value < min:
            self.value = min
        if min >= self.value_max:
            self.value_min = self.value_max - 1
        else:
            self.value_min = min

        if not self.use_timer_event:
            self.update()

    def set_MaxValue(self, max):
        if self.value > max:
            self.value = max
        if max <= self.value_min:
            self.value_max = self.value_min + 1
        else:
            self.value_max = max

        if not self.use_timer_event:
            self.update()

    def set_start_scale_angle(self, value):
        # Value range in DEG: 0 - 360
        self.scale_angle_start_value = value
        # print("startFill: " + str(self.scale_angle_start_value))

        if not self.use_timer_event:
            self.update()

    def set_total_scale_angle_size(self, value):
        self.scale_angle_size = value
        # print("stopFill: " + str(self.scale_angle_size))

        if not self.use_timer_event:
            self.update()

    def set_gauge_color_outer_radius_factor(self, value):
        self.gauge_color_outer_radius_factor = float(value) / 1000
        # print(self.gauge_color_outer_radius_factor)

        if not self.use_timer_event:
            self.update()

    def set_gauge_color_inner_radius_factor(self, value):
        self.gauge_color_inner_radius_factor = float(value) / 1000
        # print(self.gauge_color_inner_radius_factor)

        if not self.use_timer_event:
            self.update()

    def set_scale_polygon_colors(self, color_array):
        # print(type(color_array))
        if 'list' in str(type(color_array)):
            self.scale_polygon_colors = color_array
        elif color_array == None:
            self.scale_polygon_colors = [[.0, Qt.transparent]]
        else:
            self.scale_polygon_colors = [[.0, Qt.transparent]]

        if not self.use_timer_event:
            self.update()

    ###############################################################################################
    # Get Methods
    ###############################################################################################

    def get_value_max(self):
        return self.value_max

    ###############################################################################################
    # Painter
    ###############################################################################################

    def create_polygon_pie(self, outer_radius, inner_raduis, start, length):
        polygon_pie = QPolygonF()
        # start = self.scale_angle_start_value
        # start = 0
        # length = self.scale_angle_size
        # length = 180
        # inner_raduis = self.width()/4
        # print(start)
        n = 360     # angle steps size for full circle
        # changing n value will causes drawing issues
        w = 360 / n   # angle per step
        # create outer circle line from "start"-angle to "start + length"-angle
        x = 0
        y = 0

        # todo enable/disable bar graf here
        if not self.enable_barGraph:
            # float_value = ((length / (self.value_max - self.value_min)) * (self.value - self.value_min))
            length = int(round((length / (self.value_max - self.value_min)) * (self.value - self.value_min)))
            print("f: %s, l: %s" %(float_value, length))
            pass

        # mymax = 0

        for i in range(length+1):                                              # add the points of polygon
            t = w * i + start - self.angle_offset
            x = outer_radius * np.math.cos(np.math.radians(t))
            y = outer_radius * np.math.sin(np.math.radians(t))
            polygon_pie.append(QPointF(x, y))
        # create inner circle line from "start + length"-angle to "start"-angle
        for i in range(length+1):                                              # add the points of polygon
            # print("2 " + str(i))
            t = w * (length - i) + start - self.angle_offset
            x = inner_raduis * np.math.cos(np.math.radians(t))
            y = inner_raduis * np.math.sin(np.math.radians(t))
            polygon_pie.append(QPointF(x, y))

        # close outer line
        polygon_pie.append(QPointF(x, y))
        return polygon_pie

    def draw_filled_polygon(self, outline_pen_with=0):
        if not self.scale_polygon_colors == None:
            painter_filled_polygon = QPainter(self)
            painter_filled_polygon.setRenderHint(QPainter.Antialiasing)
            # Koordinatenursprung in die Mitte der Flaeche legen
            # painter_filled_polygon.translate(self.width() / 2, self.height() / 2)
            painter_filled_polygon.translate(self.width() / 2, self.height() * 0.7)

            painter_filled_polygon.setPen(Qt.NoPen)

            self.pen.setWidth(outline_pen_with)
            if outline_pen_with > 0:
                painter_filled_polygon.setPen(self.pen)

            colored_scale_polygon = self.create_polygon_pie(
                ((self.widget_diameter / 2) - (self.pen.width() / 2)) * self.gauge_color_outer_radius_factor,
                (((self.widget_diameter / 2) - (self.pen.width() / 2)) * self.gauge_color_inner_radius_factor),
                self.scale_angle_start_value, self.scale_angle_size)

            # gauge_rect = QRect(QPoint(0, 0), QSize(self.widget_diameter / 2 - 1, self.widget_diameter - 1 )) # not used anywhere
            grad = QConicalGradient(QPointF(0, 0), - self.scale_angle_size - self.scale_angle_start_value +
                                    self.angle_offset - 1)

            # todo definition scale color as array here
            for eachcolor in self.scale_polygon_colors:
                grad.setColorAt(eachcolor[0], eachcolor[1])
            # grad.setColorAt(.00, Qt.red)
            # grad.setColorAt(.1, Qt.yellow)
            # grad.setColorAt(.15, Qt.green)
            # grad.setColorAt(1, Qt.transparent)
            painter_filled_polygon.setBrush(grad)
            # self.brush = QBrush(QColor(255, 0, 255, 255))
            # painter_filled_polygon.setBrush(self.brush)
            painter_filled_polygon.drawPolygon(colored_scale_polygon)
            # return painter_filled_polygon

    ###############################################################################################
    # Scale Marker Ticks
    ###############################################################################################

    def draw_big_scaled_marker(self):
        """draw the fat ticks"""

        my_painter = QPainter(self)
        my_painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        # my_painter.translate(self.width() / 2, self.height() / 2)
        my_painter.translate(self.width() / 2, self.height() * 0.7) # mod

        self.pen = QPen(QColor(0, 0, 0, 255))
        self.pen.setWidth(2)
        my_painter.setPen(self.pen)

        my_painter.rotate(self.scale_angle_start_value - self.angle_offset)
        steps_size = (float(self.scale_angle_size) / float(self.scala_main_count))
        scale_line_outer_start = self.widget_diameter/2
        scale_line_length = (self.widget_diameter / 2) - (self.widget_diameter / 10)
        # print(stepszize)
        deltaA = (np.log10(1) - self.value_min) / (self.value_max - self.value_min) * 180
        my_painter.rotate(deltaA)

        # for i in range(self.scala_main_count+1):
        for i in range(self.scala_main_count):
            my_painter.drawLine(int(scale_line_length), 0, int(scale_line_outer_start), 0)
            my_painter.rotate(steps_size)


    def create_fine_scaled_marker(self):
        """draw the thin ticks"""

        #  Description_dict = 0
        my_painter = QPainter(self)

        my_painter.setRenderHint(QPainter.Antialiasing)
        # Koordinatenursprung in die Mitte der Flaeche legen
        # my_painter.translate(self.width() / 2, self.height() / 2)
        my_painter.translate(self.width() / 2, self.height() * 0.7) # mod

        my_painter.setPen(Qt.black)
        my_painter.rotate(self.scale_angle_start_value - self.angle_offset)
        steps_size = (float(self.scale_angle_size) / float(self.scala_main_count * self.scala_subdiv_count))
        scale_line_outer_start = self.widget_diameter/2
        scale_line_length = (self.widget_diameter / 2) - (self.widget_diameter / 40)
        for i in range((self.scala_main_count * self.scala_subdiv_count)+1):
            my_painter.drawLine(scale_line_length, 0, scale_line_outer_start, 0)
            my_painter.rotate(steps_size)


    ###############################################################################################
    # Scale Marker Ticks Labels
    ###############################################################################################


    def create_scale_marker_labels(self):
        """draws the label to the scale marker"""

        pen_shadow = QPen()
        pen_shadow.setBrush(self.ScaleValueColor)
        pen_shadow.setWidth(6)

        font = QFont(self.scale_fontname, int(self.scale_fontsize))
        fm = QFontMetrics(font)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(font)
        painter.setPen(pen_shadow)
        painter.translate(self.width() / 2 , self.height() * 0.7 ) # mod

        # Koordinatenursprung in die Mitte der Flaeche legen
        # painter.translate(self.width() / 2, self.height() / 2)
        # painter.translate(self.width() / 2, self.height() * 0.7) # mod

        # self.text_radius_factor = 0.8                # position of scale label
        text_radius = self.widget_diameter/2 * self.text_radius_factor * 0.96

        scale_per_div = int((self.value_max - self.value_min) / self.scala_main_count)

        angle_stepsize = (float(self.scale_angle_size) / float(self.scala_main_count))
        deltaA = (np.log10(1) - self.value_min) / (self.value_max - self.value_min) * 180
        # print("deltaA", deltaA)
        # for i in range(self.scala_main_count + 1):
        for i in range(self.scala_main_count ): # mod
            text = "{:0.0f}".format(np.power(10, np.ceil(self.value_min) + scale_per_div * i))

            # w = fm.width(text) + 1
            w = fm.width(text)
            h = fm.height()

            angle = angle_stepsize * i + float(self.scale_angle_start_value - self.angle_offset)
            angle += deltaA
            x = text_radius * np.math.cos(np.math.radians(angle))
            y = text_radius * np.math.sin(np.math.radians(angle))
            # print("create_scale_marker_labels: angle={:6.1f} x={:6.1f} y={:6.1f} w={:6.1f} h={:6.1f} text={}".format(angle, x, y, w,h, text))

            painter.save()
            painter.translate(x, y)
            painter.rotate(angle + 90)
            painter.drawText(0- int(w/2), 0 - int(h/2), w, h, Qt.AlignCenter, text)
            painter.restore()


    def create_values_text(self):
        """draws the current value"""

        painter = QPainter(self)
        # painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        # painter.translate(self.width() / 2, self.height() / 2)
        painter.translate(self.width() / 2, self.height() * 0.7) # mod

        # painter.save()
        # xShadow = 3.0
        # yShadow = 3.0
        font = QFont(self.value_fontname, int(self.value_fontsize))
        fm = QFontMetrics(font)

        pen_shadow = QPen()
        pen_shadow.setBrush(self.DisplayValueColor)

        painter.setPen(pen_shadow)

        # text_radius = self.widget_diameter / 2 * self.text_radius_factor
        text_radius = 50 # mod

        text = str(int(self.value))
        # print("create_values_text: value text: ", text)
        w = fm.width(text) + 1
        h = fm.height()
        painter.setFont(QFont(self.value_fontname, int(self.value_fontsize)))

        # Mitte zwischen Skalenstart und Skalenende:
        # Skalenende = Skalenanfang - 360 + Skalenlaenge
        # Skalenmitte = (Skalenende - Skalenanfang) / 2 + Skalenanfang
        angle_end = float(self.scale_angle_start_value + self.scale_angle_size - 360)

        angle = (angle_end - self.scale_angle_start_value) / 2 + self.scale_angle_start_value

        x = text_radius * np.math.cos(np.math.radians(angle))
        y = text_radius * np.math.sin(np.math.radians(angle))
        # print(w, h, x, y, text)
        text = [int(x - int(w/2)), int(y - int(h/2)), int(w), int(h), Qt.AlignCenter, text]
        painter.drawText(text[0], text[1], text[2], text[3], text[4], text[5])
        # painter.restore()

    def draw_big_needle_center_point(self, diameter=30):
        painter = QPainter(self)
        # painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        # painter.translate(self.width() / 2, self.height() / 2)
        painter.translate(self.width() / 2, self.height() * 0.7) # mod
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.CenterPointColor)
        # diameter = diameter # self.widget_diameter/6
        painter.drawEllipse(int(-diameter / 2), int(-diameter / 2), int(diameter), int(diameter))

    def draw_needle(self):
        painter = QPainter(self)
        # painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.Antialiasing)

        # Koordinatenursprung in die Mitte der Flaeche legen
        # painter.translate(self.width() / 2, self.height() / 2)
        painter.translate(self.width() / 2, self.height() * 0.7) # mod

        painter.setPen(Qt.NoPen)
        painter.setBrush(self.NeedleColor)
        if not self.logflag:
            painter.rotate(((self.value - self.value_offset - self.value_min) * self.scale_angle_size /
                            (self.value_max - self.value_min)) + 90 + self.scale_angle_start_value)
        else:
            angle = ((np.log10(self.value) - self.value_offset - self.value_min) * self.scale_angle_size / (self.value_max - self.value_min) )   + 90 + self.scale_angle_start_value
            # print("angle", angle)
            # painter.rotate(((np.power(10 , ((self.value - self.value_offset - self.value_min) * self.scale_angle_size /
            #                     (self.value_max - self.value_min)) + 90 + self.scale_angle_start_value))))
            painter.rotate(angle)

        painter.drawConvexPolygon(self.value_needle[0])

    ###############################################################################################
    # Events
    ###############################################################################################

    def resizeEvent(self, event):
        # self.resized.emit()
        # return super(self.parent, self).resizeEvent(event)
        # print("resized")
        # print(self.width())
        self.rescale_method()
        # self.emit(QtCore.SIGNAL("resize()"))
        # print("resizeEvent")

    def paintEvent(self, event):
        # Main Drawing Event:
        # Will be executed on every change
        # vgl http://doc.qt.io/qt-4.8/qt-demos-affine-xform-cpp.html
        # print("event", event)

        # colored pie area
        if self.enable_filled_Polygon:
            self.draw_filled_polygon()

        # draw scale marker lines
        if self.enable_fine_scaled_marker:
            self.create_fine_scaled_marker()
        if self.enable_big_scaled_marker:
            self.draw_big_scaled_marker()

        # draw scale marker value text
        if self.enable_scale_text:
            self.create_scale_marker_labels()

        # Display Value
        if self.enable_value_text:
            self.create_values_text()

        # draw needle 1
        if self.enable_Needle_Polygon:
            self.draw_needle()

        # Draw Center Point
        if self.enable_CenterPoint:
            # self.draw_big_needle_center_point(diameter=(self.widget_diameter / 6))
            self.draw_big_needle_center_point(diameter=(self.widget_diameter / 8)) # mod

    ###############################################################################################
    # MouseEvents
    ###############################################################################################

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def mouseReleaseEvent(self, QMouseEvent):
        # print("released")
        self.NeedleColor = self.NeedleColorReleased

        if not self.use_timer_event:
            self.update()
        pass

    def mouseMoveEvent(self, event):
        x, y = event.x() - (self.width() / 2), event.y() - (self.height() / 2)
        if not x == 0:
            angle = np.math.atan2(y, x) / np.math.pi * 180
            # winkellaenge der anzeige immer positiv 0 - 360deg
            # min wert + umskalierter wert
            value = (float(np.math.fmod(angle - self.scale_angle_start_value + 720, 360)) / \
                     (float(self.scale_angle_size) / float(self.value_max - self.value_min))) + self.value_min
            temp = value
            fmod = float(np.math.fmod(angle - self.scale_angle_start_value + 720, 360))
            state = 0
            if (self.value - (self.value_max - self.value_min) * self.value_needle_snapzone) <= \
                    value <= \
                    (self.value + (self.value_max - self.value_min) * self.value_needle_snapzone):
                self.NeedleColor = self.NeedleColorDrag
                # todo: evtl ueberpruefen
                #
                state = 9
                # if value >= self.value_max and self.last_value < (self.value_max - self.value_min) / 2:
                if value >= self.value_max and self.last_value < (self.value_max - self.value_min) / 2:
                    state = 1
                    value = self.value_max
                    self.last_value = self.value_min
                    self.valueChanged.emit(int(value))
                elif value >= self.value_max >= self.last_value:
                    state = 2
                    value = self.value_max
                    self.last_value = self.value_max
                    self.valueChanged.emit(int(value))
                else:
                    state = 3
                    self.last_value = value
                    self.valueChanged.emit(int(value))

                # todo: mouse event debug output

                # self.update_value(value, mouse_controlled=True)

                # self.valueChanged.emit(int(value))
                # print(str(int(value)))
            # self.valueChanged.emit()

            # todo: convert print to logging debug
            # print('mouseMoveEvent: x=%d, y=%d, a=%s, v=%s, fmod=%s, temp=%s, state=%s' % (
            #     x, y, angle, value, fmod, temp, state))




    # def createPoly(self, n, r, s):
    #     polygon = QPolygonF()
    #
    #     w = 360/n                                                       # angle per step
    #     for i in range(n):                                              # add the points of polygon
    #         t = w*i + s
    #         x = r*np.math.cos(np.math.radians(t))
    #         y = r*np.math.sin(np.math.radians(t))
    #         # polygon.append(QtCore.QPointF(self.width()/2 +x, self.height()/2 + y))
    #         polygon.append(QtCore.QPointF(x, y))
    #
    #     return polygon


