#!/usr/bin/python
# encoding: utf-8
#
# Tobii controller for PsychoPy
# author: Hiroyuki Sogo
#         Modified by Soyogu Matsushita
#         Further modified by Jan Freyberg
# - Tobii SDK 3.0 is required
# - no guarantee
##UPDATED 8th April, 2017
# Modifier: sunnycia of FMC-IML ShenZhen University
# Reason: Tobii Pro SDK replace Tobii Analysis SDK 3
# 

import os
import sys
import wx
import psychopy.event, psychopy.core, psychopy.monitors
import psychopy.visual, psychopy.gui
import datetime
import time 
import cPickle
import sqlite3
import numpy as np
import random
import vlc
## Tobii Pro SDK
import tobii_research


class point2D:
    def __init__(self):
        self.x = None
        self.y = None

class Color:
    # Set default colors
    gray = (0.5, 0.5, 0.5)
    black = (-1.0, -1.0, -1.0)
    white = (1.0, 1.0, 1.0)
    yellow = (1.0, 1.0, -1.0)
    green = (-1.0, 1.0, -1.0)
    blue = (-1.0, -1.0, 1.0)
    red = (1.0, -1.0, -1.0)
    cyan = (-1.0, 1.0, 1.0)

class Style:
    font = "Elephant"
    textHeight_inpix = 8 # pixel
    textHeight_incm = 1 # pixel
    
    lineWidth = 3
    
    
def clock_demo(win):
    color_pad = Color()
    ## clockface.py in psychopy demo
    # vertices (using numpy means we can scale them easily)
    handVerts = np.array([ [0, 0.8], [-0.05, 0], [0, -0.05], [0.05, 0] ])
    win.color=color_pad.gray
    
    second = psychopy.visual.ShapeStim(win, vertices=[[0, -0.1], [0.1, 0.8]],units="norm", 
        lineColor=[1, -1, -1], fillColor=None, lineWidth=2, autoLog=False)
    minute = psychopy.visual.ShapeStim(win, vertices=handVerts,units="norm", 
        lineColor=color_pad.blue, fillColor=color_pad.blue, autoLog=False)
    hour = psychopy.visual.ShapeStim(win, vertices=handVerts/2.0,units="norm", 
        lineColor=color_pad.black, fillColor=color_pad.black, autoLog=False)
    center = psychopy.visual.Circle(win,fillColor=color_pad.red, lineColor=color_pad.red, units="pix", radius=10)
    clock = psychopy.core.Clock()
    while not psychopy.event.getKeys():
        t = time.localtime()

        minPos = np.floor(t[4]) * 360 / 60  # NB floor will round down
        minute.ori = minPos
        minute.draw()

        hourPos = (t[3]) * 360 / 12  # this one can be smooth
        hour.ori = hourPos
        hour.draw()

        secPos = np.floor(t[5]) * 360 / 60  # NB floor will round down
        second.ori = secPos
        second.draw()

        center.draw()
        win.flip()
        psychopy.event.clearEvents('mouse')  # only really needed for pygame windows
    
def count_down(win, seconds, text):
    color_pad = Color()
    style = Style()
    win.color = color_pad.black
    total_length = 800 
    runner_x = -total_length/2
    if not text is None:
        # print text
        txtMessage = psychopy.visual.TextStim(win, font=style.font, color=color_pad.white, units="pix", pos=(0, 20), text=text)
        txtMessage.setAutoDraw(True)
    else:
        txtMessage = None
    wrapper = psychopy.visual.Rect(win, lineColor=color_pad.white,units='pix', 
                                    width=total_length, height=10, lineWidth=3, autoDraw=True)
    runner = psychopy.visual.Rect(win, lineColor=color_pad.blue, fillColor=color_pad.blue,
                                    units='pix', pos=(runner_x, 0), width=0, height=10, autoDraw=True)
    ratio = total_length/float(seconds)
    start_t = time.clock()
    now_t = time.clock()
    duration = now_t - start_t
    while duration < seconds:
        cur_length = duration * ratio
        runner.width = cur_length
        cur_runner_x = cur_length / 2 + runner_x
        runner.pos = (cur_runner_x, 0)
        win.flip()
        psychopy.core.wait(0.25)
        
        now_t = time.clock()
        duration = now_t - start_t
    
    if not txtMessage == None:
        txtMessage.setAutoDraw(False)
    wrapper.setAutoDraw(False)
    runner.setAutoDraw(False)

def psychopy_key_string(win):
    ## useless
    input = psychopy.event.getKeys()
    while input != "escape":
        print input
        psychopy.core.wait(1)
    
