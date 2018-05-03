#!/usr/bin/python

from Tkinter import *
import subprocess
from subprocess import Popen, PIPE

root = Tk()
root.title("OVS")

#get the Bridge ID. Works only with one bridgeID.
global bridge
bridge = subprocess.check_output(["ovs-vsctl", "list-br"]).strip()

global var1 
var1 = StringVar()
global var2 
var2 = StringVar()

counter1 = 0

inportslist = subprocess.Popen('ovs-vsctl list-ports ' + bridge,
		       shell=True,
		       stdout=subprocess.PIPE,
		       universal_newlines=True)

inName = Label(root,
               anchor=NW,
               text='Select input port').grid(row=0,column=0,columnspan=1,sticky=N,padx=10,pady=(10,0))

mybuttonlist = []
mylist = []
mynewlist = []

#duplicated in/out port check + popup window
def popupmsg(title, text):
    		popup = Tk()
		popup.wm_title(title)
    		label = Label(popup, text=text).pack(side="top", fill="x", pady=10)
    		B1 = Button(popup, text="Okay", command = popup.destroy).pack()
def selected():
    if var1.get() == var2.get():
	popupmsg('Warning', 'Select different output interface')
	for item in mybuttonlist:
		item.deselect()
	
for item in inportslist.stdout:
	inbutton = Radiobutton(root,
			     text=item,
			     variable=var1,
			     value=item, 
			     command=selected)
			     
	outbutton = Radiobutton(root,
			     text=item,
			     variable=var2,
			     value=item,
			     command=selected)
	mylist.append(item)
	inbutton.grid(row=counter1+1, column=0, sticky=NW)
	outbutton.grid(row=counter1+1, column=1, sticky=NE)
	mybuttonlist.append(outbutton)
	mybuttonlist.append(inbutton)
	counter1=counter1+1

outName = Label(root,
                anchor=NW,
                text='Select output port').grid(row=0,column=1,columnspan=1,sticky=N,padx=10,pady=(10,0))

Label(root, text="Apply Ingress Rate Limit").grid(row = counter1+3, column = 0, columnspan=2)

#rate limit interface selection popup menu

popdefvar = StringVar()
popdefvar.set(' ')

qos = False
def apply_qos(value):
	global qos
	qos = True

for i in mylist:
	mynewlist.append(i.decode().strip("\n"))

popupMenu = OptionMenu(root, popdefvar, *mynewlist, command=apply_qos).grid(row = counter1+5, column = 0)

ratelimitvar = StringVar()
ratelimitvar.set(' ')
ratelimits = [' ', '100', '1000', '10000', '100000']

#rate limit in KB
popup1Menu = OptionMenu(root, ratelimitvar, *ratelimits).grid(row = counter1+5, column = 1)

#Delete all flows in table=0, where default flow is also applied
subprocess.check_output(['ovs-ofctl del-flows ' + bridge + ' table=0'], shell=True)
#Add flow allowing ICMP ping forwarding between all interfaces
subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, icmp, actions=normal\"'], shell=True)

global inportid
global outportid

#apply button action
def append1():
	inportid = subprocess.check_output(['ovs-ofctl dump-ports-desc '+bridge+' |  grep -Po \'(?<=( )).*(?=\('+ var1.get().strip() +')\'|| true'], shell=True).strip()
	outportid = subprocess.check_output(['ovs-ofctl dump-ports-desc '+bridge+' |  grep -Po \'(?<=( )).*(?=\('+ var2.get().strip() +')\'|| true'], shell=True).strip()
	subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
	subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
	subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
	subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)
	subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)	
	applybutton.configure(command=append2)
	if qos == True:
		subprocess.check_output(['ovs-vsctl set interface ' + popdefvar.get().strip()+' ingress_policing_rate='+ratelimitvar.get()], shell=True)

def append2():
	inportid = subprocess.check_output(['ovs-ofctl dump-ports-desc '+bridge+' |  grep -Po \'(?<=( )).*(?=\('+ var1.get().strip() +')\'|| true'], shell=True).strip()
	outportid = subprocess.check_output(['ovs-ofctl dump-ports-desc '+bridge+' |  grep -Po \'(?<=( )).*(?=\('+ var2.get().strip() +')\'|| true'], shell=True).strip()
	global existingflowcheck
	existingflowcheck = subprocess.check_output(['ovs-ofctl dump-flows '+bridge+' out_port='+outportid+' | grep -c cookie | true'], shell=True).strip()
	if existingflowcheck > 0:
		subprocess.check_output(['ovs-ofctl del-flows '+ bridge + ' out_port='+outportid+' | true'], shell=True)
		#Add flow with new out port 
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \" table=0, ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)
	elif qos == True:
		subprocess.check_output(['ovs-vsctl set interface ' + popdefvar.get().strip()+' ingress_policing_rate='+ratelimitvar.get()], shell=True)
	else:
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \" table=0, ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + inportid + ', actions=output:' + outportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=319, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)
		subprocess.check_output(['ovs-ofctl add-flow ' + bridge + ' \"table=0, udp, tp_dst=320, priority=100 ' + 'in_port=' + outportid + ', actions=output:' + inportid + '\"'], shell=True)
		#print "flow with same output port does not exist"

applybutton = Button(root, text='Append', command=append1)
applybutton.grid(row=counter1+8, column=0, columnspan=2, sticky=S)

root.mainloop()
