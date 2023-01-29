#!/usr/bin/python3

"""
Provides a GUI for reviewing images. Looks in a for-review directory for
images named 'eolId1 contentId1.ext1', and, for each EOL ID, enables the user to
choose an image to keep, or reject all. Also provides image rotation.
Chosen images are placed in another directory, and rejected ones are deleted.
"""

import argparse
import sys
import re
import os
import time
import sqlite3

import tkinter as tki
from tkinter import ttk
import PIL
from PIL import ImageTk, Image, ImageOps

IMG_DIR = 'imgs_for_review'
OUT_DIR = 'imgs'
EXTRA_INFO_DB = os.path.join('..', 'data.db')

IMG_DISPLAY_SZ = 400
MAX_IMGS_PER_ID = 3
IMG_BG_COLOR = (88, 28, 135)
PLACEHOLDER_IMG = Image.new('RGB', (IMG_DISPLAY_SZ, IMG_DISPLAY_SZ), IMG_BG_COLOR)

class EolImgReviewer:
	""" Provides the GUI for reviewing images """
	def __init__(self, root, imgDir, imgList, extraInfoDb, outDir):
		self.root = root
		root.title('EOL Image Reviewer')

		# Setup main frame
		mainFrame = ttk.Frame(root, padding='5 5 5 5')
		mainFrame.grid(column=0, row=0, sticky=(tki.N, tki.W, tki.E, tki.S))
		root.columnconfigure(0, weight=1)
		root.rowconfigure(0, weight=1)

		# Set up images-to-be-reviewed frames
		self.imgs = [PLACEHOLDER_IMG] * MAX_IMGS_PER_ID # Stored as fields for use in rotation
		self.photoImgs = list(map(lambda img: ImageTk.PhotoImage(img), self.imgs)) # Image objects usable by tkinter
			# These need a persistent reference for some reason (doesn't display otherwise)
		self.labels: list[ttk.Label] = []
		for i in range(MAX_IMGS_PER_ID):
			frame = ttk.Frame(mainFrame, width=IMG_DISPLAY_SZ, height=IMG_DISPLAY_SZ)
			frame.grid(column=i, row=0)
			label = ttk.Label(frame, image=self.photoImgs[i])
			label.grid(column=0, row=0)
			self.labels.append(label)

		# Add padding
		for child in mainFrame.winfo_children():
			child.grid_configure(padx=5, pady=5)

		# Add keyboard bindings
		root.bind('<q>', self.quit)
		root.bind('<Key-j>', lambda evt: self.accept(0))
		root.bind('<Key-k>', lambda evt: self.accept(1))
		root.bind('<Key-l>', lambda evt: self.accept(2))
		root.bind('<Key-i>', lambda evt: self.reject())
		root.bind('<Key-a>', lambda evt: self.rotate(0))
		root.bind('<Key-s>', lambda evt: self.rotate(1))
		root.bind('<Key-d>', lambda evt: self.rotate(2))
		root.bind('<Key-A>', lambda evt: self.rotate(0, True))
		root.bind('<Key-S>', lambda evt: self.rotate(1, True))
		root.bind('<Key-D>', lambda evt: self.rotate(2, True))

		# Initialise fields
		self.imgDir = imgDir
		self.imgList = imgList
		self.outDir = outDir
		self.imgListIdx = 0
		self.nextEolId = 0
		self.nextImgNames: list[str] = []
		self.rotations: list[int] = []

		# For displaying extra info
		self.extraInfoDbCon = sqlite3.connect(extraInfoDb)
		self.extraInfoDbCur = self.extraInfoDbCon.cursor()
		self.numReviewed = 0
		self.startTime = time.time()

		self.getNextImgs()

	def getNextImgs(self):
		""" Updates display with new images to review, or ends program """
		# Gather names of next images to review
		for i in range(MAX_IMGS_PER_ID):
			if self.imgListIdx == len(self.imgList):
				if i == 0:
					self.quit()
					return
				break
			imgName = self.imgList[self.imgListIdx]
			eolId = int(re.match(r'(\d+) (\d+)', imgName).group(1))
			if i == 0:
				self.nextEolId = eolId
				self.nextImgNames = [imgName]
				self.rotations = [0]
			else:
				if self.nextEolId != eolId:
					break
				self.nextImgNames.append(imgName)
				self.rotations.append(0)
			self.imgListIdx += 1

		# Update displayed images
		idx = 0
		while idx < MAX_IMGS_PER_ID:
			if idx < len(self.nextImgNames):
				try:
					img = Image.open(os.path.join(self.imgDir, self.nextImgNames[idx]))
					img = ImageOps.exif_transpose(img)
				except PIL.UnidentifiedImageError:
					os.remove(os.path.join(self.imgDir, self.nextImgNames[idx]))
					del self.nextImgNames[idx]
					del self.rotations[idx]
					continue
				self.imgs[idx] = self.resizeImgForDisplay(img)
			else:
				self.imgs[idx] = PLACEHOLDER_IMG
			self.photoImgs[idx] = ImageTk.PhotoImage(self.imgs[idx])
			self.labels[idx].config(image=self.photoImgs[idx])
			idx += 1

		# Restart if all image files non-recognisable
		if not self.nextImgNames:
			self.getNextImgs()
			return

		# Update title
		firstImgIdx = self.imgListIdx - len(self.nextImgNames) + 1
		lastImgIdx = self.imgListIdx
		title = self.getExtraInfo(self.nextEolId)
		title += f' (imgs {firstImgIdx} to {lastImgIdx} out of {len(self.imgList)})'
		self.root.title(title)

	def accept(self, imgIdx):
		""" React to a user selecting an image """
		if imgIdx >= len(self.nextImgNames):
			print('Invalid selection')
			return
		for i in range(len(self.nextImgNames)):
			inFile = os.path.join(self.imgDir, self.nextImgNames[i])
			if i == imgIdx: # Move accepted image, rotating if needed
				outFile = os.path.join(self.outDir, self.nextImgNames[i])
				img = Image.open(inFile)
				img = ImageOps.exif_transpose(img)
				if self.rotations[i] != 0:
					img = img.rotate(self.rotations[i], expand=True)
				img.save(outFile)
				os.remove(inFile)
			else: # Delete non-accepted image
				os.remove(inFile)
		self.numReviewed += 1
		self.getNextImgs()

	def reject(self):
		""" React to a user rejecting all images of a set """
		for i in range(len(self.nextImgNames)):
			os.remove(os.path.join(self.imgDir, self.nextImgNames[i]))
		self.numReviewed += 1
		self.getNextImgs()

	def rotate(self, imgIdx, anticlockwise = False):
		""" Respond to a user rotating an image """
		deg = -90 if not anticlockwise else 90
		self.imgs[imgIdx] = self.imgs[imgIdx].rotate(deg)
		self.photoImgs[imgIdx] = ImageTk.PhotoImage(self.imgs[imgIdx])
		self.labels[imgIdx].config(image=self.photoImgs[imgIdx])
		self.rotations[imgIdx] = (self.rotations[imgIdx] + deg) % 360

	def quit(self, e = None):
		print(f'Number reviewed: {self.numReviewed}')
		timeElapsed = time.time() - self.startTime
		print(f'Time elapsed: {timeElapsed:.2f} seconds')
		if self.numReviewed > 0:
			print(f'Avg time per review: {timeElapsed/self.numReviewed:.2f} seconds')
		self.extraInfoDbCon.close()
		self.root.destroy()

	def resizeImgForDisplay(self, img):
		""" Returns a copy of an image, shrunk to fit in it's frame (keeps aspect ratio), and with a background """
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

	def getExtraInfo(self, eolId: int) -> str:
		""" Used to display extra EOL ID info """
		query = 'SELECT names.alt_name FROM' \
			' names INNER JOIN eol_ids ON eol_ids.name = names.name' \
			' WHERE id = ? and pref_alt = 1'
		row = self.extraInfoDbCur.execute(query, (eolId,)).fetchone()
		if row is not None:
			return f'Reviewing EOL ID {eolId}, aka "{row[0]}"'
		else:
			return f'Reviewing EOL ID {eolId}'

def reviewImgs(imgDir: str, outDir: str, extraInfoDb: str):
	print('Checking output directory')
	if not os.path.exists(outDir):
		os.mkdir(outDir)

	print('Getting input image list')
	imgList = os.listdir(imgDir)
	imgList.sort(key=lambda s: int(s.split(' ')[0]))
	if not imgList:
		print('No input images found')
		sys.exit(0)

	# Create GUI and defer control
	print('Starting GUI')
	root = tki.Tk()
	EolImgReviewer(root, imgDir, imgList, extraInfoDb, outDir)
	root.mainloop()

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.parse_args()

	reviewImgs(IMG_DIR, OUT_DIR, EXTRA_INFO_DB)
