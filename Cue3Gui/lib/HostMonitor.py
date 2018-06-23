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


from Manifest import os, QtCore, QtGui, Cue3

from MenuActions import MenuActions
import Utils
import Constants
import Logger

from HostMonitorTree import HostMonitorTree

log = Logger.getLogger(__file__)

FILTER_HEIGHT = 20

class HostMonitor(QtGui.QWidget):
    """This contains the frame list table with controls at the top"""
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.hostMonitorTree = HostMonitorTree(self)

        # Setup main vertical layout
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(4)

        # This hlayout would contain any filter/control buttons
        hlayout = QtGui.QHBoxLayout()
        self.__filterByHostNameSetup(hlayout)      # Menu to filter by host name
        self.__filterAllocationSetup(hlayout)    # Menu to filter by allocation
        self.__filterHardwareStateSetup(hlayout) # Menu to filter by hardware state
        hlayout.addStretch()
        self.__refreshToggleCheckBoxSetup(hlayout) # Checkbox to disable auto refresh
        self.__refreshButtonSetup(hlayout)         # Button to refresh
        self.__clearButtonSetup(hlayout)           # Button to clear all filters

        self.layout().addLayout(hlayout)
        self.layout().addWidget(self.hostMonitorTree)

        self.__viewHostsSetup()                  # For view_hosts signal

    def updateRequest(self):
        self.hostMonitorTree.updateRequest()

    def getColumnVisibility(self):
        return self.hostMonitorTree.getColumnVisibility()

    def setColumnVisibility(self, settings):
        self.hostMonitorTree.setColumnVisibility(settings)

# ==============================================================================
# Text box to filter by host name
# ==============================================================================
    def __filterByHostNameSetup(self, layout):
        btn = QtGui.QLineEdit(self)
        btn.setMaximumHeight(FILTER_HEIGHT)
        btn.setFixedWidth(155)
        btn.setFocusPolicy(QtCore.Qt.StrongFocus)
        layout.addWidget(btn)
        self.__filterByHostName = btn

        self.__filterByHostNameLastInput = None

        QtCore.QObject.connect(self.__filterByHostName,
                               QtCore.SIGNAL('editingFinished()'),
                               self.__filterByHostNameHandle)

        btn = QtGui.QPushButton("Clr")
        btn.setMaximumHeight(FILTER_HEIGHT)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setFixedWidth(24)
        layout.addWidget(btn)
        QtCore.QObject.connect(btn,
                               QtCore.SIGNAL('clicked()'),
                               self.__filterByHostNameClear)

        self.__filterByHostNameClearBtn = btn

    def __filterByHostNameHandle(self):
        regex = str(self.__filterByHostName.text()).split()
        if regex and regex != self.__filterByHostNameLastInput:
            self.__filterByHostNameLastInput = regex
            self.hostMonitorTree.hostSearch.regex = regex
            self.hostMonitorTree.updateRequest()

    def __filterByHostNameClear(self):
        self.__filterByHostNameLastInput = ""
        self.__filterByHostName.setText("")
        self.hostMonitorTree.hostSearch.regex = []

# ==============================================================================
# Menu to filter by allocation
# ==============================================================================
    def __filterAllocationSetup(self, layout):
        self.__filterAllocationList = sorted([alloc.data.name for alloc in Cue3.getAllocations()])

        btn = QtGui.QPushButton("Filter Allocation")
        btn.setMaximumHeight(FILTER_HEIGHT)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setContentsMargins(0,0,0,0)
        btn.setFlat(True)

        menu = QtGui.QMenu(self)
        btn.setMenu(menu)
        QtCore.QObject.connect(menu,
                               QtCore.SIGNAL("triggered(QAction*)"),
                               self.__filterAllocationHandle)

        for item in ["Clear", None] + self.__filterAllocationList:
            if item:
                a = QtGui.QAction(menu)
                a.setText(str(item))
                if item != "Clear":
                    a.setCheckable(True)
                menu.addAction(a)
            else:
                menu.addSeparator()

        layout.addWidget(btn)
        self.__filterAllocationButton = btn

    def __filterAllocationClear(self):
        """Clears the currently selected status menu items"""
        btn = self.__filterAllocationButton
        menu = btn.menu()
        for action in menu.actions():
            action.setChecked(False)
        self.hostMonitorTree.hostSearch.allocs = []

    def __filterAllocationHandle(self, action):
        """Called when an option in the filter status menu is triggered.
        Tells the HostMonitorTree widget what status to filter by.
        @param action: Defines the menu item selected
        @type  action: QAction"""
        __hostSearch = self.hostMonitorTree.hostSearch
        if action.text() == "Clear":
            for item in self.__filterAllocationButton.menu().actions():
                if item.isChecked():
                    if item.text() != "Clear":
                        __hostSearch.allocs.remove(str(item.text()))
                    item.setChecked(False)
        else:
            if action.isChecked():
                __hostSearch.allocs.append(str(action.text()))
            else:
                __hostSearch.allocs.remove(str(action.text()))

        self.hostMonitorTree.updateRequest()

