"""
this is the full film module(procedural), which goal is to 
compare human made transcripts divided into clips
to mvi(microsoft video indexer) transcript made automatically
Uses lineComp module for comparisson between lines
"""

###for faster run time in return for not applying vectorial calculations change call t

import lineComp
import webvtt
import os
import re
import pysrt
import sys


def removePunct(text):
    """
    recieves string, returns the same string, lowercase, no punctuations
    """
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return " ".join(text.replace('\n', ' ').split()).lower()

def stringTS_to_int(time_stamp):#covert string timestamp to integer represanting seconds
    """
    recieves the following format string (hh:mm:ss,ts,hs,ms) - standart str timestamp
    returns the time as seconds(int)
    """
    t = int(time_stamp[0:2])*3600 + int(time_stamp[3:5])*60 + int(time_stamp[6:8])+float("0."+time_stamp[9:12])
    return (t)

def produceManualTsFromClips(s_dir, shots_path , time_stamps_path):
    """
    recieves 3 paths - dir where clips transcript is, path to .scenes.gt file, and path to .videvents file
    returns a dictionary where key=timestamp(int in seconds),
    value=list of tuples where each tuple is (line, scene number) - line said at timestamp
    """
    shots = open(shots_path, 'r').readlines()
    time_stamps = open(time_stamps_path, 'r').readlines()
    i=1
    ts_manual={}
    for file in os.listdir(s_dir): #(os.getcwd() + "\\" + film_num):
        if file.endswith(".webvtt"):
            if(i==1):
                i+=1
                continue
            add_to_timestamp = float(time_stamps[int(shots[i-1].split()[0])-1].split()[1])
            i+=1
            for caption in webvtt.read(s_dir + '\\' +file):#(os.getcwd() + '\\' + film_num + '\\'+file):
                caption_time = stringTS_to_int(caption.start) + add_to_timestamp
                withoutPunct = removePunct(caption.text);
                if int(caption_time) not in ts_manual:
                    ts_manual[int(caption_time)]=[]
                ts_manual[int(caption_time)].append((withoutPunct ,i)) #{time: [(line, scene number),(line, scene number)]}
    return ts_manual

def produceMviTsFromStr(path):
    """
    recieves a path to srt file(produced by mvi)
    returns a a dictionary where key=timestamp(int in seconds),
    value=list of strings where each string is a line said at timestamp
    """
    ts_mvi={}
    video_indexer_product = pysrt.open(path)
    for sub in video_indexer_product:
        withoutPunct=removePunct(sub.text)
        caption_time=stringTS_to_int(str(sub.start))
        if int(caption_time)not in ts_mvi:
            ts_mvi[int(caption_time)]=[]
        ts_mvi[int(caption_time)].append(withoutPunct)
    return ts_mvi

def extendRelevantTime(line, list_of_relevant):
    """
    recieves a line and a list of lines said at the same time
    adds to the list of lines, combos of lines that start and end with the first word
    and ends with the last word of the input line
    
    #this func is supposed to rearrange certain sentances in list_of_relevant
    #to fit more accuratly to line
    
    deal with a problem like : line="me and my sister", list=["me and","my sister"]
    list will become ["me and","my sister", "me and my sister"]
    """
    
    splt = line.split()
    #right = "" - not used in new version of code
    list_ofrev_splt=[list_of_relevant[i].split() for i in range (0,len(list_of_relevant))]
    first = splt[0]
    last = splt[len(splt)-1]
    pre_last = splt[len(splt)-2]
    try:
        second = splt[1]
    except:
        second = None
    listrightadding=[]
    listrightdone=[]
    for i in range(0, len(list_ofrev_splt)):
        lin = list_ofrev_splt[i]
        for j in range(0, len(lin)):
            word = lin[j]
            if word==first or word==second:
                listrightadding.append("")
            if word!=last:
                for k in range(0, len(listrightadding)):
                    listrightadding[k] = (listrightadding[k]+ " " + word).strip()
            if word==last:
                for k in listrightadding:
                    listrightdone.append((k+" "+word).strip())
            if word==pre_last:
                for k in listrightadding:
                    try:
                        listrightdone.append((k +" " + lin[j+1]).strip())
                    except:##out of range
                        listrightdone.append(k)
    list_of_relevant.extend(listrightdone)
    list_of_relevant.extend(listrightadding)
    
    """
    the previous version of code here:
        
    found_first = False
    for i in range(0,len(list_ofrev_splt)):
        lin = list_ofrev_splt[i]
        for j in range(0, len(lin)):
            word = lin[j]
            if word==first:
                found_first=True
            if(found_first):
                if word!=last: right+=word+" "
                if word==pre_last:
                    list_of_relevant.append(right)
                if word==last:
                    right+=word
                    found_first=False
                    list_of_relevant.append(right)
                    right=""                                
    #list_of_relevant.append(right) #of some reason adding this decreases hit ratio
    
    """


