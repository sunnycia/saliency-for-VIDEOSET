###
#   Function:
#       1.read sequences in the DIR.
#       2.Filter data.(Only reserve test video data)
#       3.Filter data 2. (Drop invalid data)
#       4.Modify time stamp.()
#       
#       Resolution should be add to database
###
import cPickle
import os

dataDir = "testResult"
# dataDir = "testResult_subset"
gazeinfoFlag = "Eye gaze information."
eventinfoFlag = "Event information."
dummyVON = "3sblack.avi"
startFlag = "start playing."
stopFlag = "stop playing."

## voname, start_stamp, end_stamp, # start_index, end_index
infoPkl = "videoinfo.pkl"
infoDict = cPickle.load(open(infoPkl, "rb"))
gazeDict = {}
linesDict = {}
for key in infoDict:
    voname = key
    # print video_idx;
    gazeDict[voname] = {}
    
# print infoDict;exit()
tester_dir_list = os.listdir(dataDir)
for tester_dir in tester_dir_list:
    print "Parsing", tester_dir, "...",
    tester_idx = tester_dir.split("_")[0]
    # print tester_idx
    # continue
    tester_path = os.path.join(dataDir, tester_dir)
    four_lines = []
    for i in range(4):
        data_filename = "sequence"+str(i+1)+".csv"
        data_filepath = os.path.join(tester_path, data_filename)
        
        r_f = open(data_filepath)
        lines = r_f.readlines()
        total_len = len(lines)
        for i in range(total_len):
            lines[i] = lines[i].strip()
        
        ##extrack event
        event_idx = lines.index(eventinfoFlag)
        for i in range(1, event_idx):
            four_lines.append(lines[i])
        # four_lines.append(lines[1:event_idx])
        for i in range(event_idx+1, total_len):
            line = lines[i]
            cur_dict = {}
            
            if dummyVON in line:
                continue
            if stopFlag in line:
                continue

            VOPath = line[line.index("('")+2:line.index("', '")]
            voname = VOPath.split('/')[-1]
            
            if startFlag in line:
                cur_dict["start_stamp"] = int(line.split(',')[0])
                i += 1
                line = lines[i]
                cur_dict["stop_stamp"] = int(line.split(',')[0])
                cur_dict["duration"] = cur_dict["stop_stamp"] - cur_dict["start_stamp"]
            if tester_idx not in gazeDict[voname]:
                gazeDict[voname][tester_idx] = cur_dict
            else:
                gazeDict[voname][tester_idx] = dict(gazeDict[voname][tester_idx], **cur_dict)
    linesDict[tester_idx] = four_lines
    print "Done!"

w_f = open("gazeDict.pkl", "wb")
cPickle.dump(gazeDict, w_f)
w_f.close()
# exit()

w_f = open("linesDict.pkl", "wb")
cPickle.dump(linesDict, w_f)
w_f.close()
exit()