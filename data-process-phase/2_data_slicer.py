import sys
import cPickle
import common

gazeDict_name = "gazeDict_all.pkl"
# gazeDict_name = "gazeDict_subset.pkl"
linesDict_name = "linesDict_all.pkl"
# linesDict_name = "linesDict_subset.pkl"
r_f = open(gazeDict_name, "rb")
gazeDict = cPickle.load(r_f)
r_f.close()
r_f = open(linesDict_name, "rb")
linesDict = cPickle.load(r_f)
r_f.close()
# exit()

slice_gazeDict = {}
for voname in gazeDict:
    slice_gazeDict[voname]={}

## Slice data segment for certain video
for voname in gazeDict:
    print "Handling", voname, "..."
    # slice_gazeDict[voname] = {}
    testerDict = gazeDict[voname]
    for tester_idx in testerDict:
        print "\tHandling", tester_idx, 
        # print tester_idx;exit()
        gd = testerDict[tester_idx]
        # print gd;exit() ##record a tester's start_stamp & stop_stamp for voname
        
        data = []
        start_stamp = gd["start_stamp"]
        stop_stamp = gd["stop_stamp"]
        lines = linesDict[tester_idx]
        # print lines[0];exit()
        for i in range(len(lines)):
            # print lines[i];exit()
            line_list = lines[i].split(', ')
            # print line_list;exit()
            timestamp = int(line_list[0])
            if timestamp < start_stamp:
                continue

            if line_list[6] == '1' and line_list[7] == '1':
                data.append((line_list[0], (float(line_list[-4])+float(line_list[-2]))/2, (float(line_list[-3])+float(line_list[-1]))/2) )
            if not timestamp > stop_stamp:
                continue
            break
            
            # start_index = i
            '''
            for i in range(start_index+1, len(lines)):
                line_list = lines[i].split(', ')
                timestamp = int(line_list[0])
                if timestamp < stop_stamp:
                    if line_list[6] == '1' and line_list[7] == '1':
                        data.append((line_list[0], (float(line_list[-4])+float(line_list[-2]))/2, (float(line_list[-3])+float(line_list[-1]))/2) )
                    if i == (len(lines) - 1):
                        break
                    # continue
                # stop_index = i
                # break
            '''
        print "Done!"
        print "\t", len(data), sys.getsizeof(slice_gazeDict),
        slice_gazeDict[voname][tester_idx] = data
        # print slice_gazeDict[voname][tester_idx]
    print "Done!"

    
print "All Done! Saving dictionary..."
print sys.getsizeof(slice_gazeDict)
w_f = open("slice_gazeDict.pkl", "wb")
cPickle.dump(slice_gazeDict, w_f)
w_f.close()
'''
for key in gazeDict:
    # print key
    # gazeDict[key]
    data = []

    start_stamp = gazeDict[key]["start_stamp"]
    stop_stamp = gazeDict[key]["stop_stamp"]
    for i in range(2, event_idx):
        line_list = lines[i].split(', ')
        timestamp = int(line_list[0])
        if timestamp < start_stamp:
            continue
        # data.append(lines[i])
        if line_list[6] == '1' and line_list[7] == '1':
            data.append((line_list[0], (float(line_list[-4])+float(line_list[-2]))/2, (float(line_list[-3])+float(line_list[-1]))/2) )
        start_index = i
        break
    for i in range(start_index, event_idx):
        line_list = lines[i].split(', ')
        timestamp = int(line_list[0])
        if timestamp < stop_stamp:
            # data.append(lines[i])
            if line_list[6] == '1' and line_list[7] == '1':
                data.append((line_list[0], (float(line_list[-4])+float(line_list[-2]))/2, (float(line_list[-3])+float(line_list[-1]))/2) )
            if i == (event_idx - 1):
                stop_index = i
                break
            continue
        stop_index = i
        break

    gazeDict[key]["start_stamp"] = data[0][0]
    gazeDict[key]["stop_stamp"] = data[-1][0]
    gazeDict[key]["data"] = data
'''
########################## Gaze data generated #####################################
''' 
w_f = open("slice_gazeDict.pkl", "w")
cPickle.dump(gazeDict, w_f)
w_f.close()
## print gazeDict

for key in gazeDict:
    print key
    for info in gazeDict[key]:
        print info, ":",
        print gazeDict[key][info]
    print 
exit()
'''


### Drop invalid data
'''
for key in gazeDict:
    for data in gazeDict[key]["data"]:
        dat_list = data.split(', ')
        if dat_list[6] == '1' and dat_list[7] == '1':
            print dat_list[0], (float(dat_list[-4])+float(dat_list[-2]))/2, (float(dat_list[-3])+float(dat_list[-1]))/2
    print key;exit()
    # for data in gazeDict[key]["data"]:
        # print data
'''
