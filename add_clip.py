# coding=utf-8

# CONFIG
TYPES = ['comp', 'lighting', 'anim', 'source']
DEFAULT_TYPE = 'source'

import os

# You may define a default path to find the .clip file here
# As this is a function, you have access to environment variables.
def getClip():
  raise Exception("No suitable default location")

# Implementation

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from debug import debug
import functools
import uuid
try:
  import lxml.etree as ET
  debug("Using lxml")
except Exception as e:
  from xml.etree import ElementTree as ET
  debug("Using python xml : %s" % e)
import datetime
import string
import pwd
import sys
from identityModel import MyIdentityProxyModel
try:
  import nuke
  nukeImported = True
except:
  nukeImported = False

class DeselectableTableView(QtGui.QTableView):
  def mousePressEvent(self, event):
    self.clearSelection()
    QtGui.QTableView.mousePressEvent(self, event)


class MyComboBox(QtGui.QComboBox):
  currentTextChanged = QtCore.Signal()

  def __init__(self, parent):
    QtGui.QComboBox.__init__(self, parent)
    self.currentText = QtCore.Property(unicode, QtGui.QComboBox.currentText, self.setCurrentText, notify=self.currentTextChanged)
    self.currentIndexChanged.connect(self.currentTextChanged)

  def setCurrentText(text):
    self.setCurrentIndex(self.findText(text))


