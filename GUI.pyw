from Tkinter import *
import tkFont
from functools import partial
import tkFileDialog as fd
import csv
from subprocess import Popen, CREATE_NEW_CONSOLE
import os
import h5py
from os.path import basename
from glob import glob
import re
import ttk

######################
#   h5 decode        #
######################
# Defines a function to sort strings in natural order. This allows the keys to be read in human/natural order.
def sortkey_natural(text):
	return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text)]	


#h5 developed previously	
def oldScript():
    global app, outfile
    outfile = []
    files_list = glob(os.path.join(input_dir, '*.h5'))
    files_list_sorted = sorted(files_list)
    # sort the list and pull out the first and last items in the list
    # rename the items
    # edit here if name of file is different
    first_file = files_list_sorted[0]
    last_file = files_list_sorted[-1]
    firstfiledate = os.path.basename(first_file)[10:-50:1]
    lastfiledate = os.path.basename(last_file)[10:-50:1]

    # create output file for raw packets
    # comment next line out to NOT create output file!
    # edit here for different directory
    outputfile = {}
    ofile = {}
    for file in files_list_sorted:
        f = h5py.File(file, 'r')
        RawAPs = f["All_Data"].keys()
        for RawAP in RawAPs:
            outputfilename = RawAP +"_"+ firstfiledate +"_"+ lastfiledate
            
            outputfile[RawAP] = "output/"+basename(outputfilename)+".pkt"
            if RawAP in ofile:
                pass
            else:
                ofile[RawAP] = open(outputfile[RawAP], 'wb')
                outfile.append(outputfile[RawAP])
    
    fullSize = len(files_list)
    mpb = ttk.Progressbar(app,orient ="horizontal",length = 400, mode ="determinate")
    mpb.pack(side=TOP, expand=YES)
    mpb["maximum"] = fullSize
    
    # loop through all files
    for file in files_list_sorted:
        mpb["value"] += 1
        root.update()
        f = h5py.File(file, 'r')

        RawAPs = f["All_Data"].keys()
        for RawAP in RawAPs:
            datasets = f["All_Data/"+RawAP].keys()
            dsets = sorted(datasets, key=sortkey_natural)
            for dataset in dsets:
                RawAP_node = f['/All_Data/'+RawAP+'/'+dataset]
                RawAP_0=RawAP_node.value
                # determine location of application packets
                apStorageOffset=RawAP_0[48:52] # location from RDR Static Header table in CDFCB Vol 2
                apStorageOffset = int(apStorageOffset[3]) + (int(apStorageOffset[2])*(2**8)) + (int(apStorageOffset[1])*(2**16)) + (int(apStorageOffset[0])*(2**24))
                inputFileValues=RawAP_0[apStorageOffset:len(RawAP_0)]
                ofile[RawAP].write(inputFileValues)
    # close the input file(s)
    f.close()
    for RawAP in RawAPs:
        ofile[RawAP].close()
######################END h5 DECODE###################################

#Switch statement for instrument selection
def switch(argument):
    switcher = {
        0: "ATMS",
        1: "OMPS",
        2: "VIIRS",
        3: "CERES",
        4: "CRIS",
        5: "SC"
    }
    return switcher.get(argument, "nothing")

#Get relevant APIDs based on user selected instrument
def relevantAPIDs(ins_string):
    if ins_string == "SC":
        return range(0,139)
    elif ins_string == "ATMS":
        return range(450,543)
    elif ins_string == "OMPS":
        return range(544,649)
    elif ins_string == "VIIRS":
        return range(650,899)
    elif ins_string == "CERES":
        return range(140,199)
    elif ins_string == "CRIS":
        return range(1200,1449)
    else:
        print("Error")

#Call C++ with selected files
def launchCXX(Lb1, allAPIDs, packetSelect):
    global root
    packetSelect.withdraw()
    sel_packetsI = Lb1.curselection()
    all_packets = Lb1.get(0,END)
    root.destroy()
    sel_packets = []
    for i in sel_packetsI:
        sel_packets.append(all_packets[i])
    for file in sel_packets:
        instrument = file.split('-')[0]
        Popen(['C:/JPSS/CXXDecom/bin/x64/Decom.exe', instrument, "output/"+file, 'databases/CXXParams.csv', allAPIDs], creationflags=CREATE_NEW_CONSOLE)
    sys.exit()

