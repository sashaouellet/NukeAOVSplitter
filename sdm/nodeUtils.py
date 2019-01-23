import nuke
from sdm import UI_DIR

def reloadReads():
	nodes = nuke.selectedNodes()
	nodes = [n for n in nodes if n.Class() == 'Read']

	nodes = nuke.allNodes() if not nodes else nodes

	for n in nodes:
		if n.Class() == 'Read':
			n.knob('reload').execute()

def readSelected():
	node = None

	try:
		node = nuke.selectedNode()
	except ValueError:
		nuke.warning('Please select a node')
		return

	if not node:
		nuke.warning('Please select a node')
		return

	if node.Class() != 'Write':
		nuke.warning('Must select a Write node')
		return

	fp = node.knob('file').getValue()
	read = nuke.nodes.Read()

	read.knob('file').setValue(fp)

	nuke.activeViewer().node().setInput(0, read)

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import os, random, itertools

def findUpstreamShuffle(node):
	while node.Class() != 'Shuffle':
		up = node.input(0)

		print up.name()

		if not up:
			raise ValueError('No read node upstream')

		return findUpstreamShuffle(up)

	return node

def connectWithDot(n1, n2):
    dot = nuke.nodes.Dot()
    dot.setInput(0, n1)
    n2.setInput(0, dot)

    dot.setXYpos(dot.xpos(), n2.ypos() + n2.screenHeight() / 2 - dot.screenHeight() / 2)

