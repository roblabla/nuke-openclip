import PySide.QtCore as QtCore
import PySide.QtGui as QtGui

import datetime

try:
  import nuke
  def debug(x):
    nuke.debug("%s: %s" % (datetime.datetime.now().strftime("%H:%M:%S.%f"), str(x)))
    return x
except:
  def debug(x):
    print("%s: %s" % (datetime.datetime.now().strftime("%H:%M:%S.%f"), str(x)))
    return x



class MyIdentityProxyModel(QtGui.QAbstractProxyModel):
  def __init__(self, parent):
    QtGui.QAbstractProxyModel.__init__(self, parent)

  def columnCount(self, parent):
    assert parent.model() == self if parent.isValid() else True
    return self.sourceModel().columnCount(self.mapToSource(parent))

  # def dropMimeData

  def index(self, row, column, parent):
    assert parent.model() == self if parent.isValid() else True
    sourceParent = self.mapToSource(parent)
    sourceIndex = self.sourceModel().index(row, column, sourceParent)
    return self.mapFromSource(sourceIndex)

  def sibling(self, row, column, idx):
    return self.mapFromSource(self.sourceModel().sibling(row, column, self.mapToSource(idx)))

  # def insertColumns
  # def insertRows

  def mapFromSource(self, sourceIndex):
    if self.sourceModel() is None or not sourceIndex.isValid():
      return QtCore.QModelIndex()
    assert sourceIndex.model() == self.sourceModel()
    return self.createIndex(sourceIndex.row(), sourceIndex.column(), sourceIndex.internalPointer())

  # def mapSelectionFromSource
  # def mapSelectionToSource

  def mapToSource(self, proxyIndex):
    if self.sourceModel() is None or not proxyIndex.isValid():
      return QtCore.QModelIndex()
    assert proxyIndex.model() == self
    return self.sourceModel().createIndex(proxyIndex.row(), proxyIndex.column(), proxyIndex.internalPointer())

  # def match

  def parent(self, child):
    # assert child.model() == self if child.isValid() else True
    sourceIndex = self.mapToSource(child)
    sourceParent = sourceIndex.parent()
    return self.mapFromSource(sourceParent)

  # def removeColumns
  # def removeRows

  def rowCount(self, parent):
    assert parent.model() == self if parent.isValid() else True
    return self.sourceModel().rowCount(self.mapToSource(parent))

  def headerData(self, section, orientation, role):
    self.sourceModel().headerData(section, orientation, role)

  def setSourceModel(self, newSourceModel):
    self.beginResetModel()
    if self.sourceModel() is not None:
      # disconnect
      pass
    QtGui.QAbstractProxyModel.setSourceModel(self, newSourceModel)
    if self.sourceModel() is not None:
      self.sourceModel().rowsAboutToBeInserted.connect(self.sourceRowsAboutToBeInserted)
      self.sourceModel().rowsInserted.connect(self.sourceRowsInserted)
      #self.sourceModel().rowsAboutToBeRemoved.connect(self.sourceRowsAboutToBeRemoved)
      #self.sourceModel().rowsRemoved.connect(self.sourceRowsRemoved)
      #self.sourceModel().rowsAboutToBeMoved.connect(self.sourceRowsAboutToBeMoved)
      #self.sourceModel().rowsMoved.connect(self.sourceRowsMoved)
      #self.sourceModel().columnsAboutToBeInserted.connect(self.sourceColumnsAboutToBeInserted)
      #self.sourceModel().columnsInserted.connect(self.sourceColumnsInserted)
      #self.sourceModel().columnsAboutToBeRemoved.connect(self.sourceColumnsAboutToBeRemoved)
      #self.sourceModel().columnsRemoved.connect(self.sourceColumnsRemoved)
      #self.sourceModel().columnsAboutToBeMoved.connect(self.sourceColumnsAboutToBeMoved)
      #self.sourceModel().columnsMoved.connect(self.sourceColumnsMoved)
      #self.sourceModel().modelAboutToBeReset.connect(self.sourceModelAboutToBeReset)
      #self.sourceModel().modelReset.connect(self.sourceModelReset)
      self.sourceModel().dataChanged.connect(self.sourceDataChanged)
      #self.sourceModel().headerDataChanged.connect(self.sourceHeaderDataChanged)
      #self.sourceModel().layoutAboutToBeChanged.connect(self.sourceLayoutAboutToBeChanged)
      #self.sourceModel().layoutChanged.connect(self.sourceLayoutChanged)
    self.endResetModel()

  def sourceRowsAboutToBeInserted(self, parent, start, end):
    assert parent.model() == self.sourceModel() if parent.isValid() else True
    self.beginInsertRows(self.mapFromSource(parent), start, end)

  def sourceRowsInserted(self, parent, start, end):
    assert parent.model() == self.sourceModel() if parent.isValid() else True
    self.endInsertRows()

  def sourceDataChanged(self, topLeft, bottomRight):
    assert topLeft.model() == self.sourceModel() if topLeft.isValid() else True
    assert bottomRight.model() == self.sourceModel() if bottomRight.isValid() else True
    self.dataChanged.emit(self.mapFromSource(topLeft), self.mapFromSource(bottomRight))