class OpenClipWindow(QtGui.QWidget):
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.dirty = False
    self.file_changed  = False
    try:
      self.filename = getClip()
    except Exception as e:
      debug(e)
      (self.filename, selectedFilter) = QtGui.QFileDialog.getSaveFileName()
    if self.filename == "":
      QtCore.QTimer.singleShot(0, self, QtCore.SLOT('close()'))
      return
    try:
      xml = ET.parse(self.filename)
      #watcher = QtCore.QFileSystemWatcher([self.filename], self)
      #watcher.fileChanged.connect(self.handleFileChange)
    except Exception as e:
      debug(e)
      root = ET.Element('clip')
      root.attrib['type'] = 'clip'
      root.attrib['version'] = '4'
      tracks = ET.SubElement(root, 'tracks')
      tracks.attrib['type'] = 'tracks'
      versions = ET.SubElement(root, 'versions')
      versions.attrib['type'] = 'versions'
      track = ET.SubElement(tracks, 'track')
      track.attrib['type'] = 'track'
      track.attrib['uid'] = str(uuid.uuid1())
      trackType = ET.SubElement(track, 'trackType')
      trackType.text = 'video'
      feeds = ET.SubElement(track, 'feeds')
      xml = ET.ElementTree(root)
    self.xml_model = OpenClipModel(xml, parent = self)
    QtGui.QVBoxLayout(self)
    #self.xml_model.dataChanged.connect(self.savexml)
    trackNameEdit = QtGui.QLineEdit(self)
    trackNameMapper = QtGui.QDataWidgetMapper(self)
    trackNameMapper.setModel(self.xml_model)
    trackNameMapper.addMapping(trackNameEdit, 1)
    trackIdx = self.xml_model.track_index()
    trackNameMapper.setRootIndex(trackIdx)
    trackNameMapper.setCurrentModelIndex(self.xml_model.track_name_index(trackIdx))
    trackNameMapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
    formWidget = QtGui.QWidget(self)
    form = QtGui.QFormLayout(formWidget)
    self.myTable = DeselectableTableView()
    tableModel = OpenClipFeedsProxyModel(self)
    tableModel.setSourceModel(self.xml_model)
    sortedTableModel = QtGui.QSortFilterProxyModel(self)
    sortedTableModel.setSourceModel(tableModel)
    sortedTableModel.setDynamicSortFilter(True)
    self.myTable.setModel(sortedTableModel)
    self.myTable.setSortingEnabled(True)
    self.myTable.setColumnHidden(5, True)
    self.myTable.setColumnHidden(6, True)
    self.myTree = QtGui.QTreeView(self)
    self.myTree.setModel(self.xml_model)
    ##self.trackNameEdit.setEnabled(False)
    self.versionsCombo = QtGui.QComboBox(self)
    versionsModel = OpenClipVersionProxyModel(self)
    versionsModel.setSourceModel(self.xml_model)
    sortedVersionsModel = QtGui.QSortFilterProxyModel(self)
    sortedVersionsModel.setSourceModel(versionsModel)
    sortedVersionsModel.setDynamicSortFilter(True)
    sortedVersionsModel.sort(0, QtCore.Qt.DescendingOrder)
    self.versionsCombo.setModel(sortedVersionsModel)
    self.versionsCombo.setModelColumn(1)
    self.versionsCombo.currentIndexChanged.connect(self.xml_model.change_version)
    self.xml_model.dataChanged.connect(self.setCurrentVersion)
    self.setCurrentVersion()
    self.addAssetBtn = QtGui.QPushButton("Add Asset", parent = self)
    if not nukeImported:
        self.addAssetBtn.setEnabled(False)
    form.addRow("Track Name", trackNameEdit)
    groupbox = QtGui.QGroupBox("Edit Values", parent = self)
    groupbox.setEnabled(False)

    layout = QtGui.QGridLayout(groupbox)
    layout.addWidget(QtGui.QLabel("Version Name", groupbox), 0, 0)
    layout.addWidget(QtGui.QLineEdit(groupbox), 0, 1)
    layout.addWidget(QtGui.QLabel("Type", groupbox), 0, 2)
    self.typeGroupBox = QtGui.QComboBox(groupbox)
    self.typeGroupBox.addItems(TYPES)
    layout.addWidget(self.typeGroupBox, 0, 3)
    layout.addWidget(QtGui.QLabel("User", groupbox), 1, 0)
    layout.addWidget(QtGui.QLineEdit(groupbox), 1, 1)
    layout.addWidget(QtGui.QLabel("Date", groupbox), 1, 2)
    layout.addWidget(QtGui.QLineEdit(groupbox), 1, 3)
    layout.itemAtPosition(1, 3).widget().setEnabled(False)
    layout.addWidget(QtGui.QLabel("Comment", groupbox), 2, 0, 1, 4)
    layout.addWidget(QtGui.QPlainTextEdit(groupbox), 3, 0, 1, 4)
    layout.addWidget(QtGui.QLabel("Path", groupbox), 4, 0, 1, 4)
    layout.addWidget(QtGui.QLineEdit(groupbox), 5, 0, 1, 3)
    layout.itemAtPosition(5, 0).widget().setReadOnly(True)
    layout.addWidget(QtGui.QPushButton("Read Node", groupbox), 5, 3)

    self.groupBoxMapper = QtGui.QDataWidgetMapper(groupbox)
    self.groupBoxMapper.setModel(tableModel)
    self.groupBoxMapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
    self.groupBoxMapper.addMapping(layout.itemAtPosition(0, 1).widget(), 1)
    # We're handling this one manually...
    #self.groupBoxMapper.addMapping(layout.itemAtPosition(0, 3).widget(), 2)
    layout.itemAtPosition(0, 3).widget().currentIndexChanged.connect(self.change_type)
    self.groupBoxMapper.addMapping(layout.itemAtPosition(1, 1).widget(), 3)
    self.groupBoxMapper.addMapping(layout.itemAtPosition(1, 3).widget(), 4)
    self.groupBoxMapper.addMapping(layout.itemAtPosition(3, 0).widget(), 5)
    self.groupBoxMapper.addMapping(layout.itemAtPosition(5, 0).widget(), 6)
    layout.itemAtPosition(5, 3).widget().clicked.connect(self.createReadNode)
    self.groupBoxMapper.toFirst()
    groupbox.setLayout(layout)
    form.addRow("Selected Version", self.versionsCombo)
    self.layout().addWidget(formWidget)
    self.layout().addWidget(self.addAssetBtn)
    self.layout().addWidget(groupbox)
    self.layout().addWidget(self.myTable)
    self.myTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    self.myTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
    self.myTableSelectionModel = self.myTable.selectionModel()
    self.myTableSelectionModel.selectionChanged.connect(self.changeForm)
    self.addAssetBtn.clicked.connect(self.addAsset)
    saveXmlBtn = QtGui.QPushButton("Save Clip", self)
    self.layout().addWidget(saveXmlBtn)
    saveXmlBtn.clicked.connect(self.savexml)
    self.layout().addWidget(self.myTree)

  def addAsset(self):
    index = self.xml_model.addAsset()
    self.myTable.setCurrentIndex(self.myTable.model().mapFromSource(self.myTable.model().sourceModel().index(index, 1, QtCore.QModelIndex())))

  def change_type(self, index):
    idx = self.groupBoxMapper.currentIndex()
    qidx = self.groupBoxMapper.model().index(idx, 2, QtCore.QModelIndex())
    self.groupBoxMapper.model().setData(qidx, TYPES[index], QtCore.Qt.DisplayRole)

  def setCurrentVersion(self):
    versionsIdx = self.xml_model.sub_idx("versions")
    if 'currentVersion' not in versionsIdx.internalPointer()._inner.attrib:
      return
    uid = versionsIdx.internalPointer()._inner.attrib['currentVersion']
    versionIdx = self.xml_model.sub_idx("version", parent = versionsIdx, dict = { "uid": uid })
    oldstate = self.versionsCombo.blockSignals(True)
    self.versionsCombo.setCurrentIndex(self.xml_model.rowCount(versionsIdx) - 1 - versionIdx.row())
    self.versionsCombo.blockSignals(oldstate)

  @QtCore.Slot(QtGui.QItemSelection, QtGui.QItemSelection)
  def changeForm(self, selected, deselected):
    self.groupBoxMapper.submit()
    if len(selected.indexes()) > 0:
      idx = self.myTable.model().mapToSource(selected.indexes()[0])
      typeIdx = self.myTable.model().index(idx.row(), 2, QtCore.QModelIndex())
      currentType = self.myTable.model().data(typeIdx, QtCore.Qt.DisplayRole)
      self.groupBoxMapper.setCurrentModelIndex(idx)
      self.typeGroupBox.setCurrentIndex(self.typeGroupBox.findText(currentType))
      self.groupBoxMapper.parent().setEnabled(True)
    else:
      self.groupBoxMapper.parent().setEnabled(False)

  def savexml(self):
      debug(self.filename)
      try:
        os.makedirs(os.path.dirname(self.filename))
      except:
        pass
      with open(self.filename, 'w') as f:
        try:
          debug("Writing with lxml")
          self.xml_model._xml.write(f, pretty_print=True)
        except Exception as e:
          debug("Writing with python xml : %s" % e)
          self.xml_model._xml.write(f)

  @QtCore.Slot(str)
  def handleFileChange(self, path):
    if self.dirty:
      return
    if not self.file_changed:
      self.file_changed = True
      if nuke.ask('The clip file has changed outside of nuke. Would you like to load the updated version ?'):
        self._xml = ET.parse(self.filename)
        self.xml_model.dataChanged.emit()
      self.file_changed = False

  def createReadNode(self):
    pathIndex = self.myTable.selectionModel().selectedRows(6)[0]
    path = self.myTable.model().data(pathIndex, QtCore.Qt.DisplayRole)
    frames, padding, startIndex, endIndex = getFramePath(path)
    realPath = frames.format(f = "#" * padding)
    readNode = nuke.nodes.Read(file=realPath)
    readNode['origfirst'].setValue(startIndex)
    readNode['first'].setValue(startIndex)
    readNode['origlast'].setValue(endIndex)
    readNode['last'].setValue(endIndex)

