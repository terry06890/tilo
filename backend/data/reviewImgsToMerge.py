#!/usr/bin/python3

import sys, re, os, time
import sqlite3
import tkinter as tki
from tkinter import ttk
import PIL
from PIL import ImageTk, Image, ImageOps

usageInfo =  f"usage: {sys.argv[0]}\n"
usageInfo += "Provides a GUI that displays, for each tol-node, an associated image from\n"
usageInfo += "eol/* and enwiki/*, and enables the user to choose which to use. Writes\n"
usageInfo += "choice data to a text file with lines of the form 'otolId1 imgPath1', or\n"
usageInfo += "'otolId1', where no path indicates a choice of no image.\n"
usageInfo += "\n"
usageInfo += "The program can be closed, and run again to continue from the last choice.\n"
usageInfo += "The program looks for an existing output file to determine what choices\n"
usageInfo += "have already been made.\n"
if len(sys.argv) > 1:
	print(usageInfo, file=sys.stderr)
	sys.exit(1)

eolImgDir = "eol/imgsReviewed/"
enwikiImgDir = "enwiki/imgs/"
dbFile = "data.db"
outFile = "mergedImgList.txt"
IMG_DISPLAY_SZ = 400
PLACEHOLDER_IMG = Image.new("RGB", (IMG_DISPLAY_SZ, IMG_DISPLAY_SZ), (88, 28, 135))
onlyReviewPairs = False

# Open db
dbCon = sqlite3.connect(dbFile)
dbCur = dbCon.cursor()
# Associate nodes with images
nodeToImgs = {} # Maps otol-ids to img-path arrays
print("Looking through EOL images")
if os.path.exists(eolImgDir):
	for filename in os.listdir(eolImgDir):
		(eolId, _, _) = filename.partition(" ")
		query = "SELECT nodes.id FROM nodes INNER JOIN eol_ids ON nodes.name = eol_ids.name WHERE eol_ids.id = ?"
		found = False
		for (otolId,) in dbCur.execute(query, (int(eolId),)):
			if otolId not in nodeToImgs:
				nodeToImgs[otolId] = []
			nodeToImgs[otolId].append(eolImgDir + filename)
			found = True
		if not found:
			print(f"No node found for {eolImgDir}{filename}", file=sys.stderr)
print(f"Result has {len(nodeToImgs)} node entries")
print("Looking through enwiki images")
if os.path.exists(enwikiImgDir):
	for filename in os.listdir(enwikiImgDir):
		(wikiId, _, _) = filename.partition(".")
		query = "SELECT nodes.id FROM nodes INNER JOIN descs ON nodes.name = descs.name WHERE descs.wiki_id = ?"
		found = False
		for (otolId,) in dbCur.execute(query, (int(wikiId),)):
			if otolId not in nodeToImgs:
				nodeToImgs[otolId] = []
			nodeToImgs[otolId].append(enwikiImgDir + filename)
			found = True
		if not found:
			print(f"No node found for {enwikiImgDir}{filename}", file=sys.stderr)
print(f"Result has {len(nodeToImgs)} node entries")
# Check for already-made choices
print("Filtering out already-chosen IDs")
oldSz = len(nodeToImgs)
if os.path.exists(outFile):
	with open(outFile) as file:
		for line in file:
			line = line.rstrip()
			if " " in line:
				line = line[:line.find(" ")]
			del nodeToImgs[line]
print(f"Filtered out {oldSz - len(nodeToImgs)} entries")

