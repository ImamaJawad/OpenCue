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


"""action.py

    utility functions for creating QActions
"""
from Manifest import QtGui, QtCore

import Constants

Actions = { }
Groups = { }

ICON_PATH = "%s/images" % Constants.RESOURCE_PATH

def create(parent,text,tip,callback=None,icon=None):
    """create(QtGui.QWidget, string text, string tip, callable callback=None, string icon=None)
        creates a QtGui.QAction and optionally connects it to a slot
    """
    a = QtGui.QAction(parent)
    a.setText(text)
    if tip:
        a.setToolTip(tip)
    if icon:
        a.setIcon(QtGui.QIcon(":%s.png" % (icon)))
    if callback:
        connectActionSlot(a,callback)
    return a

def createAction(parent,id,text,tip,callback=None,icon=None):
    """create(QtGui.QWidget, string text, string tip, callable callback=None, string icon=None)
        creates a QtGui.QAction and optionally connects it to a slot
    """
    if Actions.has_key(id):
        raise Exception("Action %s has already been created" % (id))

    a = QtGui.QAction(parent)
    a.setText(text)
    if tip:
        a.setToolTip(tip)
    if icon:
        a.setIcon(QtGui.QIcon(":/images/%s.png" % icon))
    if callback:
        connectActionSlot(a,callback)
    Actions[id] = a
    return a

def getAction(id):
    return Actions[id]

def createActionGroup(parent,id,actions):
    g = QtGui.QActionGroup(parent)
    for action in actions:
        g.addAction(action)
    Groups[id] = g

def getActionGroup(id):
    return Groups[id]

def applyActionGroup(id,menu):
    for act in getActionGroup(id).actions():
        menu.addAction(act)

def connectActionSlot(action,callable):
    """connectActionSlot
        connects an action's triggered() signal to a callable object
    """
    QtCore.QObject.connect(action,QtCore.SIGNAL("triggered()"), callable)

class Refresh(QtGui.QAction):
    """Refresh

        refresh something
    """

    def __init__(self,callback=None, parent=None):
        QtGui.QAction.__init__(self,parent)
        self.setText("Refresh")
        self.setIcon(QtGui.QIcon(":/images/stock-refresh.png"))
        if callback:
            QtCore.QObject.connect(self,QtCore.SIGNAL("triggered()"), callback)