def calculateResults(film_num, ts_manual, ts_mvi, calculate_euq, calculate_cos):
    """
    recieves dictionary(timestamp:[(line,scene),..]), dictionary(timestamp:[line,..])
             boolean calculate euqlidian distances (takes a lot of time if true)
             boolean calculate cosine similarity (takes a lot of time if true)
    creates file in dir with most similar equivilant for each line said in manual transcript
             in mvi transcript, vice versa, and a file of statistic results
    """
    
    f = open("totalResults\\similaritiesByManual\\SimilaritiesFileByManual_"+film_num+".txt", "w")
    g = open("totalResults\\similaritiesByMvi\\SimilaritiesFileByVideoIndexer_"+film_num+".txt", "w")
    fR = open("totalResults\\numericResults\\ResultsFile_"+film_num+".txt", "w")
    relevant_time=[] ; false_negatives=[] ; best_fits=[] ; true_positives=[] ; false_positives=[]

    comp = lineComp.CompTwoLines("","")
    overall=0 ; sumeuq=0 ; sumcos=0 
    scene_missfit_dic = {}
    for time_man in ts_manual.keys():
        if (time_man not in ts_mvi.keys()) \
        and ((time_man+1) not in ts_mvi.keys()) and ((time_man+2) not in ts_mvi.keys())\
        and((time_man-1) not in ts_mvi.keys()) and ((time_man-2) not in ts_mvi.keys()) \
        and ((time_man-3) not in ts_mvi.keys()) and ((time_man+3) not in ts_mvi.keys()) \
        and ((time_man-4) not in ts_mvi.keys()) and((time_man+4) not in ts_mvi.keys())\
        and ((time_man-5) not in ts_mvi.keys()) and ((time_man+5) not in ts_mvi.keys()):
        #in this discrete time(+-5 seconds) nothing was said according to the videoindexer
            false_negatives.append((time_man, ts_manual[time_man]))
            continue
        relevant_time=[]
        if(time_man-5 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man-5])
        if(time_man-4 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man-4])
        if(time_man-3 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man-3])
        if(time_man-2 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man-2])
        if(time_man-1 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man-1])
        if(time_man in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man])
        if(time_man+1 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man+1])
        if(time_man+2 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man+2])#list of things said in the scope of the five seconds
        if(time_man+3 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man+3])
        if(time_man+4 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man+4])
        if(time_man+5 in ts_mvi.keys()): relevant_time.extend(ts_mvi[time_man+5])
        bestfitnum=1000 ; bestfit="" ; euq=0 ; cos=0
        for l2tup in ts_manual[time_man]:
            l2 = l2tup[0]
            extendRelevantTime(l2,relevant_time)
            for l1 in relevant_time:
                comp.setLines(l1,l2)
                if comp.countEditingChangesNeeded() < bestfitnum:
                    bestfit=l1
                    bestfitnum = comp.countEditingChangesNeeded()
                    if(calculate_euq): euq = comp.getEuqlidianDiff()
                    if(calculate_cos): cos = comp.getCosineDiff()
                    if bestfit==0:
                        continue
            #finding the most fitting line by grammer changes
            best_fits.append((l2, bestfit, bestfitnum, euq, cos))#dont know if ill need it but better be saved
            f.write("manual:       '"+l2+"' \n") ; f.write("videoindexer: '"+bestfit+"' \n")
            f.write(str(bestfitnum)+" grammer changes needed \n")
            if(calculate_euq): f.write("euqlidian: "+str(euq)+"\n")
            if(calculate_cos): f.write("cosine: "+str(cos)+"\n")
            if(calculate_euq and (euq<14 or bestfitnum<(len(l1)/2) or bestfitnum<(len(l2)/2) or comp.calculateBLEU()>0.45)):#if euq checked determine by euq 
                true_positives.append((l2,bestfit))
                f.write("good match \n")
            elif(not calculate_euq and (bestfitnum<(len(l1)/2) or bestfitnum<(len(l2)/2) or comp.calculateBLEU()>0.45)):#determine by grammer
                true_positives.append((l2,bestfit))
                f.write("good match \n")
            else: 
                f.write("bad match \n")
                false_negatives.append((time_man, ts_manual[time_man]))
                if(int(l2tup[1]) in scene_missfit_dic.keys()):
                    scene_missfit_dic[int(l2tup[1])]+=1#mapping missfit to dictionary
                else:                                   #for plotting reasons later
                    scene_missfit_dic[int(l2tup[1])]=1
            overall+=1
            sumeuq+=euq
            sumcos+=cos
            
            b = (time_man * 100/5626)
            sys.stdout.write('\rFirst Iteration : %.2f' %b +"%")#percent showing for comfort
            
            #for every line in the manual transcription, we have the best fit for it in mvi, 
            #the amount of editing changes between them, the euqlidian, and cosine distances
    fR.write("Results: \nIterating through manual transcripts: \n")
    fR.write("There were "+str(len(false_negatives))+" lines transcripted humanly and not found by microsoft videoIndexer = false negatives\n")
    fR.write("There were "+str(len(true_positives))+" lines that were identically or almost identically transcripted = true positives\n")
    fR.write("(That is %.2f" % float(str(len(true_positives)*100/overall)) + "%) - of all manual lines found \n")
    fR.write("----was checked according to grammer changes needed, BLEU meassurement")
    if(calculate_euq): fR.write(" and vectorial comparisons")
    fR.write("---- \n")
    if(calculate_euq): fR.write("The avarage euqlidian differance is "+str(sumeuq/overall) +"\n")
    if(calculate_cos): fR.write("The avarage cosine similarity is "+str(sumcos/overall) +"\n")

    
    for k in range(0,max(scene_missfit_dic.keys())):
        if k not in scene_missfit_dic.keys():
            scene_missfit_dic[k]=0
    
    import matplotlib.pyplot as plt
    plt.bar(*zip(*scene_missfit_dic.items()))
    plt.savefig(os.getcwd() +"\\totalResults\\plotByScene\\plot"+film_num+".png")
    
    ###########################################################################
                               #second iteration# - this is meant to go over the mvi product and 
                               #find false positives, something i was unable to do
                               #during the first iteration
    ########################################################################### 
                          
    comp = lineComp.CompTwoLines("","")
    for time_man in ts_mvi.keys():
        if (time_man not in ts_manual.keys()) and ((time_man+1) not in ts_manual.keys()) and ((time_man+2) not in ts_manual.keys())and ((time_man-1) not in ts_manual.keys()) and ((time_man-2) not in ts_manual.keys()) and ((time_man-3) not in ts_manual.keys()) and ((time_man+3) not in ts_manual.keys()):
        #in this discrete time(+-3 seconds) nothing was said according to the manual
            false_positives.append((time_man, ts_mvi[time_man]))
            continue
        relevant_time=[]
        if(time_man-5 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man-5]])
        if(time_man-4 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man-4]])
        if(time_man-3 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man-3]])
        if(time_man-2 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man-2]])
        if(time_man-1 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man-1]])
        if(time_man in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man]])
        if(time_man+1 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man+1]])
        if(time_man+2 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man+2]])#list of things said in the scope of the five seconds
        if(time_man+3 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man+3]])
        if(time_man+4 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man+4]])
        if(time_man+5 in ts_manual.keys()): relevant_time.extend([i[0] for i in ts_manual[time_man+5]])
        
        bestfitnum=1000 ; bestfit="" ; euq=0 ; cos=0
        for l2 in ts_mvi[time_man]:
            extendRelevantTime(l2,relevant_time)
            for l1 in relevant_time:
                comp.setLines(l1,l2)
                if comp.countEditingChangesNeeded() < bestfitnum:
                    bestfit=l1
                    bestfitnum = comp.countEditingChangesNeeded()
                    if(calculate_euq): euq = comp.getEuqlidianDiff()
                    if(calculate_cos): cos = comp.getCosineDiff()
                    if bestfit==0:
                        continue
            
            g.write("videoindexer: '"+l2+"' \n") ; g.write("manual:       '"+bestfit+"' \n")
            g.write(str(bestfitnum)+" grammer changes needed \n")
            if(calculate_euq): f.write("euqlidian: "+str(euq)+"\n")
            if(calculate_cos): f.write("cosine: "+str(cos)+"\n")
            if(calculate_euq and (euq<14 or bestfitnum<(len(l1)/2) or bestfitnum<(len(l2)/2) or comp.calculateBLEU()>0.45)):#if euq checked determine by euq  
                pass
            elif(not calculate_euq and (bestfitnum<(len(l1)/2) or bestfitnum<(len(l2)/2) or comp.calculateBLEU()>0.45)):#determine by grammer
                pass
            else: 
                false_positives.append((time_man, ts_mvi[time_man]))
            
            b = (time_man * 100/5626)
            sys.stdout.write('\rSecond Iteration : %.2f' %b +"%")##percent showing for comfort
            overall+=1
            
    ################################################################
    #Now we have true positives, false negatives and false positives!
    ################################################################    
    
    precision = len(true_positives) / (len(true_positives) + len(false_positives))
    recall = len(true_positives) / (len(true_positives) + len(false_negatives))
    F1 = (2 * precision * recall) / (precision + recall)
    jaccard = len(true_positives) / (overall - len(true_positives)) #each TP is counted twice
    
    fR.write("Iteration through mvi transcript there were "+str(len(false_positives))+" lines not found manually = false positives \n")
    fR.write("\n")
    fR.write("Precision = " +str(precision) +"\n")
    fR.write("Recall = " +str(recall) +"\n")
    fR.write("F1 measure = " +str(F1) +"\n")
    fR.write("Jaccard measure = " +str(jaccard) +"\n")

    f.close()
    g.close()
    fR.close()
    return((precision,recall,F1,jaccard))

def CompareFilm(film_num,mvi_srtName, euq_run, cos_run):
    ts_manual = produceManualTsFromClips(os.getcwd() + "\\clip_srt\\" + film_num, os.getcwd()+'\\mg_videoinfo\\scene_boundaries\\'+film_num+'.scenes.gt', os.getcwd()+'\\mg_videoinfo\\video_boundaries\\'+film_num+'.videvents')
    ts_mvi = produceMviTsFromStr(os.getcwd() + "\\mvi_srt\\" + mvi_srtName)
    calculateResults(film_num, ts_manual, ts_mvi, euq_run, cos_run) ####change to false, false for faster run time
    
    
