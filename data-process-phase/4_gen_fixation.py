import cv2
import cPickle
import os
import numpy as np
from scipy.spatial import distance


videoDir = "I:\JND VideoSet\qp_00"
gazedatPath = "gazeDict_all.pkl"
slice_gazedatPath = "slice_gazeDict-all.pkl"
voinfoPath = "videoinfo.pkl"
linesDictPath = "linesDict_all.pkl"

gazeDict = cPickle.load(open(gazedatPath, "rb"))
slice_gazedatDict = cPickle.load(open(slice_gazedatPath, "rb"))
voinfoDict = cPickle.load(open(voinfoPath, "rb"))
# linesDict = cPickle.load(open(linesDictPath, "rb"))
fixationDir = "fixation"
if not os.path.isdir(fixationDir):
    os.mkdir(fixationDir)
frameDir = "frame"
if not os.path.isdir(frameDir):
    os.mkdir(frameDir)
    
# for key in gazeDict:
    # # print key
    # for key2 in gazeDict[key]:
        # # print key2
        # for key3 in gazeDict[key][key2]:
            # print key3

def EUC(point1, point2):
    return distance.euclidean(point1, point2)

def cluster_points(point_list, threshold):
    print len(point_list)
    compared_list = []
    ready_list = []
    cluster_list = []
    for i in range(len(point_list)):
        cluster = [point_list[i]]
        if i in ready_list:
            continue
        ready_list.append(i)
        for j in range(len(point_list)):
            if i==j:
                continue
            if i < j:
                curr_cmp = (i, j)
            else:
                curr_cmp = (j, i)
            if curr_cmp in compared_list:
                continue
            compared_list.append(curr_cmp)
            
            dist = EUC(point_list[i], point_list[j])
            if dist < threshold:
                cluster.append(point_list[j])
                ready_list.append(j)
                
        cluster_list.append(cluster)
    
    # print compared_list
    # for cluster in cluster_list:
        # print len(cluster)
        # print cluster
    
    
    print len(cluster_list)
    final_list = []
    for cluster in cluster_list:
        min_idx = 0
        min_dist = len(cluster)*threshold + 1
        for i in range(len(cluster)):
            sum = 0
            for j in range(len(cluster)):
                if i==j:
                    continue
                sum += EUC(cluster[i], cluster[j])
            print sum
            if sum < min_dist:
                min_idx = i
                min_dist = sum
        print min_idx, min_dist;#exit()
        final_list.append(cluster[min_idx])
    # print final_list, len(final_list)
    ''' '''
    # exit()
    return final_list
    
# exit()
for voname in slice_gazedatDict:
    vo_idx =  voname.split("_")[0];#exit()
    fixationPath = os.path.join(fixationDir, vo_idx)
    if not os.path.isdir(fixationPath):
        os.makedirs(fixationPath)
    framePath = os.path.join(frameDir, vo_idx)
    if not os.path.isdir(framePath):
        os.makedirs(framePath)
    
    fps = voinfoDict[voname]["fps"]
    frame_count = voinfoDict[voname]["frame_count"]
    frame_duration_microsec = 1e6 * (1/fps)
    res_wid =  int(voinfoDict[voname]["frame_width"])
    res_hei =  int(voinfoDict[voname]["frame_height"])
    
    # outputname = voname.split("_")[0]+".avi"
    # outputPath = os.path.join(fixationDir, outputname)
    ori_videoPath = os.path.join(videoDir, voname)
    
    # print outputPath, exit()
    
    # out_video = cv2.VideoWriter(outputPath, 0, fps, (res_wid, res_hei))
    ori_video = cv2.VideoCapture(ori_videoPath)
    
    for i in range(1, int(frame_count)+1):
        imagename = "frame"+str(i)+".bmp"
        fiximagePath = os.path.join(fixationPath, imagename)
        frameimagePath = os.path.join(framePath, imagename)
        
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
                point_list.append((x, y))
                # print "app", 
                if timestamp > endstamp_of_cur_frame:
                    # print point[0], endstamp_of_cur_frame, "break"
                    # print type(point[0]), type(endstamp_of_cur_frame), "break"
                    break
            # exit()
            
        point_list = cluster_points(point_list, 45)
        
        # print point_list
        # point np.max(point_list[0])
        blank_image = np.zeros((res_hei, res_wid), np.uint8)
        for point in point_list:
            # cv2.circle(blank_image, point, 1, 255, 1)
            pnt = point
            cv2.line(blank_image, point,point, 255, 1)
            # print blank_image.shape;exit()
            # blank_image(point[0], point[1]] = 255
        
        cv2.imwrite(fiximagePath, blank_image)
        cv2.imwrite(frameimagePath, frame)
        # exit()
        # out_video.write(frame)
        
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