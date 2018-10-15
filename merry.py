import tkinter
from tkinter import ttk
import subprocess
import json
from functools import partial
import tkinter.messagebox
import socket
merrygui = None
fmod = {}

def internet(host="8.8.8.8", port=53, timeout=3):
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except Exception as ex:
		print( ex)
		return False

def build_package_dict(output):
	global fmod
	lines = output.split("\n")
	modules_outdated = lines[2:]
	fmod = {}
	i = 0
	for item in modules_outdated:
		f = item.split(" ")
		m = []
		i += 1
		for fi in f:
			if fi:
				m.append(fi)
		if len(m) > 0:
			fmod[i] = m
	return fmod

def get_modules(host):
	debug = False
	if debug:
		output = """Package    Version
---------- ---------
certifi    2018.4.16
psutil     5.4.6
pycairo    1.17.0
PyQt5-sip  4.19.11
setuptools 39.2.0
"""
	else:
		res = subprocess.run([host.pip, "list"], stdout=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
	data = build_package_dict(output)
	host.modules.delete(0, tkinter.END)
	for item in data:
		host.modules.insert(tkinter.END, data[item][0])
	print(data)
	host.b_update.config(state="disabled")
	host.b_uninstall.config(state="normal")
	
def get_updates(host):
	debug = False
	if debug:
		output = """Package    Version   Latest    Type 
---------- --------- --------- -----
certifi    2018.4.16 2018.8.24 wheel
psutil     5.4.6     5.4.7     sdist
pycairo    1.17.0    1.17.1    sdist
PyQt5-sip  4.19.11   4.19.12   wheel
setuptools 39.2.0    40.2.0    wheel
"""
	else:
		res = subprocess.run([host.pip, "list", "--outdated"], stdout=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
	data = build_package_dict(output)
	host.modules.delete(0, tkinter.END)
	if len(data) > 0:
		for item in data:
			host.modules.insert(tkinter.END, data[item][0])
		print(data)
		host.b_update.config(state="normal")
		host.b_uninstall.config(state="normal")
	else:
		merrygui.infolab.config(text="No updates found!")
	
def getConfig():
	with open("config.json") as f:
		return json.load(f)

def setConfig(key:str, value):
	data = getConfig()
	data[key] = value
	with open('config.json', "w") as s:
		json.dump(data, s, indent=4, sort_keys=True)

def dumpConfig(data):
	with open('config.json', "w") as s:
		json.dump(data, s, indent=4, sort_keys=True)

def boolinate(string):
	try:
		truth = ['true', '1', 'yes', 'on']
		if string.lower() in truth:
			return True
		else:
			return False
	except:
		return string

def install_module(module):
	print("will install "+module.get())
	
	if merrygui.usermode:
		res = subprocess.run([merrygui.pip, "install", "--user", module.get()], stdout=subprocess.PIPE)
	else:
		res = subprocess.run([merrygui.pip, "install", module.get()], stdout=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	#tkinter.messagebox.showinfo(title="Result", message=output)
	r = tkinter.Tk()
	lb = tkinter.Label(r, text=output)
	lb.grid()
	r.title("Result")
	r.mainloop
	
def install():
	w = tkinter.Tk()
	en = tkinter.Entry(w)
	run_inst = partial(install_module, en)
	b = tkinter.Button(w, text="Install", command=run_inst)
	en.grid()
	b.grid(row=1)
	w.title("Installer")
	w.mainloop()
	
def uninstall():
	mod = merrygui.modules.curselection()[0]
	mod += 1
	if tkinter.messagebox.askokcancel(title=f"Uninstall {fmod[mod][0]}", message=f"{fmod[mod][0]} {fmod[mod][1]} will be COMPLETELY uninstalled."):
		res = subprocess.run([merrygui.pip, "uninstall", fmod[mod][0]], stdout=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
		r = tkinter.Tk()
		lb = tkinter.Label(r, text=output)
		lb.grid()
		r.title("Result")
		r.mainloop
		
def update():
	mod = merrygui.modules.curselection()[0]
	mod += 1
	print(fmod[mod][0])
	if tkinter.messagebox.askokcancel(title=f"Update {fmod[mod][0]}", message=f"{fmod[mod][0]} will be updated from {fmod[mod][1]} to {fmod[mod][2]}"):
		if merrygui.usermode:
			res = subprocess.run([merrygui.pip, "install", "--upgrade", fmod[mod][0]], stdout=subprocess.PIPE)
		else:
			res = subprocess.run([merrygui.pip, "install", "--upgrade", "--user", fmod[mod][0]], stdout=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
		r = tkinter.Tk()
		lb = tkinter.Label(r, text=output)
		lb.grid()
		r.title("Result")
		r.mainloop
		
def onselect(evt):
	w = evt.widget
	index = int(w.curselection()[0])
	index += 1
	# value = w.get(index)
	try:
		merrygui.infolab.config(text=fmod[index][0]+" - Current Version: "+fmod[index][1]+" - PIP Version: "+fmod[index][2])
	except:
		merrygui.infolab.config(text=fmod[index][0]+" "+fmod[index][1])		

def reconnect():
	if internet():
		merrygui.b_updatecheck.config(state="normal")
		merrygui.b_rec.destroy()
		merrygui.online = True
		merrygui.infolab.config(text="Reconnected to network!")
	else:
		tkinter.messagebox.showerror(title="No network connection", message="No internet connection was found.\nMerry will run in offline mode. (No update checking.)")	
			
class pipGuiMan:
	def __init__(self):
		self.online = internet()
		self.config = getConfig()
		self.pip = self.config['pip_command']
		self.update_check_on_start = boolinate(self.config['auto_update_check'])
		self.usermode = boolinate(self.config['add_user_flag'])
		self.mainwin = tkinter.Tk()
		self.modules = tkinter.Listbox(self.mainwin)
		self.modules.grid(rowspan=5, columnspan=4)
		self.modules.bind('<<ListboxSelect>>', onselect)
		ub = partial(get_updates, self)
		ubi = partial(get_modules, self)
		self.infolab = tkinter.Label(self.mainwin, text="Selected info will appear here.")
		self.infolab.grid(row=6, columnspan=6)
		self.b_updatecheck = tkinter.Button(self.mainwin, text="Check for updates", command=ub)
		if not self.online:
			self.b_updatecheck.config(state="disabled")
			self.b_rec = tkinter.Button(self.mainwin, text="Reconnect", command=reconnect)
			self.b_rec.grid(row=0, column=5)
			self.infolab.config(text="No internet connection was found.\nMerry will run in offline mode. (No update checking.)")
		self.b_listall = tkinter.Button(self.mainwin, text="Show installed modules", command=ubi)
		self.b_install = tkinter.Button(self.mainwin, text="Install...", command=install)
		self.b_uninstall = tkinter.Button(self.mainwin, text="Uninstall", command=uninstall, state="disabled")
		self.b_update = tkinter.Button(self.mainwin, text="Update", command=update, state="disabled")
		self.b_updatecheck.grid(column=4, row=0)
		self.b_listall.grid(column=4, row=1)
		self.b_install.grid(column=4, row=2)
		self.b_uninstall.grid(column=4, row=3)
		self.b_update.grid(column=4, row=4)
		self.mainwin.title("Merry (pip GUI)")
		
		if self.update_check_on_start and self.online:
			get_updates(self)
			
merrygui = pipGuiMan()	
merrygui.mainwin.mainloop()
print(merrygui.pip)