class ImgReviewer:
	""" Provides the GUI for reviewing images """
	def __init__(self, root, nodeToImgs):
		self.root = root
		root.title("Image Reviewer")
		# Setup main frame
		mainFrame = ttk.Frame(root, padding="5 5 5 5")
		mainFrame.grid(column=0, row=0, sticky=(tki.N, tki.W, tki.E, tki.S))
		root.columnconfigure(0, weight=1)
		root.rowconfigure(0, weight=1)
		# Set up images-to-be-reviewed frames
		self.eolImg = ImageTk.PhotoImage(PLACEHOLDER_IMG)
		self.enwikiImg = ImageTk.PhotoImage(PLACEHOLDER_IMG)
		self.labels = []
		for i in (0, 1):
			frame = ttk.Frame(mainFrame, width=IMG_DISPLAY_SZ, height=IMG_DISPLAY_SZ)
			frame.grid(column=i, row=0)
			label = ttk.Label(frame, image=self.eolImg if i == 0 else self.enwikiImg)
			label.grid(column=0, row=0)
			self.labels.append(label)
		# Add padding
		for child in mainFrame.winfo_children():
			child.grid_configure(padx=5, pady=5)
		# Add bindings
		root.bind("<q>", self.quit)
		root.bind("<Key-j>", lambda evt: self.accept(0))
		root.bind("<Key-k>", lambda evt: self.accept(1))
		root.bind("<Key-l>", lambda evt: self.reject())
		# Set fields
		self.nodeImgsList = list(nodeToImgs.items())
		self.listIdx = -1
		self.otolId = None
		self.eolImgPath = None
		self.enwikiImgPath = None
		self.numReviewed = 0
		self.startTime = time.time()
		# Initialise images to review
		self.getNextImgs()
	def getNextImgs(self):
		""" Updates display with new images to review, or ends program """
		# Get next image paths
		while True:
			self.listIdx += 1
			if self.listIdx == len(self.nodeImgsList):
				print("No more images to review. Exiting program.")
				self.quit()
				return
			(self.otolId, imgPaths) = self.nodeImgsList[self.listIdx]
			# Potentially skip user choice
			if onlyReviewPairs and len(imgPaths) == 1:
				with open(outFile, 'a') as file:
					file.write(f"{self.otolId} {imgPaths[0]}\n")
				continue
			break
		# Update displayed images
		self.eolImgPath = self.enwikiImgPath = None
		imageOpenError = False
		for imgPath in imgPaths:
			img = None
			try:
				img = Image.open(imgPath)
				img = ImageOps.exif_transpose(img)
			except PIL.UnidentifiedImageError:
				print(f"UnidentifiedImageError for {imgPath}")
				imageOpenError = True
				continue
			if imgPath.startswith("eol/"):
				self.eolImgPath = imgPath
				self.eolImg = ImageTk.PhotoImage(self.resizeForDisplay(img))
			elif imgPath.startswith("enwiki/"):
				self.enwikiImgPath = imgPath
				self.enwikiImg = ImageTk.PhotoImage(self.resizeForDisplay(img))
			else:
				print(f"Unexpected image path {imgPath}", file=sys.stderr)
				self.quit()
				return
		# Re-iterate if all image paths invalid
		if self.eolImgPath == None and self.enwikiImgPath == None:
			if imageOpenError:
				self.reject()
			self.getNextImgs()
			return
		# Add placeholder images
		if self.eolImgPath == None:
			self.eolImg = ImageTk.PhotoImage(self.resizeForDisplay(PLACEHOLDER_IMG))
		elif self.enwikiImgPath == None:
			self.enwikiImg = ImageTk.PhotoImage(self.resizeForDisplay(PLACEHOLDER_IMG))
		# Update image-frames
		self.labels[0].config(image=self.eolImg)
		self.labels[1].config(image=self.enwikiImg)
		# Update title
		title = f"Imgs for otol ID {self.otolId}"
		query = "SELECT names.alt_name FROM" \
			" nodes INNER JOIN names ON nodes.name = names.name" \
			" WHERE nodes.id = ? and pref_alt = 1"
		row = dbCur.execute(query, (self.otolId,)).fetchone()
		if row != None:
			title += f", aka {row[0]}"
		title += f" ({self.listIdx + 1} out of {len(self.nodeImgsList)})"
		self.root.title(title)
	def accept(self, imgIdx):
		""" React to a user selecting an image """
		imgPath = self.eolImgPath if imgIdx == 0 else self.enwikiImgPath
		if imgPath == None:
			print("Invalid selection")
			return
		with open(outFile, 'a') as file:
			file.write(f"{self.otolId} {imgPath}\n")
		self.numReviewed += 1
		self.getNextImgs()
	def reject(self):
		""" React to a user rejecting all images of a set """
		with open(outFile, 'a') as file:
			file.write(f"{self.otolId}\n")
		self.numReviewed += 1
		self.getNextImgs()
	def quit(self, e = None):
		print(f"Number reviewed: {self.numReviewed}")
		timeElapsed = time.time() - self.startTime
		print(f"Time elapsed: {timeElapsed:.2f} seconds")
		if self.numReviewed > 0:
			print(f"Avg time per review: {timeElapsed/self.numReviewed:.2f} seconds")
		dbCon.close()
		self.root.destroy()
	def resizeForDisplay(self, img):
		""" Returns a copy of an image, shrunk to fit the display (keeps aspect ratio), and with a background """
		if max(img.width, img.height) > IMG_DISPLAY_SZ:
			if (img.width > img.height):
				newHeight = int(img.height * IMG_DISPLAY_SZ/img.width)
				img = img.resize((IMG_DISPLAY_SZ, newHeight))
			else:
				newWidth = int(img.width * IMG_DISPLAY_SZ / img.height)
				img = img.resize((newWidth, IMG_DISPLAY_SZ))
		bgImg = PLACEHOLDER_IMG.copy()
		bgImg.paste(img, box=(
			int((IMG_DISPLAY_SZ - img.width) / 2),
			int((IMG_DISPLAY_SZ - img.height) / 2)))
		return bgImg
# Create GUI and defer control
root = tki.Tk()
ImgReviewer(root, nodeToImgs)
root.mainloop()
