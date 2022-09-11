#!/usr/bin/python3

"""
Provides a GUI that displays, for each node in the database, associated
images from EOL and Wikipedia, and allows choosing which to use. Writes
choice data to a text file with lines of the form 'otolId1 imgPath1', or
'otolId1', where no path indicates a choice of no image.

The program can be closed, and run again to continue from the last choice.
The program looks for an existing output file to determine what choices
have already been made.
"""

import os, time
import sqlite3
import tkinter as tki
from tkinter import ttk
import PIL
from PIL import ImageTk, Image, ImageOps

EOL_IMG_DIR = os.path.join('eol', 'imgs')
ENWIKI_IMG_DIR = os.path.join('enwiki', 'imgs')
DB_FILE = 'data.db'
OUT_FILE = 'img_list.txt'
#
IMG_DISPLAY_SZ = 400
PLACEHOLDER_IMG = Image.new('RGB', (IMG_DISPLAY_SZ, IMG_DISPLAY_SZ), (88, 28, 135))
REVIEW = 'only pairs' # Can be: 'all', 'only pairs', 'none'

class ImgReviewer:
	""" Provides the GUI for reviewing images """
	def __init__(self, root, nodeToImgs, eolImgDir, enwikiImgDir, outFile, dbCon, review):
		self.root = root
		root.title('Image Reviewer')
		# Setup main frame
		mainFrame = ttk.Frame(root, padding='5 5 5 5')
		mainFrame.grid(column=0, row=0, sticky=(tki.N, tki.W, tki.E, tki.S))
		root.columnconfigure(0, weight=1)
		root.rowconfigure(0, weight=1)
		# Set up images-to-be-reviewed frames
		self.eolImg = ImageTk.PhotoImage(PLACEHOLDER_IMG)
		self.enwikiImg = ImageTk.PhotoImage(PLACEHOLDER_IMG)
		self.labels: list[ttk.Label] = []
		for i in (0, 1):
			frame = ttk.Frame(mainFrame, width=IMG_DISPLAY_SZ, height=IMG_DISPLAY_SZ)
			frame.grid(column=i, row=0)
			label = ttk.Label(frame, image=self.eolImg if i == 0 else self.enwikiImg)
			label.grid(column=0, row=0)
			self.labels.append(label)
		# Add padding
		for child in mainFrame.winfo_children():
			child.grid_configure(padx=5, pady=5)
		# Add keyboard bindings
		root.bind('<q>', self.quit)
		root.bind('<Key-j>', lambda evt: self.accept(0))
		root.bind('<Key-k>', lambda evt: self.accept(1))
		root.bind('<Key-l>', lambda evt: self.reject())
		# Set fields
		self.nodeImgsList = list(nodeToImgs.items())
		self.listIdx = -1
		self.eolImgDir = eolImgDir
		self.enwikiImgDir = enwikiImgDir
		self.outFile = outFile
		self.review = review
		self.dbCon = dbCon
		self.dbCur = dbCon.cursor()
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
				print('No more images to review. Exiting program.')
				self.quit()
				return
			self.otolId, imgPaths = self.nodeImgsList[self.listIdx]
			# Potentially skip user choice
			if len(imgPaths) == 1 and (self.review == 'only pairs' or self.review == 'none'):
				with open(self.outFile, 'a') as file:
					file.write(f'{self.otolId} {imgPaths[0]}\n')
				continue
			elif self.review == 'none':
				with open(self.outFile, 'a') as file:
					file.write(f'{self.otolId} {imgPaths[-1]}\n') # Prefer enwiki image
				continue
			break
		# Update displayed images
		self.eolImgPath = self.enwikiImgPath = None
		imageOpenError = False
		for imgPath in imgPaths:
			img: Image
			try:
				img = Image.open(imgPath)
				img = ImageOps.exif_transpose(img)
			except PIL.UnidentifiedImageError:
				print(f'UnidentifiedImageError for {imgPath}')
				imageOpenError = True
				continue
			if imgPath.startswith(self.eolImgDir):
				self.eolImgPath = imgPath
				self.eolImg = ImageTk.PhotoImage(self.resizeImgForDisplay(img))
			elif imgPath.startswith(self.enwikiImgDir):
				self.enwikiImgPath = imgPath
				self.enwikiImg = ImageTk.PhotoImage(self.resizeImgForDisplay(img))
			else:
				print(f'Unexpected image path {imgPath}')
				self.quit()
				return
		# Re-iterate if all image paths invalid
		if self.eolImgPath is None and self.enwikiImgPath is None:
			if imageOpenError:
				self.reject()
			self.getNextImgs()
			return
		# Add placeholder images
		if self.eolImgPath is None:
			self.eolImg = ImageTk.PhotoImage(self.resizeImgForDisplay(PLACEHOLDER_IMG))
		elif self.enwikiImgPath is None:
			self.enwikiImg = ImageTk.PhotoImage(self.resizeImgForDisplay(PLACEHOLDER_IMG))
		# Update image-frames
		self.labels[0].config(image=self.eolImg)
		self.labels[1].config(image=self.enwikiImg)
		# Update title
		title = f'Images for otol ID {self.otolId}'
		query = 'SELECT names.alt_name FROM' \
			' nodes INNER JOIN names ON nodes.name = names.name' \
			' WHERE nodes.id = ? and pref_alt = 1'
		row = self.dbCur.execute(query, (self.otolId,)).fetchone()
		if row is not None:
			title += f', aka {row[0]}'
		title += f' ({self.listIdx + 1} out of {len(self.nodeImgsList)})'
		self.root.title(title)
	def accept(self, imgIdx):
		""" React to a user selecting an image """
		imgPath = self.eolImgPath if imgIdx == 0 else self.enwikiImgPath
		if imgPath is None:
			print('Invalid selection')
			return
		with open(self.outFile, 'a') as file:
			file.write(f'{self.otolId} {imgPath}\n')
		self.numReviewed += 1
		self.getNextImgs()
	def reject(self):
		""""" React to a user rejecting all images of a set """
		with open(self.outFile, 'a') as file:
			file.write(f'{self.otolId}\n')
		self.numReviewed += 1
		self.getNextImgs()
	def quit(self, e = None):
		print(f'Number reviewed: {self.numReviewed}')
		timeElapsed = time.time() - self.startTime
		print(f'Time elapsed: {timeElapsed:.2f} seconds')
		if self.numReviewed > 0:
			print(f'Avg time per review: {timeElapsed/self.numReviewed:.2f} seconds')
		self.dbCon.close()
		self.root.destroy()
	def resizeImgForDisplay(self, img):
		""" Returns a copy of an image, shrunk to fit it's frame (keeps aspect ratio), and with a background """
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