# ==============================================================================
# Menu to filter by hardware state
# ==============================================================================
    def __filterHardwareStateSetup(self, layout):
        self.__filterHardwareStateList = sorted([state for state in dir(Cue3.HardwareState) if not state.startswith("_")])

        btn = QtGui.QPushButton("Filter HardwareState")
        btn.setMaximumHeight(FILTER_HEIGHT)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setContentsMargins(0,0,0,0)
        btn.setFlat(True)

        menu = QtGui.QMenu(self)
        btn.setMenu(menu)
        QtCore.QObject.connect(menu,
                               QtCore.SIGNAL("triggered(QAction*)"),
                               self.__filterHardwareStateHandle)

        for item in ["Clear", None] + self.__filterHardwareStateList:
            if item:
                a = QtGui.QAction(menu)
                a.setText(str(item))
                if item != "Clear":
                    a.setCheckable(True)
                menu.addAction(a)
            else:
                menu.addSeparator()

        layout.addWidget(btn)
        self.__filterHardwareStateButton = btn

    def __filterHardwareStateClear(self):
        """Clears the currently selected status menu items"""
        btn = self.__filterHardwareStateButton
        menu = btn.menu()
        for action in menu.actions():
            action.setChecked(False)
        self.hostMonitorTree.hostSearch.states = []

    def __filterHardwareStateHandle(self, action):
        """Called when an option in the filter status menu is triggered.
        Tells the HostMonitorTree widget what status to filter by.
        @param action: Defines the menu item selected
        @type  action: QAction"""
        __hostSearch = self.hostMonitorTree.hostSearch
        if action.text() == "Clear":
            for item in self.__filterHardwareStateButton.menu().actions():
                if item.isChecked():
                    if item.text() != "Clear":
                        __hostSearch.states.remove(getattr(Cue3.HardwareState,
                                                           str(item.text())))
                    item.setChecked(False)
        else:
            if action.isChecked():
                __hostSearch.states.append(getattr(Cue3.HardwareState,
                                                   str(action.text())))
            else:
                __hostSearch.states.remove(getattr(Cue3.HardwareState,
                                                   str(action.text())))

        self.hostMonitorTree.updateRequest()

# ==============================================================================
# Checkbox to toggle auto-refresh
# ==============================================================================
    def __refreshToggleCheckBoxSetup(self, layout):
        checkBox = QtGui.QCheckBox("Auto-refresh", self)
        layout.addWidget(checkBox)
        if self.hostMonitorTree.enableRefresh:
            checkBox.setCheckState(QtCore.Qt.Checked)
        QtCore.QObject.connect(checkBox,
                               QtCore.SIGNAL('stateChanged(int)'),
                               self.__refreshToggleCheckBoxHandle)
        __refreshToggleCheckBoxCheckBox = checkBox

    def __refreshToggleCheckBoxHandle(self, state):
        self.hostMonitorTree.enableRefresh = bool(state)

# ==============================================================================
# Button to refresh
# ==============================================================================
    def __refreshButtonSetup(self, layout):
        """Sets up the refresh button, adds it to the given layout
        @param layout: The layout to add the button to
        @type  layout: QLayout"""
        self.btn_refresh = QtGui.QPushButton("Refresh")
        self.btn_refresh.setMaximumHeight(FILTER_HEIGHT)
        self.btn_refresh.setFocusPolicy(QtCore.Qt.NoFocus)
        layout.addWidget(self.btn_refresh)
        QtCore.QObject.connect(self.btn_refresh,
                               QtCore.SIGNAL('clicked()'),
                               self.hostMonitorTree.updateRequest)

        QtCore.QObject.connect(self.hostMonitorTree,
                               QtCore.SIGNAL("updated()"),
                               self.__refreshButtonDisableHandle)

    def __refreshButtonEnableHandle(self):
        """Called when the refresh button should be enabled"""
        self.btn_refresh.setEnabled(True)

    def __refreshButtonDisableHandle(self):
        """Called when the refresh button should be disabled"""
        self.btn_refresh.setEnabled(False)
        QtCore.QTimer.singleShot(5000, self.__refreshButtonEnableHandle)

# ==============================================================================
# Button to clear all filters
# ==============================================================================
    def __clearButtonSetup(self, layout):
        """Sets up the clear button, adds it to the given layout
        @param layout: The layout to add the button to
        @type  layout: QLayout"""
        btn = QtGui.QPushButton("Clear")
        btn.setMaximumHeight(FILTER_HEIGHT)
        btn.setFocusPolicy(QtCore.Qt.NoFocus)
        btn.setContentsMargins(0,0,0,0)
        layout.addWidget(btn)
        QtCore.QObject.connect(btn,
                               QtCore.SIGNAL('clicked()'),
                               self.__clearButtonHandle)

    def __clearButtonHandle(self):
        """Called when the clear button is clicked"""
        self.hostMonitorTree.ticksWithoutUpdate = -1
        self.__filterAllocationClear()
        self.__filterHardwareStateClear()
        self.__filterByHostNameClear()
        self.hostMonitorTree.clearFilters()

# ==============================================================================
# Monitors and handles the view_hosts signal
# ==============================================================================
    def __viewHostsSetup(self):
        QtCore.QObject.connect(QtGui.qApp,
                               QtCore.SIGNAL('view_hosts(PyQt_PyObject)'),
                               self.__viewHostsHandle)

    def __viewHostsHandle(self, hosts):
        self.__clearButtonHandle()
        self.hostMonitorTree.hostSearch.hosts = hosts
        self.__filterByHostName.setText(" ".join(hosts))
        self.hostMonitorTree.updateRequest()