class TobiiController:
    ## Set default colors
    color_pad = Color()
    style = Style()
    correctColor = color_pad.green
    warningColor = color_pad.yellow
    wrongColor = color_pad.red
    logoPath = "bitmaps/FMCIML.png"
    ############################################################################
    # initialization&destroy and basic function
    ############################################################################
    def __init__(self, win, subj_path):
        self.eyetracker = None
        self.eyetrackers = None
        self.win = win
        self.gazeData = []
        self.eventData = []
        self.datafile = None
        self.logo = None
        self.path = subj_path
        self.log_f = open(os.path.join(subj_path, "log.txt"), "a")
        self.t0 = None
        print >> self.log_f, "Initial time", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        print >> self.log_f, "Initial timestamp", tobii_research.get_system_time_stamp()
        def fade_animation(win, stim, fade_steps=1000, fade_duration=50):
            stim.opacity=0.0
            fade_steps = fade_steps
            delta_fade = 0.5 / fade_steps

            fade_value = delta_fade
            
            while stim.opacity < 1.0:
                fade_value += delta_fade
                psychopy.core.wait(0.01)
                stim.opacity = fade_value
                stim.draw()
                win.flip()
            
            self.eyetrackers = tobii_research.find_all_eyetrackers()
            # psychopy.core.wait(1)
            
            while stim.opacity > 0.1:
                fade_value -= delta_fade
                stim.opacity = fade_value
                stim.draw()
                win.flip()
            
        try:
            self.logo = psychopy.visual.ImageStim(self.win, image=self.logoPath)
        except:
            print "logo file not found! Ignore logo."
            self.eyetrackers = tobii_research.find_all_eyetrackers()
        else:
            # self.logo.draw()
            # win.flip()
            fade_animation(self.win, self.logo, fade_steps=5, fade_duration=40)
        print >> self.log_f, "Initial complete.", tobii_research.get_system_time_stamp()
        
    def basic_info(self):
        '''
        et is an eyetracker instance
        '''
        if self.eyetracker == None:
            print "Activate eyetracker first!"
            return
        print "Address:", self.eyetracker.address
        print "Name:", self.eyetracker.device_name
        print "Serial number:", self.eyetracker.serial_number
        print "Model:", self.eyetracker.model
        print "Firmware version:", self.eyetracker.firmware_version
        # print "device device capabilities:", self.eyetracker.device_capabilities
        
    def get_system_time(self):
        if self.eyetracker == None:
            print "Activate eyetracker first!"
            return
        system_time_stamp = tobii_research.get_system_time_stamp()
        
        # microsecond
        return system_time_stamp
        
    def activate(self):
        if self.logo != None:
            self.logo.autoDraw = False
        self.logo = None
        self.win.flip()
        if len(self.eyetrackers) == 0:
            psychopy.visual.TextStim(self.win, font=self.style.font, text="Cannot find an eyetracker. Press any key to exit.", color=self.color_pad.red).draw()
            self.win.flip()
            psychopy.event.waitKeys()
            print >> self.log_f, "Cannot find an eyetracker."
            raise BaseException("Cannot find an eyetracker.")
        self.eyetracker = self.eyetrackers[0]
        self.t0 = tobii_research.get_system_time_stamp()
        print >> self.log_f, "Activate Complete! Time origin(t0) is", self.t0
        # self.basic_info()

    def destroy(self):
        self.eyetrackers = None
        self.eyetracker = None
    
    ############################################################################
    # calibration methods
    ############################################################################

    def findEyes(self):    
        ###
        ## Notification animation
        ###
        temp_txt = psychopy.visual.TextStim(self.win, font=self.style.font, text="Adjust the position of your head", color=self.color_pad.black)
        temp_txt.draw()
        self.win.flip()
        psychopy.core.wait(2)
        self.win.flip()
            
        
        
        
        
        
        
        
        # This method starts tracking, finds eyes, and then displays the
        # eyes on the screen for the researcher to see.
        print >> self.log_f, "Finding eyes...", tobii_research.get_system_time_stamp(), 
        if self.eyetracker is None:
            psychopy.visual.TextStim(self.win, font=self.style.font, text="Cannot find an eyetracker. Press any key to exit.", color=self.color_pad.red).draw()
            self.win.flip()
            psychopy.event.waitKeys()            
            print >> self.log_f, "Cannot find an eyetracker."
            raise BaseException("Cannot find an eyetracker.")

        # Make a dummy message
        self.findmsg = psychopy.visual.TextStim(self.win, color=self.color_pad.white, units='norm', font=self.style.font,
                                                pos=(0.0, -0.8), height=0.07 )
        self.findmsg.setAutoDraw(True)
        # Make stimuli for the left and right eye
        self.leftStim = psychopy.visual.Circle(self.win,fillColor=self.color_pad.gray, units='cm',
                                               radius=1, autoDraw=True)
        self.rightStim = psychopy.visual.Circle(self.win,fillColor=self.color_pad.gray,units='cm',
                                                radius=1, autoDraw=True)
        self.distCursor = psychopy.visual.Rect(self.win, fillColor=self.color_pad.black, lineColor=self.color_pad.black,
                                                units='cm', width=0.5, height=0.25, pos=(9, 0), autoDraw=True)
        # Make a rectangle in the middle to get eyes into
        self.eyeArea = psychopy.visual.Rect(self.win,lineColor=self.color_pad.green, fillColor=self.color_pad.green,
                                            units='cm', lineWidth=3,width=16, height=9,
                                            opacity=0.1, autoDraw=True)
        self.gradientMap = psychopy.visual.ImageStim(self.win, "bitmaps/gradient2.png", units="cm", pos=(8.5, 0), size=(0.8, 9))
        self.gradientMap.setAutoDraw(True)
        self.gradientWrapper = psychopy.visual.Rect(self.win, lineColor=self.color_pad.black, units='cm', 
                                                    width=1, height=9, autoDraw=True, pos=(8.5, 0), lineWidth=3)
        self.txtNotification = psychopy.visual.TextStim(self.win, color=self.color_pad.black, units='cm', font=self.style.font,
                                                        text="BEST AREA", pos=(0, 5))
        self.txtNotification.setAutoDraw(True) 
        
        self.txtNotification2 = psychopy.visual.TextStim(self.win, color=self.color_pad.black, units='cm', font=self.style.font,
                                                        text=">> BEST DISTANCE", pos=(15, 0))
        self.txtNotification2.setAutoDraw(True) 
        # Start tracking
        # self.datafile = None  # we don't want to save this data
        self.datafile_temp, self.datafile = self.datafile, None
        self.startTracking()
        # psychopy.core.wait(0.5)
        psychopy.core.wait(2)
        self.response = []
        while not self.response:
            self.lxyz, self.rxyz = self.getCurrentEyePosition()
            if self.lxyz == (None, None, None) or self.rxyz == (None, None, None):
                continue
            # print self.lxyz, self.rxyz
            center_x, center_y = self.win.size[0]/2, self.win.size[1]/2
            # update the left eye if the values are reasonable
            le_position_x = self.lxyz[0]/10
            le_position_y = self.lxyz[1]/10
            # update the right eye if the values are reasonable
            re_position_x = self.rxyz[0]/10
            re_position_y = self.rxyz[1]/10
            self.leftStim.pos = (le_position_x, le_position_y)
            self.rightStim.pos = (re_position_x, re_position_y)
            # self.leftStim.pos = (0, 0)
            # self.rightStim.pos = (0, 0.5)
            
            # update the distance if the values are reasonable
            self.distance = np.mean([self.lxyz[2], self.rxyz[2]]) / 10
            cursorY = -0.533*self.distance+34.67 # a map function
            if cursorY > 4.5:
                cursorY = 4.5
            if cursorY < -4.5:
                cursorY = -4.5
            self.distCursor.pos = (9, cursorY)
            # print (le_position_x, le_position_y), (re_position_x, re_position_y), self.distance
            if self.distance < 55 or self.distance > 75:
                self.findmsg.color = self.wrongColor
            elif self.distance > 60 and self.distance < 70:
                # correct distance
                # self.findmsg.color = (-1, 1, -1)
                self.findmsg.color = self.correctColor
            else:
                # not really correct
                # self.findmsg.color = (1, 1, 0.2)
                self.findmsg.color = self.warningColor
            self.findmsg.text = "You're currently " + \
                                str(int(self.distance)) + \
                                ("cm away from the screen.\n"
                                 "60~70cm is the best range\n"
                                 "Press [space] to calibrate or "
                                 "[esc] to abort.")
            # print self.rightStim.pos;exit()
            '''
            '''
            delta = 0.05
            if self.eyeArea.contains(self.leftStim.pos) and self.eyeArea.contains(self.rightStim.pos):
                if self.eyeArea.opacity < 0.6:
                    self.eyeArea.opacity += delta
                else:
                    self.eyeArea.opacity = 0.6
                # self.eyeArea.opacity = 0.6
                
                # if self.txtNotification.opacity < 0.6:
                    # self.txtNotification.opacity += delta
                # else:
                    # self.txtNotification.opacity = 0.6
                
            else:
                if self.eyeArea.opacity > 0.1:
                    self.eyeArea.opacity -= delta
                else:
                    self.eyeArea.opacity = 0.1
                
                # if self.txtNotification.opacity > 0.6:
                    # self.txtNotification.opacity -= delta
                # else:
                    # self.txtNotification.opacity = 0.6
            # self.txtNotification.draw()
            self.win.flip()
            self.response = psychopy.event.getKeys(keyList=['space', 'escape'])
            psychopy.core.wait(0.03)
        # Once responded, stop tracking
        self.stopTracking(None)
        self.datafile, self.datafile_temp = self.datafile_temp, None
        
        if 'escape' in self.response:
            raise KeyboardInterrupt("You interrupted the script manually.")
        else:
            # destroy the feedback stimuli and return (empty)
            self.eyeArea.setAutoDraw(False)
            self.txtNotification.setAutoDraw(False)
            self.txtNotification2.setAutoDraw(False)
            self.leftStim.setAutoDraw(False)
            self.rightStim.setAutoDraw(False)
            self.gradientMap.setAutoDraw(False)
            self.gradientWrapper.setAutoDraw(False)
            self.distCursor.setAutoDraw(False)
            self.findmsg.setAutoDraw(False)
            self.leftStim = self.rightStim = self.findmsg = None
            self.win.flip()
            return
        print >> self.log_f, "Done!", tobii_research.get_system_time_stamp()

    def doCalibration(self, calibrationPoints=[(0.5, 0.5), (0.1, 0.9),(0.1, 0.1), (0.9, 0.9),(0.9, 0.1)],
                      calinRadius=4.0, caloutRadius=None, moveFrames=80):
        ###
        ## Notification animation
        ###
        temp_txt = psychopy.visual.TextStim(self.win, font=self.style.font, text="Calibration eyetracker.", color=self.color_pad.black)
        temp_txt.draw()
        self.win.flip()
        modifier = psychopy.event.waitKeys(maxWait=2, keyList=["w"], modifiers=True)
        # print modifier;exit()
        if modifier != None:
            print "modifier is not none"
            # print modifier;exit()
            if modifier[0][0] == 'w' and modifier[0][1]["ctrl"] == True: #userpressedctrlw
                print "Escape calibration"
                return "accept"
                
        self.win.flip()

        print >> self.log_f, "Doing calibration...", tobii_research.get_system_time_stamp(),
        if self.eyetracker is None:
            psychopy.visual.TextStim(self.win, font=self.style.font, text="Cannot find an eyetracker. Press any key to exit.", color=self.color_pad.red).draw()
            self.win.flip()
            psychopy.event.waitKeys()        
            print >> self.log_f, "Cannot find an eyetracker."
            raise BaseException("Cannot find an eyetracker.")

        # set default
        if caloutRadius is None:
            caloutRadius = calinRadius * 8.0
        if calibrationPoints is None:
            calibrationPoints = [(0.5, 0.5), (0.1, 0.9),
                                 (0.1, 0.1), (0.9, 0.9), (0.9, 0.1)]

        self.points = np.random.permutation(calibrationPoints)

        # Make the "outer" circle
        self.calout = psychopy.visual.Circle(self.win, radius=caloutRadius, lineColor=self.color_pad.red,
                                             fillColor=self.color_pad.red, units='pix', autoDraw=True,
                                             pos=self.acsd2pix(self.points[-1]))
        self.calin = psychopy.visual.Circle(self.win, radius=1,lineColor=self.color_pad.black, 
                                             units='pix', autoDraw=True,pos=self.acsd2pix(self.points[-1]))
        # Make a dummy message
        self.calmsg = psychopy.visual.TextStim(self.win, color=self.color_pad.black, font=self.style.font,
                                               units='norm', height=0.07,
                                               pos=(0.0, -0.5))
        
        # Put the eye tracker into the calibration state
        print >> self.log_f, "Start new calibration..."
        self.calibration = tobii_research.ScreenBasedCalibration(self.eyetracker)
        self.calibration.enter_calibration_mode()
        
        # Draw instructions and wait for space key
        self.calmsg.text = ("Focus your eyes on the red dot, "
                            "follow it with your eyes when it moves. \n"
                            "Press [Space] when you're ready.")
        self.calmsg.draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=['space', 'enter'])

        # Go through the calibration points
        for self.point_index in range(len(self.points)):
            # The dot starts at the previous point
            self.calout.pos = \
                self.acsd2pix((self.points[self.point_index - 1][0],
                               self.points[self.point_index - 1][1]))
            self.calin.pos = \
                self.acsd2pix((self.points[self.point_index - 1][0],
                               self.points[self.point_index - 1][1]))
            # The steps for the movement is new - old divided by frames
            self.step = (self.acsd2pix((self.points[self.point_index][0],
                                        self.points[self.point_index][1])) -
                         self.calout.pos) / moveFrames

            # Create a 2D point object
            p = point2D()
            # Add the X and Y coordinates to the tobii point
            p.x, p.y = self.points[self.point_index]
            # print p.x, p.y;exit()
            # Move the point in position (smooth pursuit)
            for frame in range(moveFrames):
                self.calout.pos += self.step
                self.calin.pos += self.step
                # draw & flip
                self.win.flip()

            # Shrink the outer point (gaze fixation)
            for frame in range(moveFrames / 4):
                self.calout.radius -= (caloutRadius -
                                       calinRadius) / (moveFrames / 4)
                self.win.flip()
            
            for frame in range(moveFrames / 4):
                self.calout.radius += ((caloutRadius -
                                       calinRadius)/ 2) / (moveFrames / 4)
                self.win.flip()
                
            for frame in range(moveFrames / 4):
                self.calout.radius -= (caloutRadius -
                                       calinRadius)/2 / (moveFrames / 4)
                self.win.flip()

            # Add this point to the tobii
            status = self.calibration.collect_data(p.x, p.y)
            psychopy.core.wait(0.5)  # first wait to let the eyes settle (MIN 0.5)
            while status != tobii_research.CALIBRATION_STATUS_SUCCESS:
                psychopy.core.wait(0.5)
                self.calibration.collect_data(p.x, p.y)

            # Reset the radius of the large circle
            self.calout.radius = caloutRadius

        # After calibration, make sure the stimuli aren't drawn
        self.calout.autoDraw = False
        self.calin.autoDraw = False
        self.calout = None

        # Do compute and apply and get result
        calibration_result = self.calibration.compute_and_apply()
        print calibration_result.status
        for cp in calibration_result.calibration_points:
            print cp
            print cp.position_on_display_area
            for cs in cp.calibration_samples:
                print cs.left_eye.position_on_display_area, cs.right_eye.position_on_display_area
        
        # recalibrate_point = (0.1, 0.1)
        # calibration.discard_data(recalibrate_point[0], recalibrate_point[1])

        self.win.flip()

        if calibration_result.status == tobii_research.CALIBRATION_STATUS_FAILURE:
            # computeCalibration failed.
            self.calmsg.text = ("Not enough data was collected "
                                "(Retry:[r] Abort:[ESC])")
        elif calibration_result is None:
            # no calibration data
            self.calmsg.text = ("No calibration data "
                                "(Retry:[r] Abort:[ESC])")
        else:
            # calibration seems to have worked out
            calib_points = {}

            for cp in calibration_result.calibration_points:
                calib_points[cp.position_on_display_area] = cp.calibration_samples

            if len(calib_points) == 0:
                # no points in the calibration results
                self.calmsg.text = ("No calibration data "
                                    "(Retry:[r] Abort:[ESC])")
            else:
                # draw the calibration result
                for c_p, s_ps in calib_points.iteritems():
                    psychopy.visual.Circle(self.win, radius=calinRadius,
                                           fillColor=self.color_pad.white,
                                           units='pix',
                                           pos=self.acsd2pix(c_p)).draw()
                    print c_p
                    for s_p in s_ps:
                        print self.acsd2pix((c_p[0], c_p[1])),
                        print self.acsd2pix((s_p.left_eye.position_on_display_area)),
                        print self.acsd2pix((s_p.right_eye.position_on_display_area)), 
                        print s_p.left_eye.validity, s_p.right_eye.validity
                        
                        if s_p.left_eye.validity == tobii_research.VALIDITY_VALID_AND_USED:
                            psychopy.visual.Line(self.win, units='pix',
                                                 lineWidth=2,
                                                 lineColor=self.color_pad.blue,
                                                 start=self.acsd2pix(c_p),
                                                 end=self.acsd2pix(s_p.left_eye.position_on_display_area)).draw()
                        if s_p.right_eye.validity == tobii_research.VALIDITY_VALID_AND_USED:
                            psychopy.visual.Line(self.win, units='pix',
                                                 lineWidth=2,
                                                 lineColor=self.color_pad.green,    
                                                 start=self.acsd2pix(c_p),
                                                 end=self.acsd2pix(s_p.right_eye.position_on_display_area)).draw()
                        print 
                self.calmsg.text = ("Accept calibration results\n"
                                    "(Accept:[a] Retry:[r] Abort:[ESC])")

        self.calibration.leave_calibration_mode()
        # Update the screen, then wait for response
        self.calmsg.draw()
        self.win.flip()
        self.response = psychopy.event.waitKeys(keyList=['a', 'r', 'escape'])
        if 'a' in self.response:
            retval = 'accept'
            print >> self.log_f, "accept is pressed!", tobii_research.get_system_time_stamp()
        elif 'r' in self.response:
            retval = 'retry'
            print >> self.log_f, "retry is pressed!", tobii_research.get_system_time_stamp()
        elif 'escape' in self.response:
            retval = 'abort'
            print >> self.log_f, "abort is pressed!", tobii_research.get_system_time_stamp()

        return retval

    ############################################################################
    # tracking methods
    ############################################################################
    """
    gazeData is a list of gaze dictionary.
    gaze dictionary contains:
        ## time stamp
        system_time_stamp
        device_time_stamp
        
        ## validity
        left_pupil_validity
        right_pupil_validity
        left_gaze_origin_validity
        right_gaze_origin_validity
        left_gaze_point_validity
        right_gaze_point_validity
        
        ## gaze data
        left_pupil_diameter: float diameter (millimeters) 
        right_pupil_diameter
        left_gaze_point_in_user_coordinate_system: [x, y, z]
        right_gaze_point_in_user_coordinate_system
        left_gaze_origin_in_user_coordinate_system: [x, y, z]
        right_gaze_origin_in_user_coordinate_system
        left_gaze_origin_in_trackbox_coordinate_system: [x, y, z]
        right_gaze_origin_in_trackbox_coordinate_system
        left_gaze_point_on_display_area: [x, y]
        right_gaze_point_on_display_area
    """
    def startTracking(self):
        if self.eyetracker == None:
            # print
            return
        # creates a gaze data list and starts tobii tracking, appending
        # each data point to the list
        print >> self.log_f, "Start tracking...", tobii_research.get_system_time_stamp()
        self.gazeData = []
        self.eventData = []
        self.eyetracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA, self.on_gazedata, as_dictionary=True)

    def stopTracking(self, data_fn):
        if self.eyetracker == None:
            # print
            return
        # stops tobii tracking, writes data to file, and empties the
        # gaze data list
        print >> self.log_f, "Stop tracking...", tobii_research.get_system_time_stamp()
        self.eyetracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA)
        if not data_fn == None:
            self.flushData(data_fn)
        self.gazeData = []
        self.eventData = []

    def on_gazedata(self,gaze_data):
        # this gets called by tobii when subscribe_to get called
        self.gazeData.append(gaze_data)
    
    def getGazePosition(self, gaze):
        # returns gaze position in pixl relative to center
        ## gaze is a dictionary
        return self.acsd2pix(gaze["left_gaze_point_on_display_area"]), \
                self.acsd2pix(gaze["right_gaze_point_on_display_area"])

    def getCurrentGazePosition(self):
        # returns the most recent gaze data point
        # format is ((left.x, left.y), (right.x, right.y))
        if len(self.gazeData) == 0:
            return (None, None, None, None)
        else:
            return self.getGazePosition(self.gazeData[-1])

    def getCurrentGazeAverage(self):
        # returns the most recent average gaze position
        # x and y
        if len(self.gazeData) == 0:
            return (None, None, None, None)
        else:
            lastGaze = self.gazeData[-1]
            if lastGaze["left_gaze_point_validity"] != 0 and lastGaze["right_gaze_point_validity"] != 0:
                # return average data
                return self.acsd2pix((np.mean((lastGaze["left_gaze_point_in_user_coordinate_system"][0],
                                               lastGaze["right_gaze_point_in_user_coordinate_system"][0])),
                                      np.mean((lastGaze["left_gaze_point_in_user_coordinate_system"][1],
                                               lastGaze["right_gaze_point_in_user_coordinate_system"][1]))))
            elif lastGaze["left_gaze_point_validity"] != 0 and lastGaze["right_gaze_point_validity"] == 0:
                # only return left data
                return self.acsd2pix(lastGaze["left_gaze_point_in_user_coordinate_system"][0],
                                     lastGaze["left_gaze_point_in_user_coordinate_system"][1])
            elif lastGaze["left_gaze_point_validity"] == 0 and lastGaze["right_gaze_point_validity"] != 0:
                # only return right data
                return self.acsd2pix(lastGaze["right_gaze_point_in_user_coordinate_system"][0],
                                     lastGaze["right_gaze_point_in_user_coordinate_system"][1])
    '''
    def getCurrentValidity(self):
        if len(self.gazeData) == 0:
            return (None, None, None, None)
        else:
            return (self.gazeData[-1].LeftValidity,
                    self.gazeData[-1].RightValidity)
    
    
    def waitForFixation(self, fixationPoint=(0, 0),
                        bothEyes=True, errorMargin=0.1):
        # this function waits until the eye tracker detects one (or both)
        # eyes to be at a certain point, +- some margin of error
        # fixation point should be given in pixels
        # first, make sure data is not saved:
        self.datafile_temp, self.datafile = self.datafile, None
        self.startTracking()  # kick off tracking
        psychopy.core.wait(0.5)  # allow the tracker to gather some data
        while (abs(self.getCurrentGazeAverage()[0] -
                   fixationPoint[0]) < errorMargin and
               abs(self.getCurrentGazeAverage()[1] -
                   fixationPoint[1]) < errorMargin and
               (not bothEyes or (self.getCurrentValidity()[0] != 4 and
                                 self.getCurrentValidity()[1] != 4))):
            psychopy.core.wait(0.05)  # wait 50ms before checking again
        self.stopTracking()  # stop tracking
        # then restore data file so tracking can continue
        self.datafile, self.datafile_temp = self.datafile_temp, None
    '''

    def getCurrentEyePosition(self):
        # returns the most recent eye position
        if len(self.gazeData) == 0:
            return((None, None, None), (None, None, None))
        else:
            self.gaze = self.gazeData[-1]
            ## gaze is a dictionary
            if self.gaze["left_gaze_origin_validity"] != 0 and self.gaze["right_gaze_origin_validity"] != 0:
                return ((self.gaze["left_gaze_origin_in_user_coordinate_system"][0],
                         self.gaze["left_gaze_origin_in_user_coordinate_system"][1],
                         self.gaze["left_gaze_origin_in_user_coordinate_system"][2]),
                        (self.gaze["right_gaze_origin_in_user_coordinate_system"][0],
                         self.gaze["right_gaze_origin_in_user_coordinate_system"][1],
                         self.gaze["right_gaze_origin_in_user_coordinate_system"][2]))
            else:
                return ((None, None, None), (None, None, None))
    def getCurrentPupilDiameter(self):
        if len(self.gazeData) == 0:
            return(None, None)
        else:
            ## check validity
            return(self.gazeData[-1]["left_pupil_diameter"],
                   self.gazeData[-1]["left_pupil_diameter"])
    '''
    def setDataFile(self, filename):
        if filename is None:
            self.datafile = None
        else:
            print 'set datafile ' + filename
            self.datafile = open(filename, 'w+')
            self.datafile.write('Recording date:\t' +
                                datetime.datetime.now().strftime('%Y/%m/%d') +
                                '\n')
            self.datafile.write('Recording time:\t' +
                                datetime.datetime.now().strftime('%H:%M:%S') +
                                '\n')
            self.datafile.write('Recording resolution\t%d x %d\n\n' %
                                tuple(self.win.size))
    '''
    def closeDataFile(self, data_fn):
        print 'datafile closed'
        if self.datafile is not None:
            self.flushData(data_fn)
            self.datafile.close()
        self.datafile = None

    def recordEvent(self, event):
        if self.eyetracker == None:
            return
        t = self.get_system_time()
        self.eventData.append((t, event))

    def flushData(self, data_fn):
        # if self.datafile is None:
            # print "Data file is not set, data not saved."
            # return
        if data_fn is None:
            print >> self.log_f, "data_fn is None, abort."
            return
        print >> self.log_f, "Set datafile", data_fn
        data_path = os.path.join(self.path, data_fn)
        self.datafile = open(data_path, "w")
        
        if len(self.gazeData) == 0:
            print >> self.log_f, "No gazedata collected, no data saved."
            return

        print >> self.log_f, "Saving data."
        self.datafile.write("Eye gaze information.\n")
        self.datafile.write(', '.join( ['system_time_stamp',
                                        'device_time_stamp',
                                        'left_pupil_validity',
                                        'right_pupil_validity',
                                        'left_gaze_origin_validity',
                                        'right_gaze_origin_validity',
                                        'left_gaze_point_validity',
                                        'right_gaze_point_validity',
                                        'left_pupil_diameter',
                                        'right_pupil_diameter',
                                        'left_gaze_origin_in_user_coordinate_system-X',
                                        'left_gaze_origin_in_user_coordinate_system-Y',
                                        'left_gaze_origin_in_user_coordinate_system-Z',
                                        'right_gaze_origin_in_user_coordinate_system-X',
                                        'right_gaze_origin_in_user_coordinate_system-Y',
                                        'right_gaze_origin_in_user_coordinate_system-Z',
                                        'left_gaze_origin_in_trackbox_coordinate_system-X',
                                        'left_gaze_origin_in_trackbox_coordinate_system-Y',
                                        'left_gaze_origin_in_trackbox_coordinate_system-Z',
                                        'right_gaze_origin_in_trackbox_coordinate_system-X',
                                        'right_gaze_origin_in_trackbox_coordinate_system-Y',
                                        'right_gaze_origin_in_trackbox_coordinate_system-Z',
                                        'left_gaze_point_in_user_coordinate_system-X',
                                        'left_gaze_point_in_user_coordinate_system-Y',
                                        'left_gaze_point_in_user_coordinate_system-Z',
                                        'right_gaze_point_in_user_coordinate_system-X',
                                        'right_gaze_point_in_user_coordinate_system-Y',
                                        'right_gaze_point_in_user_coordinate_system-Z',
                                        'left_gaze_point_on_display_area-X',
                                        'left_gaze_point_on_display_area-Y',
                                        'right_gaze_point_on_display_area-X',
                                        'right_gaze_point_on_display_area-Y']) + '\n')
        systimeStampStart = self.gazeData[0]["system_time_stamp"] # first timepoint is 0s
        dvctimeStampStart = self.gazeData[0]["device_time_stamp"] # first timepoint is 0s
        
        # Write eye info
        print >> self.log_f, "Write eye info.."
        for g in self.gazeData:
            self.datafile.write(', '.join([
                '%d' % ((g["system_time_stamp"])),
                # '%d' % ((g["device_time_stamp"] - dvctimeStampStart)),
                '%d' % ((g["device_time_stamp"])),
                '%d' % g["left_pupil_validity"],
                '%d' % g["right_pupil_validity"],
                '%d' % g["left_gaze_origin_validity"],
                '%d' % g["right_gaze_origin_validity"],
                '%d' % g["left_gaze_point_validity"],
                '%d' % g["right_gaze_point_validity"],
                '%.4f' % g["left_pupil_diameter"],
                '%.4f' % g["right_pupil_diameter"],
                '%.4f' % g["left_gaze_origin_in_user_coordinate_system"][0],
                '%.4f' % g["left_gaze_origin_in_user_coordinate_system"][1],
                '%.4f' % g["left_gaze_origin_in_user_coordinate_system"][2],
                '%.4f' % g["right_gaze_origin_in_user_coordinate_system"][0],
                '%.4f' % g["right_gaze_origin_in_user_coordinate_system"][1],
                '%.4f' % g["right_gaze_origin_in_user_coordinate_system"][2],
                '%.4f' % g["left_gaze_origin_in_trackbox_coordinate_system"][0],
                '%.4f' % g["left_gaze_origin_in_trackbox_coordinate_system"][1],
                '%.4f' % g["left_gaze_origin_in_trackbox_coordinate_system"][2],
                '%.4f' % g["right_gaze_origin_in_trackbox_coordinate_system"][0],
                '%.4f' % g["right_gaze_origin_in_trackbox_coordinate_system"][1],
                '%.4f' % g["right_gaze_origin_in_trackbox_coordinate_system"][2],
                '%.4f' % g["left_gaze_point_in_user_coordinate_system"][0],
                '%.4f' % g["left_gaze_point_in_user_coordinate_system"][1],
                '%.4f' % g["left_gaze_point_in_user_coordinate_system"][2],
                '%.4f' % g["right_gaze_point_in_user_coordinate_system"][0],
                '%.4f' % g["right_gaze_point_in_user_coordinate_system"][1],
                '%.4f' % g["right_gaze_point_in_user_coordinate_system"][2],
                '%.4f' % g["left_gaze_point_on_display_area"][0],
                '%.4f' % g["left_gaze_point_on_display_area"][1],
                '%.4f' % g["right_gaze_point_on_display_area"][0],
                '%.4f' % g["right_gaze_point_on_display_area"][1]]) + '\n')
        # Write the additional event data added
        print >> self.log_f, "Write event info.."
        self.datafile.write("Event information.\n")
        for e in self.eventData:
            self.datafile.write(('%d' + ', ' + '%s\n') %
                                (e[0], e[1]))
        
        # flush the python data buffer (data written to file)
        self.datafile.flush()
        print >> self.log_f, "Done!"
        
    ########################################################################
    # helper functions
    ########################################################################

    def acsd2pix(self, xy):
        # Convert the tobii coordinates (acsd) to pixels
        # in tobii, (0, 0) is top left
        # in psychopy, (0, 0) is the middle
        return (int((xy[0] - 0.5) * self.win.size[0]),
                int((0.5 - xy[1]) * self.win.size[1]))
    ########################################################################
    # Demo
    ########################################################################

    def tracking_demo(self):
        print "Enter tracking demo..."
        marker = psychopy.visual.Circle(win, units='pix', lineColor=self.color_pad.black,radius=3, autoDraw=True)
        self.startTracking()
        resp = []
        psychopy.visual.TextStim(self.win, color=self.color_pad.white, font=self.style.font, units='norm', pos=(0.0, -0.8),height=0.07, text="Tracking demo\nPress [space] to start\nPress [esc] to quit").draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=['space'])
        while 'escape' not in resp:
            currentGazePosition = self.getCurrentGazePosition()
            if None not in currentGazePosition:
                # set marker to arithmetic mean of the two gaze poisitions
                position = (np.mean((currentGazePosition[0][0],
                                       currentGazePosition[1][0])),
                              np.mean((currentGazePosition[0][1],
                                       currentGazePosition[1][1])))
                marker.pos = position
            win.flip()
            psychopy.core.wait(0.01)
            resp = psychopy.event.getKeys()

        self.stopTracking(None)
        
    def fixpoint_demo(self):
        print "Enter fixpoint demo..."
        self.win.flip()
        psychopy.event.clearEvents()
        dummy_points = [(0.1, 0.1), (0.9, 0.1), (0.5, 0.5), (0.1, 0.9), (0.9, 0.9), (0.9, 0.5), (0.5, 0.9), (0.5, 0.1), (0.1, 0.5)]
        for point in dummy_points:
            psychopy.visual.Circle(self.win, radius=10,lineColor=self.color_pad.red,fillColor=self.color_pad.red,units='pix',pos=self.acsd2pix(point)).draw()
        psychopy.visual.TextStim(self.win, color=self.color_pad.gray, font=self.style.font, units='norm', pos=(0.0, -0.5),height=0.07, text="Fix points demo\nPress [space] to start\nPress [esc] to quit").draw()
        self.win.flip()
        psychopy.event.waitKeys(keyList=['space'])
        resp = []
        self.startTracking()
        while 'escape' not in resp:
            for point in dummy_points:
                psychopy.visual.Circle(self.win, radius=10,lineColor=self.color_pad.red,fillColor=self.color_pad.red,units='pix',pos=self.acsd2pix(point)).draw()
            vision_circle = psychopy.visual.Circle(self.win, radius=25, lineColor=self.color_pad.black, lineWidth=2, units='pix')
            currentGazePosition = self.getCurrentGazePosition()
            if None not in currentGazePosition:
                position = (np.mean((currentGazePosition[0][0],
                                       currentGazePosition[1][0])),
                              np.mean((currentGazePosition[0][1],
                                       currentGazePosition[1][1])))
                vision_circle.pos = position
                vision_circle.draw()
            win.flip()
            psychopy.core.wait(0.01)
            resp = psychopy.event.getKeys()
        self.stopTracking(None)
        
    def image_demo(self, imagePath_list, duration = 5, visual=True):
        print "Enter image demo..."
        self.win.flip()
        ## check imagePath_list
        for i in range(len(imagePath_list)):
            if not os.path.exists(imagePath_list[i]):
                print imagePath_list, "not exists.Ignore it."
                del imagePath_list[i]
        imagePath_list = np.random.permutation(imagePath_list)
        psychopy.visual.TextStim(self.win, color=self.color_pad.white,units='norm', font=self.style.font, pos=(0.0, -0.5),height=0.07, text="Image fixation demo\nPress [space] to start\nPress [esc] to quit").draw()
        self.win.flip()
        self.startTracking()
        for imagePath in imagePath_list:
            img = psychopy.visual.ImageStim(self.win, image=imagePath)
            self.win.flip()
            save_position = []
            
            last_position = (0, 0)
            start_t = datetime.datetime.now()
            elapse_s = 0
            while elapse_s < duration:
                img.draw()
                currentGazePosition = self.getCurrentGazePosition()
                if None not in currentGazePosition:
                    position = (np.mean((currentGazePosition[0][0],currentGazePosition[1][0])),\
                                np.mean((currentGazePosition[0][1],currentGazePosition[1][1])))
                    if visual:
                        psychopy.visual.Line(self.win, units='pix',lineWidth=2,lineColor=self.color_pad.white,start=last_position,end=position).draw()
                        last_position=position
                    save_position.append(position)
                win.flip()
                psychopy.core.wait(0.01)
                elapse_s = (datetime.datetime.now() - start_t).seconds
            img.draw()
            for position in save_position:
                psychopy.visual.Circle(self.win,lineColor=self.color_pad.red, units='pix',radius=1, pos=position).draw()
            self.win.flip()
            del save_position
            psychopy.core.wait(2)
        self.stopTracking(None)
        
    def video_demo(self, videoPath_list):
        print "Enter movie demo..."
        
        ## Check videoPath_list
        for i in range(len(videoPath_list)):
            if not os.path.exists(videoPath_list[i]):
                print videoPath_list, "not exists.Ignore it."
                del videoPath_list[i]
        # videoPath_list = np.random.permutation(videoPath_list)
        psychopy.visual.TextStim(self.win, color=self.color_pad.white, units='norm', font=self.style.font, pos=(0.0, -0.5),height=0.07, text="Video fixation demo\nPress [space] to start\nPress [esc] to quit").draw()
        self.win.flip()
        psychopy.event.getKeys(["space"])
        self.startTracking()
        for videoPath in videoPath_list:
            print "Handling", videoPath
            vid = psychopy.visual.MovieStim(self.win, filename=videoPath, autoLog=True,
                flipVert=False, flipHoriz=False, loop=True)
            # vid.autoDraw = True
            start_time = self.get_system_time()
            now_time = self.get_system_time()
            duration = now_time-start_time
            print duration # microsecond
            # while vid.status != psychopy.visual.FINISHED:
            while duration < 5*1e6:
                # print type(vid), vid.status
                print duration, 
                v_d = vid.draw()
                print v_d
                self.win.flip()
                v_d = vid.draw()
                print v_d
                now_time = self.get_system_time()
                # previous_duration = duration
                duration = now_time-start_time
                # print duration - previous_duration
                # if psychopy.event.getKeys():
                    # break
            print "Handling done", videoPath
            # vid.stop()
            # vid = None
            # self.win.flip()
        
        self.win.flip()
        
    def mpv_demo(self, videoPath_list, interval=3):
        print "Enter mpv movie demo..."
        self.win.flip()
        self.win.setColor(self.color_pad.red)
        # self.win.setMouseVisible(False)
        
        ## Check videoPath_list
        for i in range(len(videoPath_list)):
            if not os.path.exists(videoPath_list[i]):
                print videoPath_list, "not exists.Ignore it."
                del videoPath_list[i]
                
        for videoPath in videoPath_list:
            cmd = '{} {}'.format('mpv --no-input-cursor --ontop --video-unscaled=yes --fs --video-zoom=0 --no-taskbar-progress --no-border --no-window-dragging --cache-secs=5 ', videoPath)
            
            psychopy.core.wait(interval) 
            s_t = self.get_system_time()
            os.system(cmd)
            n_t = self.get_system_time()
            print n_t - s_t
            
    def vlc_demo(self, videoPath_list):
        import vlc
        try:
            from msvcrt import getch
        except ImportError:
            import termios
            import tty

            def getch():  # getchar(), getc(stdin)  #PYCHOK flake
                fd = sys.stdin.fileno()
                old = termios.tcgetattr(fd)
                try:
                    tty.setraw(fd)
                    ch = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old)
                return ch
                
        movie = videoPath_list[0]
        if not os.access(movie, os.R_OK):
            print('Error: %s file not readable' % movie)
            sys.exit(1)
            
        # instance = vlc.Instance("-f")
        instance = vlc.Instance("")
        try:
            media = instance.media_new(movie)
        except NameError:
            print('NameError: %s (%s vs LibVLC %s)' % (sys.exc_info()[1],
                                                       __version__,
                                                       libvlc_get_version()))
            sys.exit(1)
        print media.get_mrl()
        player = instance.media_player_new()
        player.set_media(media)
        player.set_fullscreen(True)
        player.video_set_scale(1)
        print player.get_fps()
        
        # s_t = self.get_system_time()
        # os.system(cmd)
        # player.play()
        # n_t = self.get_system_time()
        # print n_t - s_t
        
        while True:
            k = getch()
            if k == 'q':
            # print('> %s' % k)
            # if k in keybindings:
                # keybindings[k]()
            # elif k.isdigit():
                 # # jump to fraction of the movie.
                # player.set_position(float('0.'+k))
                break
                
    def mplayer_demo(self):
        # import mplayer as mp
        
        self.win.color = self.color_pad.black
        self.win.flip() # clear current psychopy window
        import MplayerCtrl as mpc
        class Frame(wx.Frame):
            start_time = None
            end_time = None
            app = None
            mpc = None
            tbc = None
            def __init__(self, parent, id, title, mplayer, media_file, tb_controller):
                self.app = wx.App(redirect=False)
                wx.Frame.__init__(self, parent, id, title, style=wx.STAY_ON_TOP)
                cursor = wx.StockCursor(wx.CURSOR_BLANK)
                self.SetCursor(cursor)
                # self.panel = wx.Panel(self)
                self.media_file = media_file
                # self.mpc = mpc.MplayerCtrl(self, -1, mplayer, media_file)
                self.mpc = mpc.MplayerCtrl(self, -1, mplayer, keep_pause=True)
                self.Bind(mpc.EVT_PROCESS_STARTED, self.on_process_started)
                self.Bind(mpc.EVT_MEDIA_STARTED, self.on_media_started)
                self.Bind(mpc.EVT_MEDIA_FINISHED, self.on_media_finished)
                self.Bind(mpc.EVT_PROCESS_STOPPED, self.on_process_stopped)
                self.tbc = tb_controller
                
                # self.Maximize(True)
                self.ShowFullScreen(True)
                # self.Center()
                self.Show()
                # self.mpc.Start(media_file)
                # length = self.mpc.GetProperty('length')
                # print length
                self.app.MainLoop()
                
            def on_process_started(self, evt):
                print 'Process started'
                print self.mpc.GetTimeLength()
                print '----------> Process started'
                # self.mpc.Loadfile(self.media_file)
                self.mpc.Loadlist(u'playlist.txt')
                self.mpc.Pause()
                self.tbc.gazeData = []
                self.tbc.eventData = []
                self.tbc.startTracking()
                # length = frame.mpc.GetProperty('length')
                # print length
                
            def on_media_started(self, evt):
                print 'Media started'
                self.start_time = self.tbc.get_system_time()
                print "start time", self.start_time
                
            def on_media_finished(self, evt):
                print 'Media finished'
                self.end_time = self.tbc.get_system_time()
                print "end time", self.end_time
                print "duration", self.end_time - self.start_time
                # self.mpc.Pause()
                # time.sleep(3)
                # self.mpc.Pause()
                # self.mpc.Quit()
                # exit()
                
            def on_process_stopped(self, evt):
                print 'Process stopped'
                self.tbc.stopTracking()

        ## first generate play list
        test_video_dir = "D:/Data/VIDEOS/REFERENCE_qp_00/videos/"
        test_video_name_list = os.listdir(test_video_dir)
        np.random.shuffle(test_video_name_list)
        test_video_name_list = test_video_name_list[:2]
        blank_path = "test_videos/3sblack.avi"
        w_f = open("playlist.txt", "w")
        for test_video_name in test_video_name_list:
            test_video_path = os.path.join(test_video_dir, test_video_name)
            print >> w_f, blank_path
            print >> w_f , test_video_path
        w_f.close()
        
        frame = Frame(None, -1, "Mplayer demo", u'mplayer', u'videoSRC004_1920x1080_30_qp_00.avi', self)
               
    def mplayer_seperatevo_demo(self):
        rest_message = "Rest your eye for a while."
        count_down_seconds = 10
        print >> self.log_f, "Begin test sequence."
        # self.win.color = self.color_pad.black
        self.win.flip() # clear current psychopy window
        import MplayerCtrl as mpc
        class Frame(wx.Frame):
            start_time = None
            end_time = None
            mpc = None
            tbc = None
            counter = 0
            def __init__(self, parent, id, title, mplayer, sequence_list, data_fn, tb_controller):
                wx.Frame.__init__(self, parent, id, title, style=wx.STAY_ON_TOP)
                self.files = iter(sequence_list)
                self.tbc = tb_controller
                ## cursor invisible
                cursor = wx.StockCursor(wx.CURSOR_BLANK)
                self.SetCursor(cursor)
                self.data_fn = data_fn
                self.mpc = mpc.MplayerCtrl(self, -1, mplayer, keep_pause=False)
                self.SetBackgroundColour('black')
                self.Bind(mpc.EVT_PROCESS_STARTED, self.on_process_started)
                self.Bind(mpc.EVT_MEDIA_STARTED, self.on_media_started)
                self.Bind(mpc.EVT_MEDIA_FINISHED, self.on_media_finished)
                self.Bind(mpc.EVT_PROCESS_STOPPED, self.on_process_stopped)
                
                self.ShowFullScreen(True)
                self.Show()
                self.mpc.Start()
                self.cur_media = self.files.next()
                self.mpc.Loadfile(self.cur_media)
                
            def on_process_started(self, evt):
                print >> self.tbc.log_f, 'Process started'
                print >> self.tbc.log_f, '----------> Process started'
                self.tbc.startTracking()
                
            def on_media_started(self, evt):
                print >> self.tbc.log_f, 'Media started:', self.cur_media
                self.start_time = self.tbc.get_system_time()
                event = self.cur_media, "start playing."
                self.tbc.recordEvent(event)
                print >> self.tbc.log_f, "start time", self.start_time
                
            def on_media_finished(self, evt):
                print >> self.tbc.log_f, 'Media finished'
                self.end_time = self.tbc.get_system_time()
                event = self.cur_media, "stop playing.", "Duration(microsecond):", self.end_time-self.start_time
                self.tbc.recordEvent(event)
                print >> self.tbc.log_f, "end time", self.end_time
                print >> self.tbc.log_f, "duration", self.end_time - self.start_time
                try:
                    self.cur_media = self.files.next()
                    # print next_file, self.tbc.get_system_time()
                    self.mpc.Loadfile(self.cur_media)
                except StopIteration:
                    print >> self.tbc.log_f, 'no more files in the playlist!'
                    print >> self.tbc.log_f, 'Quitting the mplayer'
                    self.tbc.stopTracking(self.data_fn)
                    self.mpc.Destroy()
                    self.Close()
                    
            def on_process_stopped(self, evt):
                print >> self.tbc.log_f, 'Process stopped'
                self.Close()

        ## first generate play list
        test_video_dir = "D:/Data/VIDEOS/REFERENCE_qp_00/videos/"
        print >> self.log_f, "Reading videos in", test_video_dir
        test_video_name_list = os.listdir(test_video_dir) ##pick a subset of videos for sunnycia's test
        random.shuffle(test_video_name_list)
        test_video_name_list = test_video_name_list[:12] ## Comment this when put into use
        
        ## divide into 4 lists, 
        test_video_name_arr = np.array(test_video_name_list)
        test_list1, test_list2, test_list3, test_list4 = np.split(test_video_name_arr, 4)
        
        print >> self.log_f, "sequence 1"
        
        # test_list = test_video_name_list[:2]
        blank_path = "test_videos/3sblack.avi"
        test_sequence = []
        for test_video_name in test_list1:
            test_video_path = os.path.join(test_video_dir, test_video_name)
            test_sequence.append(blank_path)
            test_sequence.append(test_video_path)
            
        app = wx.App()
        frame = Frame(None, -1, "Mplayer demo", u'mplayer', test_sequence,"seq1.csv", self)
        app.MainLoop()
        # app.Destroy()
        resp = []
        psychopy.event.clearEvents()
        print >> self.log_f, "Finished sequence 1. Now Resting..."
        txtRest = psychopy.visual.TextStim(win, color=self.color_pad.white, units='norm', font=self.style.font, pos=(0.0, 0.0),height=0.07)
        count_down(self.win, count_down_seconds, text=rest_message) ## 3 min count down
        txtRest.text = "Press [Space] to continue."
        txtRest.draw()
        self.win.flip()
        while not resp:
            resp = psychopy.event.waitKeys(keyList=['space'])
            psychopy.core.wait(0.5)
        self.win.flip()
        
        test_sequence = []
        for test_video_name in test_list2:
            test_video_path = os.path.join(test_video_dir, test_video_name)
            test_sequence.append(blank_path)
            test_sequence.append(test_video_path)
        frame = Frame(None, -1, "Mplayer", u"mplayer", test_sequence, "seq2.csv", self)
        app.MainLoop() 
        # app.Destroy()
        resp = []
        psychopy.event.clearEvents() 
        txtRest = psychopy.visual.TextStim(win, color=self.color_pad.white, units='norm', font=self.style.font, pos=(0.0, 0.0),height=0.07) 
        print >> self.log_f, "Finished sequence 2. Now Resting..."
        count_down(self.win, count_down_seconds, text=rest_message) ## 3 min count down
        txtRest.text = "Press [Space] to continue."
        txtRest.draw()
        self.win.flip()
        while not resp:
            resp = psychopy.event.waitKeys(keyList=['space'])
            psychopy.core.wait(0.5)
        self.win.flip()
        
        test_sequence = []
        for test_video_name in test_list3:
            test_video_path = os.path.join(test_video_dir, test_video_name)
            test_sequence.append(blank_path)
            test_sequence.append(test_video_path)
        # app = wx.PySimpleApp()
        frame = Frame(None, -1, "Mplayer", u"mplayer", test_sequence, "seq3.csv", self)
        app.MainLoop()
        # app.Destroy()
        resp = []
        psychopy.event.clearEvents()
        txtRest = psychopy.visual.TextStim(win, color=self.color_pad.white, units='norm', font=self.style.font, pos=(0.0, 0.0),height=0.07)
        print >> self.log_f, "Finished sequence 3. Now Resting..."
        count_down(self.win, count_down_seconds, text=rest_message) ## 3 min count down
        txtRest.text = "Press [Space] to continue."
        txtRest.draw()
        self.win.flip()
        while not resp:
            resp = psychopy.event.waitKeys(keyList=['space'])
            psychopy.core.wait(0.5)
        self.win.flip()
        
        test_sequence = []
        for test_video_name in test_list4:
            test_video_path = os.path.join(test_video_dir, test_video_name)
            test_sequence.append(blank_path)
            test_sequence.append(test_video_path)
        # app = wx.PySimpleApp()
        frame = Frame(None, -1, "Mplayer", u"mplayer", test_sequence, "seq4.csv", self)
        app.MainLoop()

        resp = []
        psychopy.event.clearEvents()
        txtRest = psychopy.visual.TextStim(win, color=self.color_pad.white, units='norm', font=self.style.font, pos=(0.0, 0.0),height=0.07)
        print >> self.log_f, "Finished sequence 4."
        txtRest.text = "All Done!\nThank you for your participant."
        txtRest.draw()
        self.win.flip()
        while not resp:
            resp = psychopy.event.waitKeys(keyList=['space'])
            psychopy.core.wait(0.5)
        self.win.flip()

    def game_demo(self):
        pass