def getFramePath(path):
  try:
    basenameParts = path.split(".")
    framesSpec = basenameParts[-2]
    if framesSpec[0] == "[" and framesSpec[-1] == "]" and len(framesSpec[1:-1].split("-")) == 2:
      frames = framesSpec[1:-1].split("-")
    else:
      frames = [framesSpec, framesSpec]
    padding = len(frames[0])
    frames = map(int, frames)
    basenameParts[-2] = "{f:0>" + str(padding) + "}"
    return ".".join(basenameParts), padding, frames[0], frames[1]
  except Exception as e:
    debug(e)
    return path, 0, 1, 1

class TwoWayDict(dict):
    def __setitem__(self, key, value):
        # Remove any previous connections with these values
        if key in self:
            del self[key]
        if value in self:
            del self[value]
        dict.__setitem__(self, key, value)
        dict.__setitem__(self, value, key)

    def __delitem__(self, key):
        dict.__delitem__(self, self[key])
        dict.__delitem__(self, key)

    def __len__(self):
        """Returns the number of connections"""
        return dict.__len__(self) // 2

class OpenClipFeedsProxyModel(MyIdentityProxyModel):
  def __init__(self, parent = None, *arg):
    QtGui.QAbstractProxyModel.__init__(self, parent, *arg)
    self.cols = TwoWayDict()
    self.cols['ID'] = 0
    self.cols['Name'] = 1
    self.cols['Type'] = 2
    self.cols['User'] = 3
    self.cols['Date'] = 4
    self.cols['Comment'] = 5
    self.cols['Path'] = 6

  def sourceRowsAboutToBeInserted(self, parent, start, end):
    if parent.internalPointer().name == "feeds":
      self.beginInsertRows(self.mapFromSource(parent), start - 1, end - 1)

  def sourceRowsInserted(self, parent, start, end):
    if parent.internalPointer().name == "feeds":
      self.endInsertRows()

  def rowCount(self, parent):
    trackIdx = self.sourceModel().track_index()
    feedsIdx = self.sourceModel().sub_idx("feeds", parent = trackIdx)
    return len(feedsIdx.internalPointer()._inner.findall("./*"))

  def columnCount(self, parent):
    return len(self.cols)

  def index(self, row, count, parent):
    return self.createIndex(row, count)

  # This... is horrible. But it works ¯\_(ツ)_/¯
  # The proper way to do this would be to use the "real" index fn
  # and do the mappings here. I'm lazy though. This will sooooo
  # come and bite me in the ass later.
  def mapFromSource(self, sourceIndex):
    return QtCore.QModelIndex()

  def mapToSource(self, proxyIndex):
    if not proxyIndex.isValid():
      return QtCore.QModelIndex()
    tracksIdx = self.sourceModel().sub_idx("tracks")
    trackIdx = self.sourceModel().sub_idx("track", parent = tracksIdx)
    feedsIdx = self.sourceModel().sub_idx("feeds", parent = trackIdx)
    feedIdx = self.sourceModel().index(proxyIndex.row() + 1, 0, feedsIdx)
    xml = self.sourceModel().root._inner
    if proxyIndex.column() == 0: 
      # Overriding data to add this column, since it does not exist in the
      # original model.
      return QtCore.QModelIndex()
    elif proxyIndex.column() == 1:
      vuid = feedIdx.internalPointer()._inner.attrib['vuid']
      versions = self.sourceModel().sub_idx("versions")
      versionIdx = self.sourceModel().sub_idx("version[@uid='%s']" % vuid, parent = versions)
      version = versionIdx.internalPointer()._inner
      return self.sourceModel().sub_idx("name", parent = versionIdx, col = 1, value = version.attrib['uid'])
    elif proxyIndex.column() == 2:
      userDataIdx = self.sourceModel().sub_idx("userData", parent = feedIdx, dict = { 'type': 'dict' })
      return self.sourceModel().sub_idx("shotType", parent = userDataIdx, col = 1, dict = { 'type': 'string' }, value = DEFAULT_TYPE)
    elif proxyIndex.column() == 3:
      #return self.parent().getUser(proxyIndex)
      userDataIdx = self.sourceModel().sub_idx("userData", parent = feedIdx, dict = { 'type': 'dict' })
      try:
        formattedPath = feedIdx.internalPointer()._inner.find(".//path").text
        path, padding, startFrame, endFrame = getFramePath(formattedPath)
        stat = os.stat(path.format(f = str(startFrame)))
        text = pwd.getpwuid(stat.st_uid).pw_name
      except Exception as e:
        debug(e)
        text = "unknown"
      return self.sourceModel().sub_idx("user", parent = userDataIdx, col = 1, dict = { 'type': 'string' }, value = text)
    elif proxyIndex.column() == 4:
      vuid = feedIdx.internalPointer()._inner.attrib['vuid']
      versions = self.sourceModel().sub_idx("versions")
      version = self.sourceModel().sub_idx("version[@uid='%s']" % vuid, parent = versions)
      return self.sourceModel().sub_idx("creationDate", parent = version, col = 1)
    elif proxyIndex.column() == 5:
      try:
        return self.sourceModel().sub_idx("comment", parent = feedIdx, col = 1)
      except:
        feed = feedIdx.internalPointer()._inner
        index = len(feed.findall("./*")) + 1
        self.sourceModel().beginInsertRows(feedIdx, index, index)
        ET.SubElement(feed, "comment")
        self.sourceModel().endInsertRows()
        return QtCore.QModelIndex()
    elif proxyIndex.column() == 6:
      spansIdx = self.sourceModel().sub_idx("spans", parent = feedIdx)
      spanIdx = self.sourceModel().sub_idx("span", parent = spansIdx)
      if spanIdx.internalPointer()._inner.find("path") is None:
        pathsIdx = self.sourceModel().sub_idx("paths", parent = spanIdx)
        return self.sourceModel().sub_idx("path", parent = pathsIdx, col = 1)
      else:
        return self.sourceModel().sub_idx("path", parent = spanIdx, col = 1)
    else:
      return QtCore.QModelIndex()

  def data(self, index, role):
    if index.isValid() and index.column() == 0 and (role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole):
      return index.row()
    return MyIdentityProxyModel.data(self, index, role)

  def headerData(self, section, orientation, role):
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      return self.cols.get(section, None)
    return None
 
  def parent(self, child):
    return QtCore.QModelIndex()

