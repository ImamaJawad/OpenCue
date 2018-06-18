#  Copyright (c) 2018 Sony Pictures Imageworks Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


"""
A frame list based on AbstractTreeWidget
"""
from Manifest import os, QtCore, QtGui, Cue3

import Constants
import Logger
import Style
import Utils

from MenuActions import MenuActions
from AbstractTreeWidget import *
from AbstractWidgetItem import *

logger = Logger.getLogger(__file__)

class ProcMonitorTree(AbstractTreeWidget):
    def __init__(self, parent):
        self.startColumnsForType(Constants.TYPE_PROC)
        self.addColumn("Name", 150, id=1,
                       data=lambda proc:(proc.data.name),
                       tip="Name of the running proc.")
        self.addColumn("Cores", 50, id=2,
                       data=lambda proc: ("%.2f" % proc.data.reservedCores),
                       tip="The number of cores reserved.")
        self.addColumn("Mem Reserved", 100, id=3,
                       data=lambda proc:(Utils.memoryToString(proc.data.reservedMemory)),
                       tip="The amount of memory reserved.")
        self.addColumn("Mem Used", 100, id=4,
                       data=lambda proc:(Utils.memoryToString(proc.data.usedMemory)),
                       tip="The amount of memory used.")
        self.addColumn("GPU Used", 100, id=5,
                       data=lambda proc:(Utils.memoryToString(proc.data.reservedGpu)),
                       tip="The amount of gpu memory used.")
        self.addColumn("Age", 60, id=6,
                       data=lambda proc:(Utils.secondsToHHHMM(time.time() - proc.data.dispatchTime)),
                       tip="The age of the running frame.")
        self.addColumn("Unbooked", 80, id=7,
                       data=lambda proc:(proc.data.unbooked),
                       tip="If the proc has been unbooked.\n If it is unbooked then"
                           "when the frame finishes the job will stop using this proc")
        self.addColumn("Name", 300, id=8,
                       data=lambda proc:(proc.data.frameName),
                       tip="The name of the proc, includes frame number and layer name.")
        self.addColumn("Job", 50, id=9,
                       data=lambda proc:(proc.data.jobName),
                       tip="The job that this proc is running on.")

        self.procSearch = Cue3.ProcSearch()

        AbstractTreeWidget.__init__(self, parent)

        # Used to build right click context menus
        self.__menuActions = MenuActions(self, self.updateSoon, self.selectedObjects)

        QtCore.QObject.connect(self,
                               QtCore.SIGNAL('itemClicked(QTreeWidgetItem*,int)'),
                               self.__itemSingleClickedCopy)

        # Don't use the standard space bar to refresh
        QtCore.QObject.disconnect(QtGui.qApp,
                                  QtCore.SIGNAL('request_update()'),
                                  self.updateRequest)

        self.startTicksUpdate(40)
        # Don't start refreshing until the user sets a filter or hits refresh
        self.ticksWithoutUpdate = -1
        self.enableRefresh = False

    def tick(self):
        if self.ticksWithoutUpdate >= self.updateInterval and \
           not self.window().isMinimized():
            self.ticksWithoutUpdate = 0
            self._update()
            return

        if self.enableRefresh and \
           self.ticksWithoutUpdate <= self.updateInterval + 1 and \
           self.ticksWithoutUpdate >= 0:
            self.ticksWithoutUpdate += 1

    def facilityChanged(self):
        """Called when the facility is changed and removes then updates the proc
        list"""
        self.removeAllItems()
        self._update()

    def __itemSingleClickedCopy(self, item, col):
        """Called when an item is clicked on. Copies selected object names to
        the middle click selection clip board.
        @type  item: QTreeWidgetItem
        @param item: The item clicked on
        @type  col: int
        @param col: The column clicked on"""
        selected = [proc.data.name for proc in self.selectedObjects() if Utils.isProc(proc)]
        if selected:
            QtGui.QApplication.clipboard().setText(",".join(selected),
                                                   QtGui.QClipboard.Selection)

    def clearFilters(self):
        self.clearSelection()
        self.procSearch = Cue3.ProcSearch()
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.removeAllItems()

    def updateRequest(self):
        """Updates the items in the TreeWidget if sufficient time has passed
        since last updated"""
        self.ticksWithoutUpdate = 999

    def _getUpdate(self):
        """Returns the proper data from the cuebot"""
        try:
            # Refuse to update if no search criteria is defined
            if not self.procSearch.maxResults and \
               not self.procSearch.hosts and \
               not self.procSearch.jobs and \
               not self.procSearch.layers and \
               not self.procSearch.shows and \
               not self.procSearch.allocs and \
               not self.procSearch.memoryRange and \
               not self.procSearch.durationRange:
                return []

            return Cue3.Cuebot.Proxy.getProcs(self.procSearch)
        except Exception, e:
            map(logger.warning, Utils.exceptionOutput(e))
            return []

    def _createItem(self, object, parent = None):
        """Creates and returns the proper item
        @type  object: Proc
        @param object: The object for this item
        @type  parent: QTreeWidgetItem
        @param parent: Optional parent for this item
        @rtype:  QTreeWidgetItem
        @return: The created item"""
        if not parent:
            parent = self
        return ProcWidgetItem(object, parent)

    def contextMenuEvent(self, e):
        """When right clicking on an item, this raises a context menu"""
        menu = QtGui.QMenu()
        self.__menuActions.procs().addAction(menu, "view")
        self.__menuActions.procs().addAction(menu, "unbook")
        self.__menuActions.procs().addAction(menu, "kill")
        self.__menuActions.procs().addAction(menu, "unbookKill")
        menu.exec_(e.globalPos())

class ProcWidgetItem(AbstractWidgetItem):
    def __init__(self, object, parent):
        AbstractWidgetItem.__init__(self, Constants.TYPE_PROC, object, parent)