class UiLoader(QUiLoader):
    """Custom UI loader to apply created widgets directly to "baseinstance"

    This is supposed to emulate the behavior of uic
    """

    def __init__(self, baseinstance, customWidgets=None):
        super(UiLoader, self).__init__(baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

    def createWidget(self, class_name, parent=None, name=''):
        """Function that is called for each widget defined in ui file,
        overridden here to populate baseinstance instead.
        """

        if parent is None and self.baseinstance:
            # supposed to create the top-level widget, return the base instance
            # instead
            return self.baseinstance
        else:
            if class_name in self.availableWidgets():
                # create a new widget for child widgets
                widget = QUiLoader.createWidget(self, class_name, parent, name)
            else:
                # if not in the list of availableWidgets, must be a custom widget
                # this will raise KeyError if the user has not supplied the
                # relevant class_name in the dictionary, or TypeError, if
                # customWidgets is None
                try:
                    widget = self.customWidgets[class_name](parent)
                except (TypeError, KeyError) as e:
                    raise Exception('No custom widget ' + class_name + ' found in customWidgets param of UiLoader __init__.')

            if self.baseinstance:
                # set an attribute for the new child widget on the base
                # instance, just like PyQt4.uic.loadUi does.
                setattr(self.baseinstance, name, widget)

            return widget

class AOVModel(QAbstractListModel):
	def __init__(self, parent, aovs=[]):
		super(AOVModel, self).__init__(parent)

		self.setAOVs(aovs)

	def setAOVs(self, aovs):
		self.beginResetModel()
		self.aovs = aovs
		self.endResetModel()

	def removeAov(self, aov):
		if aov in self.aovs:
			self.beginResetModel()
			self.aovs.remove(aov)
			self.endResetModel()

	def addAov(self, aov):
		if aov not in self.aovs:
			self.beginResetModel()
			self.aovs.append(aov)
			self.endResetModel()

	def rowCount(self, index=QModelIndex()):
		return len(self.aovs)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if role == Qt.DisplayRole:
			return self.aovs[index.row()]

		return None

class AOVSplitterDialog(QDialog):
	IGNORE = ['rgba']

	def __init__(self, read, parent=None):
		super(AOVSplitterDialog, self).__init__(parent)

		self.read = read

		self.aovs = self.getAllAovs()
		self.aovChecks = []

		loader = UiLoader(self)
		loader.load(QFile(os.path.join(UI_DIR, 'aovSplitter.ui')))

		self.initUI()
		self.makeConnections()

	def getAllAovs(self):
		aovs = list(set([c.split('.')[0] for c in self.read.channels()]))
		aovs = filter(lambda x: x.lower() not in AOVSplitterDialog.IGNORE, aovs)

		aovs.sort(key=lambda x: x.lower())

		return aovs

	def handleChecked(self, state, aov=None):
		checked = state == Qt.Checked
		print checked, aov

		if checked:
			self.model.addAov(aov)
		else:
			self.model.removeAov(aov)

	def populateAovList(self, aovs):
		for aov in aovs:
			chk = QCheckBox(aov)
			chk.setChecked(True)
			self.LAY_aovs.addWidget(chk)
			self.aovChecks.append(chk)

			# chk.stateChanged.connect(lambda: self.handleChecked(aov=aov))

		self.LAY_aovs.invalidate()
		self.LAY_aovs.activate()
		self.LAY_aovs.update()

	def handleReorder(self, up):
		indexes = self.LST_order.selectedIndexes()

		if indexes:
			index = indexes[0]
			delta = -1 if up else 1
			newRow = min(max(index.row() + delta, 0), self.model.rowCount() - 1)

			tmp = self.model.aovs[newRow]
			self.model.aovs[newRow] = self.model.aovs[index.row()]
			self.model.aovs[index.row()] = tmp

			self.model.setAOVs(self.model.aovs)
			self.LST_order.selectionModel().select(self.model.index(newRow), QItemSelectionModel.Select)

	def initUI(self):
		self.LBL_split.setText('Splitting: {} ({})'.format(self.read.knob('file').value(), self.read.name()))

		if not self.aovs:
			nuke.message('No AOVs found')
			self.BTN_split.setEnabled(False)

		self.populateAovList(self.aovs)

		self.model = AOVModel(parent=self, aovs=self.aovs)

		self.LST_order.setModel(self.model)
		self.LST_order.setSelectionMode(QAbstractItemView.SingleSelection)

		self.GRP_order.setVisible(False)

	def makeConnections(self):
		self.BTN_cancel.clicked.connect(self.reject)
		self.BTN_split.clicked.connect(self.accept)
		self.BTN_up.clicked.connect(lambda: self.handleReorder(True))
		self.BTN_down.clicked.connect(lambda: self.handleReorder(False))

	def accept(self):
		self.split()
		super(AOVSplitterDialog, self).accept()

	def backdropNodes(self, nodes, label, bufferY=0):
		# Calculate bounds for the backdrop node
		bdX = min([node.xpos() for node in nodes])
		bdY = min([node.ypos() for node in nodes])
		bdW = max([node.xpos() + node.screenWidth() for node in nodes]) - bdX
		bdH = max([node.ypos() + node.screenHeight() for node in nodes]) - bdY

		# Expand the bounds to leave a little border. Elements are offsets for left, top, right and bottom edges respectively
		left, top, right, bottom = (-10, -80, 10, 10 + bufferY)
		bdX += left
		bdY += top
		bdW += (right - left)
		bdH += (bottom - top)

		n = nuke.nodes.BackdropNode(
			xpos = bdX,
			bdwidth = bdW,
			ypos = bdY,
			bdheight = bdH,
			tile_color = int((random.random() * (16 - 10))) + 10,
			note_font_size=42,
			label=label
		)

	def moveNode(self, node, x=0, y=0):
		node.setXYpos(node.xpos() + x, node.ypos() + y)

	def split(self):
		outputGroups = {}
		outputs = []
		dots = []

		for aovCheck in self.aovChecks:
			aov = str(aovCheck.text())

			if not aovCheck.isChecked():
				continue

			out = nuke.nodes.Shuffle(name=aov)

			out.knob('in').setValue(aov)
			out.knob('postage_stamp').setValue(self.CHK_postage.isChecked())

			# In between per-aov adjustment nodes
			if self.CHK_denoise.isChecked():
				denoise = nuke.nodes.Denoise()

				denoise.setInput(0, out)

				out = denoise

			if self.CHK_grade.isChecked():
				grade = nuke.nodes.Grade()

				grade.setInput(0, out)

				out = grade

			if self.CHK_colorCorrect.isChecked():
				cc = nuke.nodes.ColorCorrect()

				cc.setInput(0, out)

				out = cc

			aovOutputs = outputGroups.get(aov.split('_')[0], [])
			aovOutputs.append(out)
			outputGroups[aov.split('_')[0]] = aovOutputs

		allOuts = list(itertools.chain.from_iterable(outputGroups.values()))

		for outputs in outputGroups.values():
			for o in outputs:
				shuffle = findUpstreamShuffle(o)
				dot = nuke.nodes.Dot()

				shuffle.setInput(0, dot)
				dots.append(dot)

		if self.CHK_merge.isChecked() and len(allOuts) >= 2:
			finalMerges = []

			for aov, outputs in outputGroups.iteritems():
				originalOutputs = outputs[:]
				out1 = outputs.pop()
				out2 = None

				if outputs:
					out2 = outputs.pop()
				else:
					self.backdropNodes(originalOutputs + [findUpstreamShuffle(originalOutputs[0])], aov, bufferY=100)
					finalMerges.append(originalOutputs[0])
					continue

				merge = nuke.nodes.Merge(name='merge_{}'.format(aov))

				merge.knob('operation').setValue('plus')

				merge.setInput(0, out1)
				merge.setInput(1, out2)

				while outputs:
					newMerge = nuke.nodes.Merge()

					newMerge.knob('operation').setValue('plus')

					newMerge.setInput(0, merge)
					newMerge.setInput(1, outputs.pop())

					merge = newMerge

				self.backdropNodes([findUpstreamShuffle(o) for o in originalOutputs] + [merge], aov, bufferY=100)
				finalMerges.append(merge)

			if finalMerges:
				conn1 = finalMerges.pop()

				while finalMerges:
					conn2 = finalMerges.pop()
					merge = nuke.nodes.Merge()
					merge.knob('operation').setValue('plus')

					merge.setInput(0, conn1)
					merge.setInput(1, conn2)

					conn1 = merge

				for i, dot in enumerate(dots):
					self.moveNode(dot, y=-100)

					if i == 0:
						dot.setInput(0, self.read)
					else:
						dot.setInput(0, dots[i - 1])

				# 34 is "half" node width
				self.read.setXYpos(dots[0].xpos() - 34, dots[0].ypos() - 200)

				nuke.activeViewer().node().setInput(0, conn1)

def splitAOVs():
	node = None

	try:
		node = nuke.selectedNode()
	except ValueError:
		nuke.warning('Please select a node')
		return


	if not node:
		nuke.warning('Please select a node')
		return

	if node.Class() != 'Read':
		nuke.warning('Must select a Read node')
		return

	dialog = AOVSplitterDialog(node)

	ret = dialog.exec_()

	return

	if ret != QDialog.Accepted:
		return

	channels = list(set([c.split('.')[0] for c in node.channels()]))
	ignore = ['rgba']
	shuffles = []

	for ch in channels:
		if ch in ignore:
			continue

		shuffle = nuke.nodes.Shuffle(name=ch)

		shuffle.knob('in').setValue(ch)
		shuffle.knob('postage_stamp').setValue(True)
		shuffle.setInput(0, node)

		shuffles.append(shuffle)

	return # TODO re-implement plus merging

	if shuffles and len(shuffles) >= 2:
		shuf1 = shuffles.pop()
		shuf2 = shuffles.pop()
		merge = nuke.nodes.Merge()

		merge.knob('operation').setValue('plus')

		merge.setInput(0, shuf1)
		merge.setInput(1, shuf2)

		while shuffles:
			newMerge = nuke.nodes.Merge()

			newMerge.knob('operation').setValue('plus')

			newMerge.setInput(0, merge)
			newMerge.setInput(1, shuffles.pop())

			merge = newMerge

		nuke.activeViewer().node().setInput(0, merge)