class OpenClipVersionProxyModel(MyIdentityProxyModel):
  def __init__(self, parent = None):
    MyIdentityProxyModel.__init__(self, parent)

  def sourceRowsAboutToBeInserted(self, parent, start, end):
    if parent.internalPointer().name == "versions":
      debug("sourceRowsAboutToBeInserted : %d,%d" % (start - 1, end - 1))
      self.beginInsertRows(self.mapFromSource(parent), start - 1, end - 1)

  def sourceRowsInserted(self, parent, start, end):
    if parent.internalPointer().name == "versions":
      self.endInsertRows()
  
  def rowCount(self, parent):
    return self.sourceModel().rowCount(self.sourceModel().sub_idx("versions")) - 1

  def index(self, row, column, parent):
    assert parent.model() == self if parent.isValid() else True
    if not parent.isValid():
      sourceParent = self.sourceModel().sub_idx("versions")
    else:
      sourceParent = self.mapToSource(parent)
    sourceIndex = self.sourceModel().index(row + 1, column, sourceParent)
    return self.mapFromSource(sourceIndex)
    

  def columnCount(self, parent):
    return 2
 
  def mapFromSource(self, sourceIndex):
    if not sourceIndex.isValid():
      return QtCore.QModelIndex()
    if sourceIndex.internalPointer().name != "version":
      return QtCore.QModelIndex()
    return self.createIndex(sourceIndex.row() - 1, sourceIndex.column(), sourceIndex.internalPointer())

  def mapToSource(self, proxyIndex):
    if not proxyIndex.isValid():
      return QtCore.QModelIndex()
      #return self.sourceModel().sub_idx("versions")
    versionsIdx = self.sourceModel().sub_idx("versions")
    versionIdx = self.sourceModel().index(proxyIndex.row() + 1, 0, versionsIdx)
    if versionIdx.internalPointer()._inner.find("name") is None:
      self.sourceModel().beginInsertRows(versionIdx, self.sourceModel().rowCount(versionIdx), self.sourceModel().rowCount(versionIdx))
      name = ET.SubElement(versionIdx.internalPointer()._inner, "name")
      name.text = versionIdx.internalPointer()._inner.attrib['uid']
      self.sourceModel().endInsertRows()
      return QtCore.QModelIndex()
    else:
      return self.sourceModel().sub_idx("name", versionIdx, 1)
      
    return self.sourceModel().sub_idx("name", versionIdx, 1)

  def data(self, index, role):
    if index.isValid() and index.column() == 0 and (role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole):
      return index.row()
    debug("data : %s[%d,%d]" % (index.internalPointer(), index.row(), index.column()))
    return debug(MyIdentityProxyModel.data(self, index, role))
  def parent(self, child):
    return QtCore.QModelIndex()
 

