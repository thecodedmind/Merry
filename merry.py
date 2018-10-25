import tkinter
from tkinter import ttk
import subprocess
import json
from functools import partial
import tkinter.messagebox
import socket
import os
import asyncio
import webbrowser
from git import Repo


changelog = """Binary support"""

version = "18.10.25"

scriptdir = os.path.dirname(os.path.abspath(__file__))+"/"
merrygui = None
fmod = {}
checkbox_force_reinstall = 0
checkbox_full_search = 0

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None
		
    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tkinter.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
     
    def __str__(self):
        return "CreateToolTip"
	
def internet(host="8.8.8.8", port=53, timeout=3):
	if boolinate(getConfig()['force_offline']):
		return False
	try:
		socket.setdefaulttimeout(timeout)
		socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
		return True
	except Exception as ex:
		print( ex)
		return False

def running_net_check():
	if not internet():
		print("Network test failed.")
		merrygui.offline = False
		merrygui.b_updatecheck.config(state="disabled")
		merrygui.b_install.config(state="disabled")
		merrygui.b_rec = tkinter.Button(merrygui.mainwin, image=merrygui.bicon, command=reconnect)
		merrygui.b_rec.grid(row=0, column=5)
		CreateToolTip(merrygui.b_rec, "Reconnect to network.")
		merrygui.infolab.config(text="No internet connection was found.\nMerry will run in offline mode. (No update checking.)")
		tkinter.messagebox.showerror(message="Internet connection was lost...")
		return False
	else:
		print("Network test passed.")
		return True

"""
	shadow = copy.copy(data)
	ls = getConfig()['ignores']
	for item in shadow:
		if shadow[item][0] in ls:
			print(f"Deleting {item}")
			del data[item]
			"""		
