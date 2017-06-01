import cv2
import cPickle
import os
import numpy as np

videoDir = "I:\JND VideoSet\qp_00"
gazedatPath = "gazeDict_all.pkl"
slice_gazedatPath = "slice_gazeDict-all.pkl"
voinfoPath = "videoinfo.pkl"
testerinfoPath = "testerinfo.pkl"
linesDictPath = "linesDict_all.pkl"
outputDir = "videoutput_gender"

gazeDict = cPickle.load(open(gazedatPath, "rb"))
slice_gazedatDict = cPickle.load(open(slice_gazedatPath, "rb"))
voinfoDict = cPickle.load(open(voinfoPath, "rb"))
testerinfoDict = cPickle.load(open(testerinfoPath, "rb"))
# linesDict = cPickle.load(open(linesDictPath, "rb"))
if not os.path.isdir(outputDir):
    os.mkdir(outputDir)

    
# for key in gazeDict:
    # # print key
    # for key2 in gazeDict[key]:
        # # print key2
        # for key3 in gazeDict[key][key2]:
            # print key3


# exit()

for voname in slice_gazedatDict:
    # print voname
    fps = voinfoDict[voname]["fps"]
    frame_count = voinfoDict[voname]["frame_count"]
    frame_duration_microsec = 1e6 * (1/fps)
    res_wid =  int(voinfoDict[voname]["frame_width"])
    res_hei =  int(voinfoDict[voname]["frame_height"])
    
    outputname = voname.split("_")[0]+".avi"
    outputPath = os.path.join(outputDir, outputname)
    ori_videoPath = os.path.join(videoDir, voname)
    
    # print outputPath, exit()
    
    out_video = cv2.VideoWriter(outputPath, 0, fps, (res_wid, res_hei))
    ori_video = cv2.VideoCapture(ori_videoPath)
    
    for i in range(1, int(frame_count)+1):
        status, frame = ori_video.read()
        if not status:
            break
        
        point_list = []
        for tester_idx in slice_gazedatDict[voname]:
            data = slice_gazedatDict[voname][tester_idx]
            startstamp = gazeDict[voname][tester_idx]["start_stamp"]
            stopstamp = gazeDict[voname][tester_idx]["stop_stamp"]
            beginstamp_of_cur_frame = startstamp + (i-1)*frame_duration_microsec
            endstamp_of_cur_frame = startstamp + i*frame_duration_microsec
            gender = testerinfoDict[tester_idx]["gender"]
            # print gender;
            # print beginstamp_of_cur_frame, endstamp_of_cur_frame
            # print beginstamp_of_cur_frame, endstamp_of_cur_frame
            for point in data:
                # print point[0]
                # print data[1][0]
                timestamp = int(point[0])
                # print 
                if timestamp < beginstamp_of_cur_frame:
                    continue
                    
                norm_x = point[1]
                norm_y = point[2]
                x = int(norm_x*res_wid)
                y = int(norm_y*res_hei)
                point_list.append((y, x, gender))
                # print "app", 
                if timestamp > endstamp_of_cur_frame:
                    # print point[0], endstamp_of_cur_frame, "break"
                    # print type(point[0]), type(endstamp_of_cur_frame), "break"
                    break
            # exit()
        # print point_list
        for point in point_list:
            if point[2] == 0:
                cv2.circle(frame, (point[1], point[0]), 3, (0, 0, 255), 3)
            else:
                cv2.circle(frame, (point[1], point[0]), 3, (255, 0, 0), 3)
            
        
        out_video.write(frame)
        
    print voname, "Done!"
exit()
'''
for tester_idx in slice_gazedatDict[voname]:  
    print "\t", tester_idx
    startstamp = gazeDict[voname][tester_idx]["startstamp"]
    stopstamp = gazeDict[voname][tester_idx]["stopstamp"]
    
    data = slice_gazedatDict[voname][tester_idx]
    
    # print len(data), data[0]
'''
        
    # exit()
    # print slice_gazedatDict[voname];#exit()
    # ori_videoPath = os.path.join(videoDir, voname)
    
    # data = slice_gazedatDict[voname]
    # for key in slice_gazedatDict[voname]:
        # print 
        # print slice_gazedatDict[voname][key]
exit()
for key in linesDict:
    print key
    for line in linesDict[key]:
        # linesDict[key]
        print line.split(', ')[0],
    exit()