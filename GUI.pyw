from Tkinter import *
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


def bin_to_dec(data):
    data_bin = []
    for x in range(len(data)):
        data_bin.append(dec_to_bin(data[x]).zfill(8))

    bin_value = data_bin[0] + data_bin[1]

    return int(bin_value, 2)
 

# Converts a positive integer value to binary
# input:      n              positive base-10 integer to convert to binary
#
# output                     corresponding binary string value
def dec_to_bin(n):
    return format(n, 'b')


# Extracts primary header parameters
# input:      pheadData      six element byte array containing primary CCSDS packet header values
#
# output                     list containing primary header elements and corresponding integer values
def phead(pheadData):
    return bin_to_dec(pheadData[4:6]) + 7


# Defines a function to sort strings in natural order. This allows the keys to be read in human/natural order.
def sortkey_natural(text):
	return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text)]	


#h5 developed previously	
def oldScript():
    global root, outfile
    outfile = []
    files_list = glob(os.path.join(input_dir, '*.h5'))
    files_list_sorted = sorted(files_list)
    # sort the list and pull out the first and last items in the list
    # rename the items
    # edit here if name of file is different
    first_file = files_list_sorted.pop(0)
    last_file = files_list_sorted.pop()
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
            
            outputfile[RawAP] = "C:/JPSS/"+basename(outputfilename)+".pkt"
            if RawAP in ofile:
                pass
            else:
                ofile[RawAP] = open(outputfile[RawAP], 'wb')
                outfile.append(outputfile[RawAP])
    
    fullSize = len(files_list)
    mpb = ttk.Progressbar(root,orient ="horizontal",length = 200, mode ="determinate")
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
                offset = apStorageOffset
                inputFileValues=RawAP_0[apStorageOffset:len(RawAP_0)]
                
                # set file offset for packet area to zero    
                offset = 0                
                # loop through application packets
                while offset < len(inputFileValues):                    
                    # read the primary header
                    packetlen = phead(inputFileValues[offset:offset+7])
                    # write packet to output file, comment out for no output file!
                    ofile[RawAP].write(inputFileValues[offset:offset+packetlen])
                    # set file offset to the next packet location   
                    offset = offset + packetlen
		
    # close the input file(s)
    f.close()
    for RawAP in RawAPs:
        ofile[RawAP].close()

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
     
#Launch C++ to do the de-com     
def callCXX (sel_apids, database, ins_string):  
    global outfile
    with open("C:\JPSS\CXXParams.csv",'wb') as resultFile:
        wr = csv.writer(resultFile, dialect='excel')
        wr.writerow(sel_apids)
    for file in outfile:
        Popen(['C:/JPSS/CXXDecom/bin/x64/Decom.exe', database, ins_string, file, 'C:/JPSS/CXXParams.csv'], creationflags=CREATE_NEW_CONSOLE)
    sys.exit()

#Run h5 script
#Create menu for selecting APIds
def run (root, instrument): 
    global database
    oldScript()
    root.withdraw()
    ins_string = switch(instrument.get())
    apids = relevantAPIDs(ins_string)
    
    apidwindow = Toplevel(root)  
    apidwindow.minsize(width=666, height=666)
    apidwindow.wm_title("APID Select")
    Label(apidwindow, text="Desired APIDs").pack() 
    
    Lb1 = Listbox(apidwindow, selectmode='multiple') 
    for i,apid in enumerate(apids):
        Lb1.insert(i, apid)
    Lb1.pack(side="left", fill="both", expand=True)
    
    Button(apidwindow, text = "Execute", command = partial(run2, Lb1, apidwindow, root, database, ins_string), fg = 'red').pack(fill="both", expand=True) 

 

#Get user selected APIDs and get ready to call C++   
def run2 (Lb1, apidwindow, root, database, ins_string):
    sel_apids = Lb1.curselection()
    apidwindow.destroy()
    root.destroy()
    callCXX(sel_apids,database, ins_string)
    

#Prompt user for filename
def getfilename():
    global database
    database = str(fd.askopenfilename(initialdir='C:/JPSS/'))

def getdirname():
    global input_dir
    input_dir = str(fd.askdirectory(initialdir='C:/Users/ggordon5/Documents/for_interns/for Gabe/Gravite_data/'))


#########################
#Main Section
#Handles GUI Creation
#########################
database = ''
input_dir = ''
root = Tk()
root.title('De-Com Tool')
app = Frame(root)
Button(app, text = 'Select Database File', command = getfilename).pack(side=TOP, expand=YES)
Button(app, text = 'Select h5 Folder', command = getdirname).pack(side=TOP, expand=YES)


instrument = IntVar()
Label(app, text="Instrument:").pack(side=TOP, expand=YES)
Radiobutton(app, text="ATMS", variable=instrument, value = 0).pack(side=TOP, expand=YES)
Radiobutton(app, text="OMPS", variable=instrument, value = 1).pack(side=TOP, expand=YES)
Radiobutton(app, text="VIIRS", variable=instrument, value = 2).pack(side=TOP, expand=YES)
Radiobutton(app, text="CERES", variable=instrument, value = 3).pack(side=TOP, expand=YES)
Radiobutton(app, text="CRIS", variable=instrument, value = 4).pack(side=TOP, expand=YES)
Radiobutton(app, text="S/C", variable=instrument, value = 5).pack(side=TOP, expand=YES)


Button(app, text = "Execute", command = partial(run, root, instrument), fg = 'red').pack(side=TOP, expand=YES)
app.pack(fill=BOTH, expand=YES)
root.mainloop()



