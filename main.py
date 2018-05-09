# CTI-110
# Final project. A website.
# Aaron Bolyard
# 2018-05-03

import http.server
import time
import json
import sqlite3
import html
import socketserver
import mimetypes
import urllib.parse

# An in-memory database (i.e., temporary) that stores notes.
#
# A note is a dictionary of three values: date, author, message, landmark.
class Database:
	connection = None

	def __init__(self):
		self.connection = sqlite3.connect(":memory:")

		c = self.connection.cursor()
		c.execute('''
			CREATE TABLE Notes (
				date TEXT,
				author TEXT,
				message TEXT,
				landmark TEXT
			)''')
		self.connection.commit()

	# Adds a Note.
	#
	# The text properties are escaped.
	def add(self, author, message, landmark):
		c = self.connection.cursor()
		c.execute('''
				INSERT INTO Notes VALUES(?, ?, ?, ?)
			''', (time.ctime(), html.escape(author), html.escape(message), html.escape(landmark)))
		self.connection.commit()

	# Gets a Note.
	#
	# Returns an array of dictionaries with the following fields:
	#  * date: a string with the date
	#  * author: a string with the author's name
	#  * message: a string with the message
	#  * landmark: a string with the landmark
	def get(self):
		results = []
		c = self.connection.cursor()
		for item in c.execute('''SELECT * from Notes'''):
			result = {
				'date': item[0],
				'author': item[1],
				'message': item[2],
				'landmark': item[3]
			}
			results.append(result)

		return results

# A base page class. Emits HTML.
class Page:
	def write(self):
		return '''
			<html>
				<head>
					<title>404</title>
				</head>
				<body>
					<h1>404 - File Not found</h1>
				</body>
			</html>'''.encode()

	def read(self, properties):
		pass

	def getMime(self):
		return "text/html"

class DatabaseGetPage(Page):
	database = None

	def __init__(self, database):
		self.database = database

	def write(self):
		return json.dumps(self.database.get()).encode()

	def getMime(self):
		return "application/json"

class DatabaseSubmitPage(Page):
	database = None
	view = None

	def __init__(self, database, view):
		self.database = database
		self.view = view

	def write(self):
		return self.view.write()

	def read(self, properties):
		author = properties.get("author", [ "Anonymous" ])[0]
		message = properties.get("message", [ None ])[0]
		landmark = properties.get("landmark", [ None ])[0]

		if message != None and landmark != None:
			self.database.add(author, message, landmark)

class SimplePage(Page):
	filename = None

	def __init__(self, filename):
		self.filename = filename

	def write(self):
		with open(self.filename, 'rb') as file:
			return file.read()

	def getMime(self):
		return mimetypes.guess_type(self.filename)[0]

class Website:
	pages = {}
	page404 = Page()
	instance = None

	def addPage(self, filename, page):
		if page != None:
			self.pages[filename] = page

	def getPage(self, filename):
		return self.pages.get(filename, self.page404)

	def getWebsite():
		if Website.instance == None:
			Website.instance = Website()

		return Website.instance

# The request handler.
class WebsiteRequestHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		website = Website.getWebsite()
		filename = self.requestline.split(" ")[1]
		page = website.getPage(filename)

		print("GET", filename)

		if page != None:
			result = page.write()

			self.send_response(200)
			self.send_header("Content-Type", page.getMime())
			self.end_headers()
			self.wfile.write(result)

	def do_POST(self):
		website = Website.getWebsite()
		filename = self.requestline.split(" ")[1]
		page = website.getPage(filename)

		print("POST", filename)

		if page != None:
			propertiesUrl = self.rfile.read(int(self.headers['content-length'])).decode("ascii")
			properties = urllib.parse.parse_qs(propertiesUrl)
			page.read(properties)

			result = page.write()

			self.send_response(200)
			self.send_header("Content-Type", page.getMime())
			self.end_headers()
			self.wfile.write(result)

def main():
	database = Database()
	database.add("Bob", "Great place to buy an axe!", "Bob's Axes")
	database.add("Hans", "My favorite bush.", "South-west bush")
	database.add("EvlHckr420", "<script>alert('youve been h4cked')</script>", "Suspicious rock")

	Website.getWebsite().addPage("/", SimplePage("www/index.html"))
	Website.getWebsite().addPage("/home", SimplePage("www/index.html"))
	Website.getWebsite().addPage("/map", SimplePage("www/map.html"))
	Website.getWebsite().addPage("/about", SimplePage("www/about.html"))
	Website.getWebsite().addPage("/notes", DatabaseGetPage(database))
	Website.getWebsite().addPage("/submit", DatabaseSubmitPage(database, SimplePage("www/submit.html")))
	Website.getWebsite().addPage("/add", SimplePage("www/add.html"))
	Website.getWebsite().addPage("/view", SimplePage("www/view.html"))
	Website.getWebsite().addPage("/style.css", SimplePage("www/style.css"))
	Website.getWebsite().addPage("/images/background-diagonal.png", SimplePage("www/images/background-diagonal.png"))
	Website.getWebsite().addPage("/images/background-solid.png", SimplePage("www/images/background-solid.png"))
	Website.getWebsite().addPage("/images/button.png", SimplePage("www/images/button.png"))
	Website.getWebsite().addPage("/images/map.png", SimplePage("www/images/map.png"))
	Website.getWebsite().addPage("/images/castle.png", SimplePage("www/images/castle.png"))
	Website.getWebsite().addPage("/images/banner.png", SimplePage("www/images/banner.png"))

	results = database.get()
	for result in results:
		print(result['date'], result['author'], result['message'], result['landmark'])

	httpd = socketserver.TCPServer(("", 8000), WebsiteRequestHandler)
	httpd.serve_forever()

main()