class OpenClipModelItem(object): 
  def __init__(self, row, type, parent):
    self.row = row
    self.type = type
    self.parent = parent
    self.child_cache = []

  @property
  def name(self):
    if self.type == "tag":
      return self._inner.tag
    elif self.type == "attribute_list":
      return "#attr"
    elif self.type == "attribute_item":
      return self._inner['name']
    else:
      return None

  @property
  def value(self):
    if self.type == "tag":
      return self._inner.text if self._inner.text is not None else ""
    elif self.type == "attribute_list":
      return ""
    elif self.type == "attribute_item":
      return self._inner['dict'][self._inner['name']]
    else:
      return None

  @value.setter
  def value(self, value):
    if self.type == "tag":
      self._inner.text = value
    elif self.type == "attribute_item":
      self._inner['dict'][self._inner['name']] = value
    else:
      pass

  @staticmethod
  def tag(elem, row, parent = None):
    item = OpenClipModelItem(row, "tag", parent)
    item._inner = elem
    return item

  @staticmethod
  def attr_root(items, parent):
    item = OpenClipModelItem(0, "attribute_list", parent)
    item._inner = items
    return item

  @staticmethod
  def attr_item((name, value), row, parent):
    item = OpenClipModelItem(row, "attribute_item", parent)
    item._inner = { "dict": parent._inner, "name": name }
    return item

  def child(self, row):
    if row >= len(self.child_cache):
      self.child_cache.extend([None] * (row + 1 + len(self.child_cache)))
    if self.child_cache[row] is None:
      if self.type == "tag" and row == 0:
        self.child_cache[row] = self.attr_root(self._inner.attrib, self)
      elif self.type == "tag" and row - 1 < len(self._inner.findall("./*")):
        self.child_cache[row] = self.tag(self._inner.findall("./*")[row - 1], row, self)
      elif self.type == "attribute_list" and row < len(self._inner.items()):
        self.child_cache[row] = self.attr_item(self._inner.items()[row], row, self)
      else:
        return None
    return self.child_cache[row]

  def child_count(self):
    if self.type == "tag":
      return len(self._inner.findall("./*")) + 1
    elif self.type == "attribute_list":
      return len(self._inner.items())
    else:
      return 0

  def __repr__(self):
    type = self.type if hasattr(self, 'type') else 'None'
    name = self.name if hasattr(self, 'name') else 'None'
    value = self.value if hasattr(self, 'value') else 'None'
    row = self.row if hasattr(self, 'row') else -500
    return "<%s type:%s, name:%s, value:%s, row:%d>" % ("OpenClipModelItem", type, name, value, row)

