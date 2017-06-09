from Tkinter import *
from functools import partial
import tkFileDialog as fd
import csv
import subprocess

def switch(argument):
    switcher = {
        0: "ATMS",
        1: "OMPS",
        2: "VIIRS",
        3: "CERES",
        4: "CRIS",
        5: "S/C"
    }
    return switcher.get(argument, "nothing")

def relevantAPIDs(ins_string):
    if ins_string == "S/C":
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
        
def callCXX (sel_apids, database, ins_string):  
    with open("C:\JPSS\Decom\Debug\CXXParams.csv",'wb') as resultFile:
        wr = csv.writer(resultFile, dialect='excel')
        wr.writerow(sel_apids)
    
    args = ['C:\JPSS\Decom\Debug\Decom.exe', database, ins_string]
    subprocess.call(args) 

def run (root, instrument): 
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
    
    Button(apidwindow, text = "Execute", command = partial(run2, Lb1, apidwindow, root, database, ins_string), fg = 'red').pack() 

    
def run2 (Lb1, apidwindow, root, database, ins_string):
    sel_apids = Lb1.curselection()
    apidwindow.destroy()
    root.destroy()
    callCXX(sel_apids,database, ins_string)
    
def getfilename(database):
    database = str(fd.askopenfilename(initialdir="C:\JPSS\\"))


database = ''

root = Tk()
root.title('De-Com Tool')
app = Frame(root)
Button(app, text = 'Select Database File', command = partial(getfilename, database)).pack(side=TOP, expand=YES)

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