def reviewImgs(eolImgDir: str, enwikiImgDir: str, dbFile: str, outFile: str, review: str) -> None:
	print('Opening database')
	dbCon = sqlite3.connect(dbFile)
	dbCur = dbCon.cursor()
	#
	nodeToImgs: dict[str, list[str]] = {} # Maps otol-ids to arrays of image paths
	print('Iterating through images from EOL')
	if os.path.exists(eolImgDir):
		for filename in os.listdir(eolImgDir):
			# Get associated EOL ID
			eolId, _, _ = filename.partition(' ')
			query = 'SELECT nodes.id FROM nodes INNER JOIN eol_ids ON nodes.name = eol_ids.name WHERE eol_ids.id = ?'
			# Get associated node IDs
			found = False
			for (otolId,) in dbCur.execute(query, (int(eolId),)):
				if otolId not in nodeToImgs:
					nodeToImgs[otolId] = []
				nodeToImgs[otolId].append(os.path.join(eolImgDir, filename))
				found = True
			if not found:
				print(f'WARNING: No node found for {os.path.join(eolImgDir, filename)}')
	print(f'Result: {len(nodeToImgs)} nodes with images')
	print('Iterating through images from Wikipedia')
	if os.path.exists(enwikiImgDir):
		for filename in os.listdir(enwikiImgDir):
			# Get associated page ID
			wikiId, _, _ = filename.partition('.')
			# Get associated node IDs
			query = 'SELECT nodes.id FROM nodes INNER JOIN wiki_ids ON nodes.name = wiki_ids.name WHERE wiki_ids.id = ?'
			found = False
			for (otolId,) in dbCur.execute(query, (int(wikiId),)):
				if otolId not in nodeToImgs:
					nodeToImgs[otolId] = []
				nodeToImgs[otolId].append(os.path.join(enwikiImgDir, filename))
				found = True
			if not found:
				print(f'WARNING: No node found for {os.path.join(enwikiImgDir, filename)}')
	print(f'Result: {len(nodeToImgs)} nodes with images')
	#
	print('Filtering out already-made image choices')
	oldSz = len(nodeToImgs)
	if os.path.exists(outFile):
		with open(outFile) as file:
			for line in file:
				line = line.rstrip()
				if ' ' in line:
					line = line[:line.find(' ')]
				del nodeToImgs[line]
	print(f'Filtered out {oldSz - len(nodeToImgs)} entries')
	#
	# Create GUI and defer control
	print('Starting GUI')
	root = tki.Tk()
	ImgReviewer(root, nodeToImgs, eolImgDir, enwikiImgDir, outFile, dbCon, review)
	root.mainloop()
	dbCon.close()

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()
	#
	reviewImgs(EOL_IMG_DIR, ENWIKI_IMG_DIR, DB_FILE, OUT_FILE, REVIEW)