def build_package_dict(output):
	global fmod
	lines = output.split("\n")
	modules_outdated = lines[2:]
	fmod = {}
	i = 0
	for item in modules_outdated:
		f = item.split(" ")
		ls = getConfig()['ignores']
		print(f[0])
		if f[0] not in ls:
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
		res = subprocess.run([host.pip, "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		output = str(res.stdout,"latin-1")
		output += str(res.stderr,"latin-1")
	data = build_package_dict(output)
	host.modules.delete(0, tkinter.END)
	i = 0
	for item in data:
		host.modules.insert(tkinter.END, data[item][0])
		i += 1
	print(data)
	host.b_update.config(state="disabled")
	host.b_uninstall.config(state="normal")
	merrygui.infolab.config(text=f"{i} modules found.")
	
def get_updates(host):
	if not running_net_check():
		return
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
		res = subprocess.run([host.pip, "list", "--outdated"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		output = str(res.stdout,"latin-1")
		output_err = str(res.stderr,"latin-1")
		if len(output_err) > 0:
			tkinter.messagebox.showerror(message=output_err)
			return
			
	data = build_package_dict(output)
	host.modules.delete(0, tkinter.END)
	
	if len(data) > 0:
		for item in data:
			host.modules.insert(tkinter.END, data[item][0])
		print(data)
		host.b_update.config(state="normal")
		host.b_uninstall.config(state="normal")
		tkinter.messagebox.showinfo(title="Result", message=f"{len(data)} updates found!")
		merrygui.infolab.config(text=f"{len(data)} updates found!")
	else:
		merrygui.infolab.config(text="No updates found!")
		tkinter.messagebox.showinfo(title="Result", message=f"No updates found!")
	
def getConfig():
	with open(scriptdir+"config.json") as f:
		return json.load(f)

def setConfig(key:str, value):
	data = getConfig()
	data[key] = value
	with open(scriptdir+'config.json', "w") as s:
		json.dump(data, s, indent=4, sort_keys=True)

def dumpConfig(data):
	with open(scriptdir+'config.json', "w") as s:
		json.dump(data, s, indent=4, sort_keys=True)

def install_binary():
	binscript = '''#!/usr/bin/env python3

import subprocess
import os
path = os.path.expanduser('~')
subprocess.run(['python3', path+'/merry/merry.py'])'''
	path = os.path.expanduser('~')
	open(path+"/.local/bin/merry", 'w+').close()
	with open(path+"/.local/bin/merry", 'w+') as f:
		f.write(binscript)
	subprocess.run(['chmod', 'u+x', path+"/.local/bin/merry"])
def boolinate(string):
	try:
		truth = ['true', '1', 'yes', 'on']
		if string.lower() in truth:
			return True
		else:
			return False
	except:
		return string

def install_moduletext(module):
	if not running_net_check():
		return
			
	if len(module) == 0:
		tkinter.messagebox.showerror(message="Enter text first!")
		return
		
	print("will install "+module)

	if merrygui.usermode:
		res = subprocess.run([merrygui.pip, "install", "--user", module.get()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	else:
		res = subprocess.run([merrygui.pip, "install", module], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	output = str(res.stdout,"latin-1")
	output += str(res.stderr,"latin-1")
	#tkinter.messagebox.showinfo(title="Result", message=output)
	#r = tkinter.Tk()
	#lb = tkinter.Label(r, text=output, justify="left")
	#lb.grid()

	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	T.insert('1.0',output)
	master.title("Result")
	master.mainloop()
	
def install_module(module):
	if not running_net_check():
		return
		
	if len(module.get()) == 0:
		tkinter.messagebox.showerror(message="Enter text first!")
		return
	
	print(checkbox_force_reinstall)	
	print("will install "+module.get())
	if not tkinter.messagebox.askokcancel(message=f"Install {module.get()}"):
		return
		
	coms = [merrygui.pip, 'install']
	if merrygui.usermode:
		coms.append("--user")
	if checkbox_force_reinstall:
		coms.append("--force-reinstall")
	coms.append(module.get())
	print(coms)
	
	res = subprocess.run(coms, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	output = str(res.stdout,"latin-1")
	output += str(res.stderr,"latin-1")
	#tkinter.messagebox.showinfo(title="Result", message=output)
	#r = tkinter.Tk()
	#lb = tkinter.Label(r, text=output, justify="left")
	#lb.grid()

	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	T.insert('1.0',output)
	master.title("Result")
	master.mainloop()

def search_module(module):
	if not running_net_check():
		return
	if len(module.get()) == 0:
		tkinter.messagebox.showerror(message="Enter text first!")
		return
	print("will search "+module.get())
	
	res = subprocess.run([merrygui.pip, "search", module.get()], stdout=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	
	if checkbox_full_search:
		master = tkinter.Tk()
		master.geometry(merrygui.win_size)
		S = tkinter.Scrollbar(master)
		
		S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
		T = tkinter.Text(master, height=20, width=70)
		T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
		S.config(command=T.yview)
		T.config(yscrollcommand=S.set)	
		T.insert('1.0',output)
		master.title("Result")
		master.mainloop()
		return
		
	#tkinter.messagebox.showinfo(title="Result", message=output)
	outs = output.split("\n")
	fout = []
	fvers = []
	fdesc = []
	for item in outs:
		if item != "" and "INSTALLED: " not in item and "LATEST: " not in item:
			fout.append(item.split(" ")[0])
			fvers.append(item.split(" ")[1])
			fdesc.append(' '.join(item.split(" ")[2:]))
			
	r = tkinter.Tk()
	i = 0
	while i < len(fout):
		ins = partial(install_moduletext, fout[i])
		lbut = tkinter.Button(r, text=fout[i]+" "+fvers[i], command=ins, width=20)
		lb = tkinter.Label(r, text=fdesc[i].strip(), justify="left")
		lb.grid(row=i, column=1)
		lbut.grid(row=i)
		
		i += 1
		if i > 5:
			break
		
	r.title(f"{len(fout)} results")
	r.mainloop()

def checkbox_force_reinstall_toggle():
	global checkbox_force_reinstall
	if checkbox_force_reinstall == 0:
		checkbox_force_reinstall = 1
	else:
		checkbox_force_reinstall = 0
		
def checkbox_full_search_toggle():
	global checkbox_full_search
	if checkbox_full_search == 0:
		checkbox_full_search = 1
	else:
		checkbox_full_search = 0	

def about_installer():
	tkinter.messagebox.showinfo(message="Enter a module name in to the box first.\nPressing INSTALL will directly install the module with that name through pip.\nIf you toggle 'force reinstall' on, it will force reinstall the module.\nPressing Search will display the top results of modules using the input as a search term.\nBy default it will show the top 6 results. Press the name button to install the module.\nToggling on Show FULL search will show EVERY result.")
	
def install():
	if not running_net_check():
		return
		
	w = tkinter.Tk()
	
	en = tkinter.Entry(w, width=20)
	run_inst = partial(install_module, en)
	run_srch = partial(search_module, en)
	b = tkinter.Button(w, text="Install", command=run_inst, cursor="hand1")
	sr = tkinter.Button(w, text="Search", command=run_srch, cursor="hand1")
	chk = tkinter.Checkbutton(w, text="Force Reinstall", command=checkbox_force_reinstall_toggle)
	chk2 = tkinter.Checkbutton(w, text="Show FULL search", command=checkbox_full_search_toggle)
	lab = tkinter.Button(w, text="?", command=about_installer)
	en.grid(columnspan=3)
	b.grid(row=1)
	sr.grid(row=1, column=1)
	lab.grid(row=1, column=2)
	
	chk.grid(row=2, column=0, columnspan=3)
	chk2.grid(row=3, column=0, columnspan=3)
	
	w.title("Installer")
	w.mainloop()
	
def uninstall():
	mod = merrygui.modules.curselection()[0]
	mod += 1
	if tkinter.messagebox.askokcancel(title=f"Uninstall {fmod[mod][0]}", message=f"{fmod[mod][0]} {fmod[mod][1]} will be COMPLETELY uninstalled."):
		res = subprocess.run([merrygui.pip, "uninstall", "-y", fmod[mod][0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
		output += str(res.stderr,"latin-1")
		merrygui.modules.delete(mod-1)
		merrygui.modules.insert(mod-1, fmod[mod][0]+" (Removed)")
		#r = tkinter.Tk()
		#lb = tkinter.Label(r, text=output, justify="left")
		#lb.grid()

		master = tkinter.Tk()
		master.geometry(merrygui.win_size)
		S = tkinter.Scrollbar(master)
		
		S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
		T = tkinter.Text(master, height=20, width=70)
		T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
		S.config(command=T.yview)
		T.config(yscrollcommand=S.set)	
		T.insert('1.0',output)
		master.title("Result")
		master.mainloop()

def update():
	if not running_net_check():
		return
		
	mod = merrygui.modules.curselection()[0]
	mod += 1
	print(fmod[mod][0])
	if tkinter.messagebox.askokcancel(title=f"Update {fmod[mod][0]}", message=f"{fmod[mod][0]} will be updated from {fmod[mod][1]} to {fmod[mod][2]}"):
		if merrygui.usermode:
			res = subprocess.run([merrygui.pip, "install", "--upgrade", fmod[mod][0]], stdout=subprocess.PIPE)
		else:
			res = subprocess.run([merrygui.pip, "install", "--upgrade", "--user", fmod[mod][0]], stdout=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
		merrygui.modules.delete(mod-1)
		merrygui.modules.insert(mod-1, fmod[mod][0]+" (Updated)")
		#session_updates.append(fmod[mod][0])
		#build_package_dict(session_update)
		#merrygui.modules.selection_set("--==UPDATED==--")
		#r = tkinter.Tk()
		#lb = tkinter.Label(r, text=output, justify="left")
		#lb.grid()

		master = tkinter.Tk()
		master.geometry(merrygui.win_size)
		S = tkinter.Scrollbar(master)
		
		S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
		T = tkinter.Text(master, height=20, width=70)
		T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
		S.config(command=T.yview)
		T.config(yscrollcommand=S.set)	
		T.insert('1.0',output)
		master.title("Result")
		master.mainloop()

def onselect(evt):
	w = evt.widget
	try:
		index = int(w.curselection()[0])
	except IndexError:
		return
	index += 1
	# value = w.get(index)
	try:
		merrygui.infolab.config(text=fmod[index][0]+" - Current Version: "+fmod[index][1]+" - PIP Version: "+fmod[index][2])
	except:
		merrygui.infolab.config(text=fmod[index][0]+" "+fmod[index][1])		

def reconnect():
	if internet():
		merrygui.b_updatecheck.config(state="normal")
		merrygui.b_install.config(state="normal")
		merrygui.b_rec.destroy()
		merrygui.online = True
		merrygui.infolab.config(text="Reconnected to network!")
	else:
		tkinter.messagebox.showerror(title="No network connection", message="No internet connection was found.\nMerry will run in offline mode. (No update checking.)")	

def pipcheck():
	res = subprocess.run([merrygui.pip, "check"], stdout=subprocess.PIPE)
	output = str(res.stdout,"latin-1")	
	#r = tkinter.Tk()
	#lb = tkinter.Label(r, text=output, justify="left")
	#lb.grid()

	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	T.insert('1.0',output)
	master.title("Result")
	master.mainloop()

	
def pipshow():
	try:
		mod = merrygui.modules.curselection()[0]
	except IndexError:
		tkinter.messagebox.showerror(title="Error", message="No package selected.")
		return
	mod += 1
	res = subprocess.run([merrygui.pip, "show", fmod[mod][0]], stdout=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	#r = tkinter.Tk()
	#lb = tkinter.Label(r, text=output, justify="left")
	#lb.grid()

	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	T.insert('1.0',output)
	master.title("Result")
	master.mainloop()

def piprein():
	if not running_net_check():
		return
		
	try:
		mod = merrygui.modules.curselection()[0]
	except IndexError:
		tkinter.messagebox.showerror(title="Error", message="No package selected.")
		return
		
	mod += 1
	
	if not tkinter.messagebox.askokcancel(message=f"Reinstall {fmod[mod][0]}?"):
		return	
		
	res = subprocess.run([merrygui.pip, "install", "--force-reinstall", fmod[mod][0]], stdout=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	merrygui.modules.delete(mod-1)
	merrygui.modules.insert(mod-1, fmod[mod][0].split(' ')[0])
	#r = tkinter.Tk()
	#lb = tkinter.Label(r, text=output, justify="left")
	#lb.grid()

	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	T.insert('1.0',output)
	master.title("Result")
	master.mainloop()

def set_launch_cfg():
	print("launch cfg")
	old = getConfig()['auto_update_check']
	if boolinate(old):
		setConfig('auto_update_check', "false")
	else:
		setConfig('auto_update_check', "true")
		
def set_launch_self_cfg():
	print("launch cfg")
	old = getConfig()['auto_update_check_self']
	if boolinate(old):
		setConfig('auto_update_check_self', "false")
	else:
		setConfig('auto_update_check_self', "true")
		
def set_offline_cfg():
	print("offline cfg")
	old = getConfig()['force_offline']
	if boolinate(old):
		setConfig('force_offline', "false")
	else:
		setConfig('force_offline', "true")
			
def set_user_cfg():
	print("user cfg")
	old = getConfig()['add_user_flag']
	if boolinate(old):
		setConfig('add_user_flag', "false")
	else:
		setConfig('add_user_flag', "true")

		
def commit_pip_cfg(entry):
	print(entry.get())
	setConfig('pip_command', entry.get())

def commit_output_cfg(entry):
	print(entry.get())
	setConfig('output_win_size', entry.get())
	
def open_config_win():
	w = tkinter.Tk()
	w.title("Config")
	basecfg = getConfig()
	chk = tkinter.Checkbutton(w, text="Update pip modules on Launch", command=set_launch_cfg)
	chk2 = tkinter.Checkbutton(w, text="Add --user flag to installs", command=set_user_cfg)
	chk3 = tkinter.Checkbutton(w, text="Force offline mode", command=set_offline_cfg)
	chk4 = tkinter.Checkbutton(w, text="Check for Merry updates on launch", command=set_launch_self_cfg)
	en_lab = tkinter.Label(w, text="Pip command: ")
	en = tkinter.Entry(w)
	en2_lab = tkinter.Label(w, text="Output Window size: ")
	en2 = tkinter.Entry(w)
	cp = partial(commit_pip_cfg, en)
	co = partial(commit_output_cfg, en2)
	en_but = tkinter.Button(w, text="Save", command=cp)
	en2_but = tkinter.Button(w, text="Save", command=co)
	chk.grid(columnspan=2, sticky="w")
	chk2.grid(row=1, columnspan=2, sticky="w")
	chk3.grid(row=2, columnspan=2, sticky="w")
	chk4.grid(row=3, columnspan=2, sticky="w")
	en_lab.grid(row=4, column=0)
	en2_lab.grid(row=5, column=0)
	en.grid(row=4, column=1)
	en2.grid(row=5, column=1)
	en_but.grid(row=4, column=3)
	en2_but.grid(row=5, column=3)
	
	if boolinate(basecfg['auto_update_check']):
		chk.select()
	if boolinate(basecfg['add_user_flag']):
		chk2.select()
	if boolinate(basecfg['force_offline']):
		chk3.select()
	if boolinate(basecfg['auto_update_check_self']):
		chk4.select()
	en.insert(0, basecfg['pip_command'])
	en2.insert(0, basecfg['output_win_size'])
	
def opengithub(event):
	if not running_net_check():
		return
		
	webbrowser.open(r"https://github.com/Kaiz0r/Merry")

def openpypi():
	if not running_net_check():
		return
		
	try:
		mod = merrygui.modules.curselection()[0]
	except IndexError:
		tkinter.messagebox.showerror(title="Error", message="No package selected.")
		return
		
	mod += 1
	
	if not tkinter.messagebox.askokcancel(message=f"Open https://pypi.org/project/{fmod[mod][0]}?"):
		return	
		
	webbrowser.open(r"https://pypi.org/project/"+fmod[mod][0]+"/")
    		
def about():
	w = tkinter.Tk()
	info = tkinter.Label(w, text="Merry is a pip GUI interface written by Kaiser. Source is available at ")
	url = tkinter.Label(w, text="https://github.com/Kaiz0r/Merry", fg="blue", cursor="hand2")
	info.pack()
	url.pack()
	url.bind("<Button-1>", opengithub)
	w.title("About")

def self_update():
	subprocess.run(['rm', '-rf', '_tmp'])
	subprocess.run(['mkdir', '_tmp'])
	Repo.clone_from("https://github.com/Kaiz0r/Merry.git", scriptdir+"_tmp")
	new_file = os.path.getsize(scriptdir+"_tmp/merry.py")
	this_file = os.path.getsize(scriptdir+"merry.py")
	if this_file != new_file:
		w = tkinter.Tk()
		w.title("Update")
		lab = tkinter.Label(w, text="There is an update available from the Git source.\nPress the Update button below to auto-install the update.\nOr, you can manually download the files from GitHub.\nOr, copy the files over from the _tmp directory in this scripts directory.")
		url = tkinter.Label(w, text="https://github.com/Kaiz0r/Merry", fg="blue", cursor="hand2")
		lab.pack()
		url.pack()
		url.bind("<Button-1>", opengithub)
		upd_cfg = partial(commit_update, True)
		upd = tkinter.Button(w, text="Update (Save Old Config)", command=commit_update)
		upd2 = tkinter.Button(w, text="Update All", command=upd_cfg)
		upd.pack()
		upd2.pack()
	else:
		try:
			merrygui.infolab.config(text="Merry is up-to-date!")
		except:
			print("Update check passed.")
		subprocess.run(['rm', '-rf', '_tmp'])
	#subprocess.run(['rmdir', '_tmp'])

def commit_update(overwrite_cfg=False):
	master = tkinter.Tk()
	master.geometry(merrygui.win_size)
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	
	master.title("Updating")
	#master.mainloop()
	T.insert('1.0',"Starting update.\n")
	
	if overwrite_cfg:
		T.insert('1.0', "cp _tmp/config.json config.json\n")
		res = subprocess.run(['cp', '_tmp/config.json', 'config.json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output = str(res.stdout,"latin-1")
		output_errs = str(res.stderr,"latin-1")
		T.insert('1.0',output)
		T.insert('1.0',output_errs)
	else:
		T.insert('1.0', "Skipping config.\n")
		

	T.insert('1.0', "cp _tmp/merry.py merry.py\n")
	res = subprocess.run(['cp', '_tmp/merry.py', 'merry.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/dl.png dl.png\n")
	res = subprocess.run(['cp', '_tmp/dl.png', 'dl.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/icon.png icon.png\n")
	res = subprocess.run(['cp', '_tmp/icon.png', 'icon.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/list.png list.png\n")
	res = subprocess.run(['cp', '_tmp/list.png', 'list.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/py.png py.png\n")
	res = subprocess.run(['cp', '_tmp/py.png', 'py.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/reset.png reset.png\n")
	res = subprocess.run(['cp', '_tmp/reset.png', 'reset.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
	
	T.insert('1.0', "cp _tmp/uni.png uni.png\n")
	res = subprocess.run(['cp', '_tmp/uni.png', 'uni.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)	
		
	T.insert('1.0', "cp _tmp/upg.png upg.png\n")
	res = subprocess.run(['cp', '_tmp/upg.png', 'upg.png'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	output = str(res.stdout,"latin-1")
	output_errs = str(res.stderr,"latin-1")
	T.insert('1.0',output)
	T.insert('1.0',output_errs)		
	
	#T.insert('1.0', "Update complete.\n")	
	subprocess.run(['rm', '-rf', '_tmp'])
	T.insert('1.0', "Clearing temp directory.\n")
	T.insert('1.0', "Update complete. Restart Merry to see the changes!\n")	

def changes():
	master = tkinter.Tk()
	master.geometry("240x120")
	S = tkinter.Scrollbar(master)
	
	S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
	T = tkinter.Text(master, height=20, width=70)
	T.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
	S.config(command=T.yview)
	T.config(yscrollcommand=S.set)	
	
	master.title("Changes")
	#master.mainloop()
	T.insert('1.0',changelog)

def add_ignore(modules, en):
	if len(en.get()) == 0:
		tkinter.messagebox.showerror(message="No module name entered.")
		return
		
	ls = getConfig()['ignores']
	modules.insert(tkinter.END, en.get())
	ls.append(en.get())
	setConfig("ignores", ls)
	
def rem_ignore(modules):
	try:
		mod = modules.curselection()[0]
	except:
		return
	ls = getConfig()['ignores']
	ls.remove(ls[mod])
	setConfig("ignores", ls)
	modules.delete(mod)
	
def edit_ignores():
	ls = getConfig()['ignores']
	w = tkinter.Tk()
	w.title("Ignores")
	modules = tkinter.Listbox(w, height=15)
	en = tkinter.Entry(w)
	addmod = partial(add_ignore, modules, en)
	remmod = partial(rem_ignore, modules)
	b_add = tkinter.Button(w, text="+", command=addmod)
	b_rem = tkinter.Button(w, text="-", command=remmod)
	
	modules.grid(columnspan=2)
	b_add.grid(column=0, row=1)
	b_rem.grid(column=1, row=1)
	en.grid(columnspan=2, row=2)
	for item in ls:
		modules.insert(tkinter.END, item)
	
class pipGuiMan:
	def __init__(self):
		self.online = internet()
		self.config = getConfig()
		self.pip = self.config['pip_command']
		self.update_check_on_start = boolinate(self.config['auto_update_check'])
		self.usermode = boolinate(self.config['add_user_flag'])
		self.win_size = self.config['output_win_size']
		self.mainwin = tkinter.Tk()
		self.modules = tkinter.Listbox(self.mainwin, height=15)
		self.modules.grid(rowspan=6, columnspan=4)
		self.modules_scroll = tkinter.Scrollbar(self.mainwin)
		self.modules_scroll.grid(column=4, row=0, rowspan=5, sticky="ns")
		self.modules_scroll.config(command=self.modules.yview)
		self.modules.config(yscrollcommand=self.modules_scroll.set)	
		self.modules.bind('<<ListboxSelect>>', onselect)
		ub = partial(get_updates, self)
		ubi = partial(get_modules, self)
		self.infolab = tkinter.Label(self.mainwin, text="Selected info will appear here.")
		self.infolab.grid(row=6, columnspan=6)
		self.chicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'py.png'))
		self.listicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'list.png'))
		self.dlicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'dl.png'))
		self.unicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'uni.png'))
		self.upicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'upg.png'))
		self.b_updatecheck = tkinter.Button(self.mainwin, image=self.chicon, compound="left", text="Check for updates", command=ub, cursor="hand1", width=150, anchor="w")
		self.b_listall = tkinter.Button(self.mainwin, text="Show list", image=self.listicon, compound="left", command=ubi, cursor="hand1", width=150, anchor="w")
		self.b_install = tkinter.Button(self.mainwin, image=self.dlicon, compound="left", text="Install...", command=install, cursor="hand1", width=150, anchor="w")
		self.b_uninstall = tkinter.Button(self.mainwin, image=self.unicon, compound="left", text="Uninstall", command=uninstall, state="disabled", cursor="hand1", width=150, anchor="w")
		self.b_update = tkinter.Button(self.mainwin, image=self.upicon, compound="left", text="Update", command=update, state="disabled", cursor="hand1", width=150, anchor="w")
		
		self.b_updatecheck.grid(column=5, row=0)
		CreateToolTip(self.b_updatecheck, "Gets outdated modules list.\nNOTE: Will take a few moments.")
		self.b_listall.grid(column=5, row=1)
		CreateToolTip(self.b_listall, "Gets installed modules list.\nNOTE: Will take a few moments.")
		self.b_install.grid(column=5, row=2)
		CreateToolTip(self.b_install, "Opens the Installer window. Enter a module name to download and install using pip.")
		self.b_uninstall.grid(column=5, row=3)
		CreateToolTip(self.b_uninstall, "Completely uninstalls the module selected in the list.")
		self.b_update.grid(column=5, row=4)
		CreateToolTip(self.b_update, "Updates the selected module in the list.")
		self.mainwin.title("Merry "+version)
		imgicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'icon.png'))
		self.mainwin.tk.call('wm', 'iconphoto', self.mainwin, imgicon)  
		self.menu = tkinter.Menu(self.mainwin)
		self.mainwin.config(menu=self.menu)

		self.filemenu = tkinter.Menu(self.mainwin)
		self.menu.add_cascade(label="Merry", menu=self.filemenu)
		self.filemenu.add_command(label="About", command=about)
		self.filemenu.add_command(label="Check Libraries integrity", command=pipcheck)
		self.filemenu.add_command(label="Show info on selected package", command=pipshow)
		self.filemenu.add_command(label="Force reinstall selected package", command=piprein)
		self.filemenu.add_command(label="Edit Ignored modules", command=edit_ignores)
		self.filemenu.add_command(label="Open module on pypi", command=openpypi)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Open config...", command=open_config_win)
		self.filemenu.add_command(label="Check for updates", command=self_update)
		self.filemenu.add_command(label="Changelog", command=changes)
		self.filemenu.add_command(label="Install Binary file", command=install_binary)
		self.filemenu.add_separator()
		self.filemenu.add_command(label="Exit", command=self.mainwin.destroy)
		
		if not self.online:
			self.b_updatecheck.config(state="disabled")
			self.b_install.config(state="disabled")
			self.bicon = tkinter.PhotoImage(file=os.path.join(scriptdir,'reset.png'))
			self.b_rec = tkinter.Button(self.mainwin, image=self.bicon, command=reconnect)
			self.b_rec.grid(row=0, column=5)
			CreateToolTip(self.b_rec, "Reconnect to network.")
			self.infolab.config(text="No internet connection was found.\nMerry will run in offline mode. (No update checking.)")
			
		if self.update_check_on_start and self.online:
			get_updates(self)
		if boolinate(self.config['auto_update_check_self']) and self.online:
			self_update()	

def begin():
	global merrygui
	merrygui = pipGuiMan()	
	merrygui.mainwin.mainloop()
if __name__ == "__main__":	
	begin()
	print("Closing.")