class Subject:
    subject_name = None
    subject_id = None
    subject_gender = None
    subject_phonenumber = None
    subject_age = None
    subject_glasses = None
    path = None
    def __init__(self):
        '''
        r_f = open("sample_subj.pkl", "rb")
        info = cPickle.load(r_f)
        tip = cPickle.load(r_f)
        dlg = psychopy.gui.DlgFromDict(dictionary=info, title="Subject text", tip=tip)
        dlg.style=wx.STAY_ON_TOP
        if dlg.OK:
            print info
        else:
            print "User cancelled."
        '''
        dlg = psychopy.gui.Dlg(title="Subject info", labelButtonCancel="Exit")
        dlg.addText("Input your information", color="Blue")
        dlg.addField("Name:", "SZH", tip="your name abbreviation. e.g. SZH")
        dlg.addField("Student ID:", "2161230402", tip="your name abbreviation. e.g. 2161230402")
        dlg.addField("Phone No.:", "15112585779", tip="your mobile number. e.g. 15112585779")
        dlg.addField("Age:", 20)
        dlg.addField("Gender:", choices=["Male", "Female"])
        dlg.addField("Wear Glasses:", initial=False, tip="check it if you wear glasses.")
        
        subj_info = dlg.show()
        if dlg.OK:
            self.subject_name = subj_info[0]
            self.subject_id = subj_info[1]
            self.subject_phonenumber = subj_info[2]
            self.subject_age = subj_info[3]
            self.subject_gender = subj_info[4]
            self.subject_glasses = subj_info[5]
            
            ## save in database
            resultDir = "testResult"
            if not os.path.isdir(resultDir):
                os.mkdir(resultDir)
            
            subj_count = len(os.listdir(resultDir))
            cur_index = subj_count + 1
            subjectDir= os.path.join(resultDir, str(cur_index) +"_"+ self.subject_id +"_"+ self.subject_name)
            if not os.path.isdir(os.path.join(resultDir, subjectDir)):
                os.mkdir(subjectDir)
            else:
                ## not likely to go through following code
                cur_index += 1
                subjectDir= os.path.join(resultDir, str(cur_index) +"_"+ self.subject_id +"_"+ self.subject_name)
                os.mkdir(subjectDir)
            
            self.path = subjectDir
            
            basic_info_fn = "log.txt"
            w_f = open(os.path.join(self.path, basic_info_fn), "w")
            print >> w_f, "Text index:", cur_index
            print >> w_f, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            print >> w_f, "Name", self.subject_name
            print >> w_f, "ID", self.subject_id
            print >> w_f, "Phone", self.subject_phonenumber
            print >> w_f, "Age", self.subject_age
            print >> w_f, "Gender", self.subject_gender
            print >> w_f, "Glasses", self.subject_glasses
            w_f.close()
            # dlg.Destroy()
        else:
            exit()

