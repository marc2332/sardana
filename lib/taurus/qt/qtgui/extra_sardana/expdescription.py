#!/usr/bin/env python

#############################################################################
##
## This file is part of Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""This module provides widget for configuring the data acquisition and display of an experiment"""

__all__ = ["ExpDescriptionEditor"]

from taurus.qt import Qt
import copy
import taurus
from taurus.qt.qtgui.base import TaurusBaseWidget

class ExpDescriptionEditor(Qt.QWidget, TaurusBaseWidget):
    '''
    A widget for editing the configuration of a experiment (measurement groups,
    plot and storage parameters, etc).
    
    It receives a Sardana Door name as its model and gets/sets the configuration
    using the `ExperimentConfiguration` environmental variable for that Door.
    '''
    def __init__(self, parent=None, door=None):
        Qt.QWidget.__init__(self, parent)
        TaurusBaseWidget.__init__(self, 'ExpDescriptionEditor')
        from ui.ui_ExpDescriptionEditor import Ui_ExpDescriptionEditor
        self.ui = Ui_ExpDescriptionEditor()
        self.ui.setupUi(self)
        BB = Qt.QDialogButtonBox
        self.ui.buttonBox.setStandardButtons(Qt.QDialogButtonBox.Reset | Qt.QDialogButtonBox.Apply)
        
        self._localConfig = None
        self._originalConfiguration = None
        self._dirty = False
        self._dirtyMntGrps = set()
        
        self.connect(self.ui.activeMntGrpCB, Qt.SIGNAL('activated (QString)'), self.onActiveMntGrpActivated)
        self.connect(self.ui.compressionCB, Qt.SIGNAL('currentIndexChanged (int)'), self.onCompressionCBChanged )
        self.connect(self.ui.pathLE, Qt.SIGNAL('textEdited (QString)'), self.onPathLEEdited )
        self.connect(self.ui.filenameLE, Qt.SIGNAL('textEdited (QString)'), self.onFilenameLEEdited )
        self.connect(self.ui.channelEditor.getQModel(), Qt.SIGNAL('dataChanged (QModelIndex, QModelIndex)'), self._updateButtonBox )
        self.connect(self.ui.channelEditor.getQModel(), Qt.SIGNAL('modelReset ()'), self._updateButtonBox )
        self.connect(self.ui.preScanList, Qt.SIGNAL('dataChanged'), self.onPreScanSnapshotChanged )
        self.connect(self.ui.choosePathBT, Qt.SIGNAL('clicked ()'), self.onChooseScanDirButtonClicked)
        
        if door is not None:
            self.setModel(door)
        self.connect(self.ui.buttonBox, Qt.SIGNAL("clicked(QAbstractButton *)"), self.onDialogButtonClicked)
             
    def getModelClass(self):
        '''reimplemented from :class:`TaurusBaseWidget`'''
        return taurus.core.TaurusDevice
    
    def onChooseScanDirButtonClicked(self):
        ret = Qt.QFileDialog.getExistingDirectory ( self, 'Choose directory for saving files', self.ui.pathLE.text())
        if ret:
            self.ui.pathLE.setText(ret)
            self.ui.pathLE.emit(Qt.SIGNAL('textEdited (QString)'),ret)
        
    def onDialogButtonClicked(self, button):
        role = self.ui.buttonBox.buttonRole(button)
        if role == Qt.QDialogButtonBox.ApplyRole:
            self.writeExperimentConfiguration(ask=False)
        elif role == Qt.QDialogButtonBox.ResetRole:
            self._reloadConf()
    
    def closeEvent(self,event):
        '''This event handler receives widget close events'''
        if self.isDataChanged():
            self.writeExperimentConfiguration(ask=True)
        Qt.QWidget.closeEvent(self,event)
    
    def setModel(self, model):
        '''reimplemented from :class:`TaurusBaseWidget`'''
        TaurusBaseWidget.setModel(self, model)
        self._reloadConf(force=True)
        #set the model of some child widgets
        door = self.getModelObj()
        if door is None: return
        tghost = taurus.Database().getNormalName() #@todo: get the tghost from the door model instead
        msname = door.macro_server.getFullName()
        self.ui.taurusModelTree.setModel(tghost)
        self.ui.sardanaElementTree.setModel(msname)

    def _reloadConf(self, force=False):
        if not force and self.isDataChanged():
            op = Qt.QMessageBox.question(self, "Reload info from door", 
                "If you reload, all current experiment configuration changes will be lost. Reload?", 
                Qt.QMessageBox.Yes|Qt.QMessageBox.Cancel)
            if op != Qt.QMessageBox.Yes: 
                return
        door = self.getModelObj()
        if door is None: return
        conf = door.getExperimentConfiguration()
        self._originalConfiguration = copy.deepcopy(conf)
        self.setLocalConfig(conf)
        self._setDirty(False)
        self._dirtyMntGrps = set()
        #set a list of available channels
        channels = door.macro_server.getExpChannelElements()
        avail_channels = {}
        for ch_info in door.macro_server.getExpChannelElements().values():
            avail_channels[ch_info.name] = ch_info.getData()
        self.ui.channelEditor.getQModel().setAvailableChannels(avail_channels)
    
    def _setDirty(self,dirty):
        self._dirty = dirty
        self._updateButtonBox()
        
    def isDataChanged(self):
        """Tells if the local data has been modified since it was last refreshed
        
        :return: (bool) True if he local data has been modified since it was last refreshed
        """
        return bool(self._dirty or self.ui.channelEditor.getQModel().isDataChanged() or self._dirtyMntGrps)
    
    def _updateButtonBox(self, *args, **kwargs):
        self.ui.buttonBox.setEnabled(self.isDataChanged())

    def getLocalConfig(self):
        return self._localConfig

    def setLocalConfig(self, conf):
        '''gets a ExpDescription dictionary and sets up the widget'''
    
        self._localConfig = conf
        
        #set the Channel Editor
        activeMntGrpName = self._localConfig['ActiveMntGrp']
        mgconfig = self._localConfig['MntGrpConfigs'][activeMntGrpName]
        self.ui.channelEditor.getQModel().setDataSource(mgconfig)
        
        #set the measurement group ComboBox
        self.ui.activeMntGrpCB.clear()
        self.ui.activeMntGrpCB.addItems(sorted(self._localConfig['MntGrpConfigs'].keys()))
        idx = self.ui.activeMntGrpCB.findText(activeMntGrpName)
        self.ui.activeMntGrpCB.setCurrentIndex(idx)
        
        #set the system snapshot list
        psl = self._localConfig.get('PreScanSnapshot') #I get it before clearing because clear() changes the _localConfig
        self.ui.preScanList.clear()
        self.ui.preScanList.addModels(psl)
        
        #other settings
        self.ui.filenameLE.setText(", ".join(self._localConfig['ScanFile']))
        self.ui.pathLE.setText(self._localConfig['ScanDir'] or '')
        self.ui.compressionCB.setCurrentIndex(self._localConfig['DataCompressionRank']+1)
        
    def writeExperimentConfiguration(self, ask=True):
        '''sends the current local configuration to the door
        
        :param ask: (bool) If True (default) prompts the user before saving.
        '''
        if ask:
            op = Qt.QMessageBox.question(self, "Save configuration?", 
                                        'Do you want to save the current configuration?\n(if not, any changes will be lost)', 
                                        Qt.QMessageBox.Yes|Qt.QMessageBox.No)
            if op != Qt.QMessageBox.Yes:
                return False
        
        #check if the currently displayed mntgrp is changed
        if self.ui.channelEditor.getQModel().isDataChanged():
            self._dirtyMntGrps.add(self._localConfig['ActiveMntGrp'])
            
        conf = self.getLocalConfig()
        door = self.getModelObj()
        door.setExperimentConfiguration(conf, mnt_grps=self._dirtyMntGrps)
        self._originalConfiguration = copy.deepcopy(conf)
        self._dirtyMntGrps = set()
        self.ui.channelEditor.getQModel().setDataChanged(False)
        self._setDirty(False)
        self.emit(Qt.SIGNAL('experimentConfigurationChanged'), copy.deepcopy(conf))
        return True
        
    def onActiveMntGrpActivated(self, activeMntGrpName):
        activeMntGrpName = str(activeMntGrpName)
        if self._localConfig is None: 
            return
        if activeMntGrpName == self._localConfig['ActiveMntGrp']: 
            return #nothing changed
        if activeMntGrpName not in self._localConfig['MntGrpConfigs']: 
            raise KeyError('Unknown measurement group "%s"'%activeMntGrpName)
        
        #add the previous measurement group to the list of "dirty" groups if something was changed
        if self.ui.channelEditor.getQModel().isDataChanged():
            self._dirtyMntGrps.add(self._localConfig['ActiveMntGrp'])
                            
        self._localConfig['ActiveMntGrp'] = activeMntGrpName
        mgconfig = self._localConfig['MntGrpConfigs'][activeMntGrpName]
        self.ui.channelEditor.getQModel().setDataSource(mgconfig)
        self._setDirty(True)
        
    def onCompressionCBChanged(self, idx):
        if self._localConfig is None: return
        self._localConfig['DataCompressionRank'] = idx - 1
        self._setDirty(True)
        
    def onPathLEEdited(self, text):
        self._localConfig['ScanDir'] = str(text)
        self._setDirty(True)
        
    def onFilenameLEEdited(self, text):
        self._localConfig['ScanFile'] = [v.strip() for v in str(text).split(',')]
        self._setDirty(True)
        
    def onPreScanSnapshotChanged(self, items):  
        self._localConfig['PreScanSnapshot'] = [(e.src,e.display) for e in items]
        self._setDirty(True)    
    
        
            


  
            
def demo(model="mydoor"):
    """Table panels"""
    #w = main_ChannelEditor()
    w = ExpDescriptionEditor(door=model)
    return w


def main():
    import sys
    import taurus.qt.qtgui.application
    Application = taurus.qt.qtgui.application.TaurusApplication
    
    app = Application.instance()
    owns_app = app is None
    
    if owns_app:
        app = Application(app_name="Exp. Description demo", app_version="1.0",
                          org_domain="Sardana", org_name="Tango community")
    
    args = app.get_command_line_args()
    if len(args)==1:
        w = demo(model=args[0])
    else:
        w = demo()
    w.show()
    
    if owns_app:
        sys.exit(app.exec_())
    else:
        return w
    
if __name__ == "__main__":
    main()
