from Tkinter import *
from functools import partial
import tkFileDialog as fd
import csv
import subprocess
import os
from datetime import datetime
import h5py
import numpy
from os.path import basename
from glob import glob
import re
import array
from operator import itemgetter
import ttk
# Extracts bit string from integer array and converts to decimal value
# input:      data           byte or byte array containing integer value(s) to convert
#            start_bit      start bit location
#            bit_length     bit length
#
# output:                    corresponding base-10 integer value
def bin_to_dec(data, start_bit, bit_length, two_comp='no'):
    if type(data)==type(int()) or type(data)==numpy.uint8:
        bin_value = dec_to_bin(data).zfill(8)
    else:
        data_bin = []
        for x in range(len(data)):
            data_bin.append( dec_to_bin(data[x]).zfill(8) )
        bin_value = ''
        for x in data_bin:
            bin_value = bin_value + x
    if two_comp == 'yes':
        if bin_value[start_bit:start_bit+1] == "0":
            return int( bin_value[start_bit+1:start_bit+bit_length], 2)
        else:
            return -1 * abs( int( bin_value[start_bit+1:start_bit+bit_length] ,2) - 2**(bit_length-1)  )
    else:
        return int( bin_value[start_bit:start_bit+bit_length], 2)


# Converts a positive integer value to binary
# Taken from 'http://en.literateprograms.org/Binary_numeral_conversion_(Python)'
# input:      n              positive base-10 integer to convert to binary
#
# output                     corresponding binary string value
def dec_to_bin(n):
    s = ''
    while n != 0:
        if n % 2 == 0: bit = '0'
        else: bit = '1'
        s = bit + s
        n >>= 1
    return s or '0'


# Extracts primary header parameters
# input:      pheadData      six element byte array containing primary CCSDS packet header values
#
# output                     list containing primary header elements and corresponding integer values
def phead(pheadData):
    pheader = {}
    pheader["version"] = bin_to_dec( pheadData[0],   0, 3)
    pheader["type"]    = bin_to_dec( pheadData[0],   3, 1)
    pheader["sec_hdr"] = bin_to_dec( pheadData[0],   4, 1)
    pheader["apid"]    = bin_to_dec( pheadData[0:2], 5, 11)
    pheader["seq_flg"] = bin_to_dec( pheadData[2],   0, 2)
    pheader["seq_cnt"] = bin_to_dec( pheadData[2:4], 2, 14)
    pheader["pkt_len"] = bin_to_dec( pheadData[4:6], 0, 16)
    pheader["pkt_len_with_header"] = pheader["pkt_len"] + 7
    return pheader


# Extracts secondary header parameters
# input:      sheadData      eight element byte array containing secondary CCSDS packet header values
#
# output                     list containing secondary header elements (packet timestamp) and corresponding values
def shead(sheadData):
    sheader = {}
    day = (sheadData[0] * 2.0**8.0)  + sheadData[1]
    ms  = (sheadData[2] * 2.0**24.0) + (sheadData[3] * 2.0**16.0) + (sheadData[4] * 2.0**8.0) + sheadData[5]
    us  = (sheadData[6] * 2.0**8.0)  + sheadData[7]
    sheader["unix_time"] = (day * 86400.0) + ( ms * 0.001 ) + ( us * 0.000001 ) - 378691200.0
    sheader["desc_time"] = datetime.utcfromtimestamp(sheader["unix_time"]).isoformat()
    return sheader

# Defines a function to sort strings in natural order. This allows the keys to be read in human/natural order.
def sortkey_natural(text):
	return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text)]	