class OpenClipModel(QtCore.QAbstractItemModel):
  def __init__(self, xml, parent = None, *args):
    QtCore.QAbstractItemModel.__init__(self, parent, *args)
    self._xml = xml
    self.root = OpenClipModelItem.tag(self._xml.getroot(), 0, None)
    self.cols = TwoWayDict()
    self.cols['Name'] = 0
    self.cols['Value'] = 1

  def columnCount(self, parent):
    return len(self.cols)

  def rowCount(self, parent):
    if parent.column() > 0:
      return 0
    if not parent.isValid():
      parentItem = self.root
    else:
      parentItem = parent.internalPointer()
    return parentItem.child_count()

  def data(self, index, role):
    if not index.isValid():
      return None
    if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
      return None
    item = index.internalPointer()
    if index.column() == 0:
      return item.name
    elif index.column() == 1:
      return item.value
    else:
      return None

  def setData(self, index, value, role):
    if not index.isValid():
      return False
    # check role
    item = index.internalPointer()
    if index.column() == 1:
      item.value = value
    else:
      return False
    self.dataChanged.emit(index, index)
    return True

  def flags(self, index):
    if not index.isValid():
      return QtCore.Qt.NoItemFlags
    return QtCore.QAbstractItemModel.flags(self, index)

  def headerData(self, section, orientation, role):
    if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
      return self.cols.get(section, None)
    return None

  def index(self, row, column, parent):
    if not self.hasIndex(row, column, parent):
      return QtCore.QModelIndex()
    if not parent.isValid():
      parentItem = self.root
    else:
      parentItem = parent.internalPointer()
    childItem = parentItem.child(row)
    if childItem is not None:
      return self.createIndex(row, column, childItem)
    else:
      return QtCore.QModelIndex()

  def parent(self, child):
    if not child.isValid():
      return QtCore.QModelIndex()
    childItem = child.internalPointer()
    
    parentItem = childItem.parent
    if parentItem is None or parentItem == self.root:
      return QtCore.QModelIndex()
    return self.createIndex(parentItem.row, 0, parentItem)

  def track_index(self):
    tracks = self.root._inner.find("tracks")
    row = self.root._inner.findall("./*").index(tracks) + 1
    idx = self.index(row, 0, QtCore.QModelIndex())
    debug(tracks.findall("./*"))
    row = tracks.findall("./*").index(tracks.find("track")) + 1
    return self.index(row, 0, idx)

  def track_name_index(self, trackIdx):
    if not trackIdx.isValid():
      return QtCore.QModelIndex()
    track = trackIdx.internalPointer()._inner
    if track.find("name") is not None:
      row = track.findall("./*").index(track.find("name")) + 1
      return self.index(row, 0, trackIdx)
    else:
      return QtCore.QModelIndex()

  def sub_idx(self, childName, parent = QtCore.QModelIndex(), col = 0, dict = {}, value = None):
    ptr = parent.internalPointer() if parent.isValid() else self.root
    if ptr.type == "tag" and childName == "#attr":
      return self.index(0, col, parent)
    elif ptr.type == "tag":
      childAt = childName
      for k, v in dict.items():
        childAt += "[@%s='%s']" % (k, v)
      if ptr._inner.find(childAt) is None:
        self.beginInsertRows(parent, len(ptr._inner.findall("./*")) + 1, len(ptr._inner.findall("./*")) + 1)
        c = ET.SubElement(ptr._inner, childName)
        for k, v in dict.items():
          c.attrib[k] = v
        c.text = value
      return self.index(ptr._inner.findall("./*").index(ptr._inner.find(childAt)) + 1, col, parent)
    elif ptr.type == "attribute_list":
      i = 0
      for (k, v) in ptr._inner.items():
        if k == childName:
          return self.index(i, col, parent)
        else:
          i += 1
      import traceback
      debug("creating index in sub_idx : %s, %s, %s, %s, %s\n%s" % (childName, parent, i, col, dict, value, ''.join(traceback.format_stack())))
      self.beginInsertRows(parent, len(ptr._inner), len(ptr._inner))
      ptr._inner[childName] = value
      self.endInsertRows()
      return self.index(i, col, parent)
    else:
      return QtCore.QModelIndex()

  def addAsset(self):
    node = nuke.selectedNode()
    if node.Class() != "Read":
      return
    track = self._xml.find("tracks/track")
    vuid = str(uuid.uuid1())
    pathValArr = node['file'].value().split('%')
    if len(pathValArr) > 1:
      i = 0
      while pathValArr[1][i].isdigit():
        i += 1
      padLen = int(pathValArr[1][:i])
      pathValArr[1] = '[' + str(node['origfirst'].value()).zfill(padLen) + '-' + str(node['origlast'].value()).zfill(padLen) + ']' + pathValArr[1][pathValArr[1].index('d') + 1:]
    pathVal = ''.join(pathValArr)
    versionNameArr = os.path.basename(pathVal).split(".")[:-1]
    if len(versionNameArr) > 0 and isFormat(versionNameArr[-1]):
      versionNameArr = versionNameArr[:-1]
    versionsIdx = self.sub_idx("versions")
    index = self.rowCount(versionsIdx)
    self.beginInsertRows(versionsIdx, index, index)
    createVersionTag(self._xml.find("versions"), vuid, ".".join(versionNameArr))
    self.endInsertRows()
    feedsIdx = self.sub_idx("feeds", parent = self.track_index())
    index = self.rowCount(feedsIdx)
    self.beginInsertRows(feedsIdx, index, index)
    feed = ET.SubElement(track.find("feeds"), "feed")
    feed.attrib["type"] = "feed"
    feed.attrib["vuid"] = vuid
    feed.attrib["uid"] = str(uuid.uuid1())
    spans = ET.SubElement(feed, "spans")
    spans.attrib["type"] = "spans"
    spans.attrib["version"] = "4"
    span = ET.SubElement(spans, "span")
    span.attrib["type"] = "span"
    span.attrib["version"] = "4"
    path = ET.SubElement(span, "path")
    path.text = pathVal
    self.endInsertRows()
    return index - 1

  @QtCore.Slot(int)
  def change_version(self, idx):
    trackIdx = self.track_index()
    track = trackIdx.internalPointer()._inner
    feedsIdx = self.sub_idx("feeds", parent = trackIdx)
    fattrIdx = self.sub_idx("#attr", parent = feedsIdx)
    fattr0 = self.sub_idx("currentVersion", parent = fattrIdx, col = 0)
    fattr1 = self.sub_idx("currentVersion", parent = fattrIdx, col = 1)
    versionsIdx = self.sub_idx("versions")
    versions = versionsIdx.internalPointer()._inner
    if len(versions.findall("./*")) == 0:
      return
    version = versions.findall("./*")[len(versions.findall("./*")) - 1 - idx]
    vattrIdx = self.sub_idx("#attr", parent = versionsIdx)
    vattr0 = self.sub_idx("currentVersion", parent = vattrIdx, col = 0)
    vattr1 = self.sub_idx("currentVersion", parent = vattrIdx, col = 1)
    fattr0.internalPointer().value = debug(version.attrib['uid'])
    vattr0.internalPointer().value = version.attrib['uid']
    self.dataChanged.emit(vattr0, vattr1)
    self.dataChanged.emit(fattr0, fattr1)

def createVersionTag(versions, vuid, versionName):
  version = ET.SubElement(versions, "version")
  version.attrib["type"] = "version"
  version.attrib["version"] = "3"
  version.attrib["uid"] = vuid
  nameTag = ET.SubElement(version, "name")
  nameTag.text = versionName
  creationDate = ET.SubElement(version, "creationDate")
  creationDate.text = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
  comment = ET.SubElement(version, "comment")
  comment.text = "AutoGenerated from nuke"
  return version

def isFormat(s):
  try:
    if s[0] == '%' and s[-1] == 'd':
      x = int(s[1:-1])
      return True
    else:
      return False
  except:
    return False

def start():
  app = QtGui.QApplication([])
  wnd = OpenClipWindow()
  wnd.show()
  sys.exit(app.exec_())

if __name__ == "__main__":
  start()

def myinit():
  try:
    from nukescripts import panels
    panels.registerWidgetAsPanel('__import__("add_clip").OpenClipWindow', 'Open Clip', 'im.cmc.OpenClipWindow')
  except:
    debug("Couldn't register panel")