#Prepare to launch C++ to do the de-com     
def callCXX (sel_apids, allAPIDs):  
    global outfile, root
    with open("databases/CXXParams.csv",'wb') as resultFile: #Write selected APIDs to file
        wr = csv.writer(resultFile, dialect='excel')
        wr.writerow(sel_apids)
        
    helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
    helv14 = tkFont.Font(family='Helvetica', size=14)

    packetSelect = Toplevel(root)
    packetSelect.state('zoomed')
    packetSelect.wm_title("Packet Select")
    Label(packetSelect, text="Packet Select", font=helv14).pack() 
    Lb1 = Listbox(packetSelect, selectmode='multiple', font=helv14) 
    for i,packet in enumerate(outfile): #Create packet selector box
        Lb1.insert(i,packet.split('/')[1])
    Button(packetSelect, text = "Execute", command = partial(launchCXX, Lb1, allAPIDs, packetSelect), fg = 'red', font=helv20).pack(side="top", fill=X, expand=NO) 
    Lb1.pack(side="bottom", fill="both", expand=True)

#Run h5 script
#Create menu for selecting APIds
def run (root, instrument):
    if not os.path.exists("databases"): #Make output folders
        os.makedirs("databases")
    if not os.path.exists("output"):
        os.makedirs("output")
    oldScript()
    root.withdraw()
    ins_string = switch(instrument.get())
    apids = relevantAPIDs(ins_string)
    
    helv24 = tkFont.Font(family='Helvetica', size=24, weight='bold')
    helv14 = tkFont.Font(family='Helvetica', size=14)
    apidwindow = Toplevel(root)  
    apidwindow.state('zoomed')
    apidwindow.wm_title("APID Select")
    Label(apidwindow, text="Desired APIDs").pack() 
    apidframe=Frame(apidwindow)
    apidframe.pack(side=BOTTOM, fill=BOTH, expand=YES)
    scrollbar = Scrollbar(apidframe) 
    scrollbar.pack(side=RIGHT, fill=Y)
    Lb1 = Listbox(apidframe, yscrollcommand=scrollbar.set, selectmode='multiple', font=helv14) 
    Lb1.pack(fill=BOTH, expand=YES)
    scrollbar.config(command=Lb1.yview)
    
    for i,apid in enumerate(apids):
        Lb1.insert(i, apid)
    
    apidVar = IntVar()
    Checkbutton(apidwindow, text="All APIDs?", variable=apidVar, font=helv24).pack(side=TOP, fill=BOTH)
    Button(apidwindow, text = "Execute", command = partial(run2, Lb1, apidwindow, apidVar), fg = 'red', font=helv24).pack(fill=BOTH) 

 

#Get user selected APIDs and get ready to call C++   
def run2 (Lb1, apidwindow, apidVar):
    apidwindow.withdraw()
    sel_apids = Lb1.curselection()
    allAPIDs = str(apidVar.get())
    callCXX(sel_apids, allAPIDs)

#Prompt user for h5 folder location
def getdirname():
    global input_dir
    input_dir = str(fd.askdirectory(initialdir='C:/JPSS/data'))


#########################
#Main Section
#Handles GUI Creation
#########################
input_dir = 'data'
root = Tk()
root.title('De-Com Tool')
root.state('zoomed')
app = Frame(root)
root.minsize(width=300, height=666)
helv24 = tkFont.Font(family='Helvetica', size=24, weight='bold')
helv18 = tkFont.Font(family='Helvetica', size=18, weight='bold')
helv16 = tkFont.Font(family='Helvetica', size=16, weight='bold')

Button(app, text = 'Select h5 Folder', command = getdirname, font=helv24).pack(side=TOP, expand=YES, fill=BOTH)

instrument = IntVar()
Label(app, text="Instrument:", font=helv18).pack(side=TOP, expand=YES)
Radiobutton(app, text="ATMS", variable=instrument, value = 0, font=helv16).pack(side=TOP, expand=YES)
Radiobutton(app, text="OMPS", variable=instrument, value = 1, font=helv16).pack(side=TOP, expand=YES)
Radiobutton(app, text="VIIRS", variable=instrument, value = 2, font=helv16).pack(side=TOP, expand=YES)
Radiobutton(app, text="CERES", variable=instrument, value = 3, font=helv16).pack(side=TOP, expand=YES)
Radiobutton(app, text="CRIS", variable=instrument, value = 4, font=helv16).pack(side=TOP, expand=YES)
Radiobutton(app, text="SC", variable=instrument, value = 5, font=helv16).pack(side=TOP, expand=YES)


Button(app, text = "Execute", command = partial(run, root, instrument), fg = 'red', font=helv24).pack(side=TOP, expand=YES, fill=BOTH)
app.pack(fill=BOTH, expand=YES)
root.mainloop()