#h5 developed previously	
def oldScript():
    global root, outfile
    file_list = glob(os.path.join(input_dir, '*.h5'))
    # sort the list and pull out the first and last items in the list
    # rename the items
    # edit here if name of file is different
    for file in sorted(file_list):	
        first_file = sorted(file_list).pop(0)
        last_file = sorted(file_list).pop()
        firstfiledate = os.path.basename(first_file)[10:-50:1]
        lastfiledate = os.path.basename(last_file)[10:-50:1]
        scifirstfiledate = os.path.basename(first_file)[16:-50:1]
        scilastfiledate = os.path.basename(last_file)[16:-50:1]
	
    # create output file for raw packets
    # comment next line out to NOT create output file!
    # edit here for different directory
    outputfile = {}
    ofile = {}
    for path, dirs, files in os.walk(input_dir):
        files_list = glob(os.path.join(input_dir, '*.h5'))
        for file in sorted(files_list):
            #f = h5py.File(os.path.join(files_list,file), 'r')
            f = h5py.File(file, 'r')
            RawAPs = f["All_Data"].keys()
            for RawAP in RawAPs:
                outputfilename = RawAP +"_"+ firstfiledate +"_"+ lastfiledate
                
                outputfile[RawAP] = "C:/JPSS/"+basename(outputfilename)+".pkt"
                outfile = outputfile[RawAP]
                if RawAP in ofile:
                    pass
                else:
                    ofile[RawAP] = open(outputfile[RawAP], 'wb')

    fullSize = len(files_list)
    chunkSize = fullSize/100
    mpb = ttk.Progressbar(root,orient ="horizontal",length = 200, mode ="determinate")
    mpb.pack(side=TOP, expand=YES)
    mpb["maximum"] = fullSize
    # loop through all files
    for path, dirs, files in os.walk(input_dir):
        files_list = glob(os.path.join(input_dir, '*.h5'))
        for file in sorted(files_list):
            mpb["value"] = mpb["value"] + chunkSize
            root.update()
            f = h5py.File(file, 'r')
            #f = h5py.File(os.path.join(files_list,file), 'r')
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
                      pheader = phead(inputFileValues[offset:offset+7])
                      if pheader["apid"] > 0:
                          # read the secondary header
                         sheader = shead(inputFileValues[offset+6:offset+6+9])

        					# extract telemetry points of interest
    						# these lines are commented out to speed up the running time of the program
    						#telem_item_word_no = bin_to_dec( inputFileValues[offset+14:offset+14+2], 0, 16)
    						#dwell_sample_1 = bin_to_dec( inputFileValues[offset+14+2:offset+14+4], 0, 16)
    						#dwell_sample_2 = bin_to_dec( inputFileValues[offset+14+4:offset+14+6], 0, 16)
    						#dwell_sample_3 = bin_to_dec( inputFileValues[offset+14+6:offset+14+8], 0, 16)
            
                         # write packet to output file, comment out for no output file!
                         ofile[RawAP].write(inputFileValues[offset:offset+pheader["pkt_len"]+7])
                        
                         # display packet time and first three telemetry points
                         # this line is commented out to speed up the running time of the program
                         #print pheader["apid"],", ", pheader["seq_cnt"],", ", sheader["desc_time"],",", telem_item_word_no,",", dwell_sample_1, ",", dwell_sample_2, ",", dwell_sample_3
                        
                         # set file offset to the next packet location   
                         offset = offset + pheader["pkt_len"] + 6 + 1
                         # print that the output file was written
                         # comment out for NO output file(s)
                         # this line is commented out to speed up the running time of the program
                         #print "Wrote " + outputfile[RawAP]
		
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
        return range(0,100)
    elif ins_string == "ATMS":
        print()
    elif ins_string == "OMPS":
        print()
    elif ins_string == "VIIRS":
        print()
    elif ins_string == "CERES":
        print()
    elif ins_string == "CRIS":
        print()
    else:
        print("Error")
     
#Launch C++ to do the de-com     
def callCXX (sel_apids, database, ins_string):  
    global outfile
    with open("C:\JPSS\CXXParams.csv",'wb') as resultFile:
        wr = csv.writer(resultFile, dialect='excel')
        wr.writerow(sel_apids)
    args = ['C:/JPSS/CXXDecom/x64/Release/Decom.exe', database, ins_string, outfile, 'C:/JPSS/CXXParams.csv']
    subprocess.call(args) 


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