############################################################################
# run following codes if this file is executed directly
############################################################################

if __name__ == "__main__":
    import sys
    subj = Subject()
    screen = psychopy.monitors.Monitor(name='tobii-x3-120', width=51, distance=60)
    screen.setSizePix([1920, 1080])
    ## http://www.psychopy.org/api/monitors.html
    screen.setWidth(51)
    screen.setDistance(60)
    win = psychopy.visual.Window(size=(1920, 1080), units='pix', monitor=screen,
                                 allowGUI=False, color=1.0)
    win.mouseVisible=True
    # count_down(win, 60, rest_message)
    # exit()
    # controller = TobiiController(win, subj.path)
    controller = TobiiController(win, "temp") ## NEED TO FIND ANOTHER SOLUTION.
    
    # check eye trackers and open the first one
    controller.activate()
    
    ##Add to database

    # help the subject find the eyes
    win.mouseVisible=False
    controller.findEyes()


    while True:
        ret = controller.doCalibration(
            [(0.1, 0.1), (0.9, 0.1), (0.5, 0.5), (0.1, 0.9), (0.9, 0.9), (0.9, 0.5), (0.5, 0.9), (0.5, 0.1), (0.1, 0.5)])
        if ret == 'accept':
            break
        elif ret == 'abort':
            controller.destroy()
            raise KeyboardInterrupt("The calibration was aborted.")
    
    
    ##DEMO selection area
    # controller.tracking_demo()
    # controller.fixpoint_demo()
    # controller.image_demo([controller.logoPath, "report/promoImage.jpg", "report/lake.jpg", "nus/color8.jpg", "nus/color58.jpg", "nus/color234.jpg", "nus/color529.jpg", "nus/color568.jpg"], visual=True)
    # controller.video_demo(["test_videos/testMovie.mp4", "test_videos/5.avi", "test_videos/6.avi"])
    # controller.mpv_demo(["test_videos/testMovie.mp4", "test_videos/5.avi", "test_videos/6.avi"])
    # controller.vlc_demo(["test_videos/testMovie.mp4", "test_videos/5.avi", "test_videos/6.avi"])
    # controller.mplayer_demo()
    # controller.clock_demo()
    controller.mplayer_seperatevo_demo()
    
    controller.destroy()
    win.close()
    # controller.closeDataFile()
