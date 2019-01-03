import tkinter
from tkinter import ttk
from textblob import TextBlob
from bs4 import BeautifulSoup
from functools import partial
import requests
import json

class OutputWindow:
	def __init__(self, *, title="Message", text="", master_window=None, geometry="480x240", font=[], size=8, bg='white', format_links_html=False):
	#	master = tkinter.Tk()
		if master_window:
			self.frame = tkinter.Frame(master_window)
			master = self.frame
		else:
			master = tkinter.Tk()
			master.geometry(geometry)
			master.title(title)
			
		S = tkinter.Scrollbar(master)
		S.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
		self.textbox = tkinter.Text(master, height=20, width=70)
		self.textbox.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.YES)
		S.config(command=self.textbox.yview)
		self.textbox.config(yscrollcommand=S.set)	
		
		
		#master.mainloop()

		self.textbox.tag_configure('red', foreground='red')
		self.textbox.tag_configure('white', foreground='white')
		self.textbox.tag_configure('yellow', foreground='yellow')
		self.textbox.tag_configure('green', foreground='green')
		self.textbox.tag_configure('orange', foreground='orange')
		self.textbox.tag_configure('grey', foreground='grey')
		self.textbox.tag_configure('bold', font=('bold'))
		self.textbox.tag_configure('italics', font=('italics'))
		self.textbox.tag_configure('size', font=(size))
		self.textbox.configure(bg=bg)
		self.textbox.insert('end', text, font)
		self.textbox.config(state="disabled")
		
	def delete(self, index, end_index):
		self.textbox.config(state="normal")
		self.textbox.delete(index, end_index)
		self.textbox.config(state="disabled")
		
	def insert(self, text, *, font=[], size=8, command=None, sep="\n", link_id = "", index='end'):
		self.textbox.config(state="normal")
		#print(f"Inserting `{text}` at `{index}`")
		#print(command)
		#print(link_id)
		if command:
			if link_id == "":
				raise AttributeError("If command is specified, you must give the link a unique ID usin the `link_id` argument.")
			self.textbox.tag_configure(link_id, foreground="blue", underline=1)
			self.textbox.tag_bind(link_id, "<Enter>", self._enter)
			self.textbox.tag_bind(link_id, "<Leave>", self._leave)
			self.textbox.tag_bind(link_id, "<Button-1>", command)
			self.textbox.insert(index, text+sep, link_id)
			self.textbox.config(state="disabled")
			return
		
		self.textbox.insert(index, f"{text}{sep}", font)
		#self.textbox.insert('end', "\n")
		self.textbox.config(state="disabled")
	
	def _enter(self, event):
		self.textbox.config(cursor="hand2")

	def _leave(self, event):
		self.textbox.config(cursor="")

	def _click(self, event):
		print(event.widget)

class PageBrowser:
	def __init__(self, page, *, master_window = "", title = "PageBrowser", base_url = "", data_tags = ['p', 'h2', 'a'], debug=False):
		if base_url:
			self.page = base_url+page
		else:
			self.page = page
		print(f"Query send: {self.page}")
		self.data = requests.get(self.page).text
		
		
		soup = BeautifulSoup(self.data, 'html5lib')
		
		if debug:
			dbg = OutputWindow(title="DEBUGGER")
			dbg.insert(soup.prettify())
		
		if soup.title:
			pass_title = soup.title.text
		else:
			pass_title = title
		self.textwin = OutputWindow(title=pass_title, master_window=master_window)
		if master_window:
			self.textbox = self.textwin.frame
		subs = soup.find_all('a')
		i = 0
		for item in soup.find_all(data_tags):
			i += 1
			if item.name == 'a':
				try:
					if item.get('class') == ["b"] or item.get('class') == ["it"]:
						launcher = partial(BrowseEvent, base_url+item['href'])
						self.textwin.insert(f"{item.text}", link_id=f"lnk_{i}", command=launcher)
				except Exception as e:
					print(type(e))
					print(e)
			elif item.name == "p":
				try:
					if "noMarkerNotice" in item['class'][1] or "videoErrorNotice" in item['class'][1]:
						pass
				except:
					if not item.find('a'):
					#	print(item.text)
						self.textwin.insert(item.text)
				
			elif item.name == "h2":
				self.textwin.insert("\n")
				self.textwin.insert(item.text, font="size", size=20, sep="\n\n")

class JSONBrowser:
	def __init__(self, page, *, master_window = "", title = "PageBrowser", base_url = "", data_tags = ['p', 'h2', 'a'], debug=False, json_string = ""):
		if base_url:
			self.page = base_url+page
		else:
			self.page = page
		print(f"Query send: {self.page}")
		if not json_string:
			self.data = requests.get(self.page).text
			soup = BeautifulSoup(self.data, 'html5lib')
			data = json.loads(soup.text)
		else:
			data = json_string
			
		self.textwin = OutputWindow(title=title, master_window=master_window)
		if master_window:
			self.textbox = self.textwin.frame
		
		if type(data) == dict:
			for item in data:
				if type(data[item]) is not dict:
					self.textwin.insert(ufilter(data[item]))
				else:
					self.textwin.insert(ufilter(item)+" =>", link_id=item, command=lambda event: JSONBrowser("", json_string = data[item]))
		elif type(data) == list:
			for item in data:
				if type(item) is not dict:
					self.textwin.insert(ufilter(item))
				else:
					self.textwin.insert(ufilter(item)+" =>", link_id=item, command=lambda event: JSONBrowser("", json_string = item))
		else:
			self.textwin.insert(ufilter(data))
		
def ufilter(s):
	#return str(s).encode('utf-8')
	return "".join(i for i in str(s) if ord(i)<128)

def BrowseEvent(event, command):
	PageBrowser(event)			
	
