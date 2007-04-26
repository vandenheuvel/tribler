import wx
import wx.xrc as xrc
import random
from Tribler.vwxGUI.GuiUtility import GUIUtility
from Tribler.vwxGUI.tribler_topButton import tribler_topButton
from Tribler.CacheDB.CacheDBHandler import MyDBHandler

class ProfileOverviewPanel(wx.Panel):
    def __init__(self, *args, **kw):
#        print "<mluc> tribler_topButton in init"
        self.initDone = False
        self.elementsName = [ 'bgPanel_Overall', 'perf_Overall', 'icon_Overall', 'text_Overall', 
                             'bgPanel_Quality', 'perf_Quality', 'text_Quality', 
                             'bgPanel_Files', 'perf_Files', 'text_Files', 
                             'bgPanel_Persons', 'perf_Persons', 'text_Persons', 
                             'bgPanel_Download', 'perf_Download', 'text_Download', 
                             'bgPanel_Presence', 'perf_Presence', 'text_Presence',
                             'st229c']
        self.elements = {}
        self.data = {} #data related to profile information, to be used in details panel
        if len(args) == 0: 
            pre = wx.PrePanel() 
            # the Create step is done by XRC. 
            self.PostCreate(pre) 
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate) 
        else:
            wx.Panel.__init__(self, *args, **kw) 
            self._PostInit()     
        
    def OnCreate(self, event):
#        print "<mluc> tribler_topButton in OnCreate"
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self._PostInit)
        event.Skip()
        return True
    
    def _PostInit(self):
#        print "<mluc> tribler_topButton in _PostInit"
        # Do all init here
        self.guiUtility = GUIUtility.getInstance()
#        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouseAction)
#        self.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
        for element in self.elementsName:
            xrcElement = xrc.XRCCTRL(self, element)
            if not xrcElement:
                print 'profileOverviewPanel: Error: Could not identify xrc element:',element
            self.elements[element] = xrcElement

        my_db = MyDBHandler()
        self.getGuiElement('st229c').SetLabel(my_db.get('name', ''))

        self.buttons = []
        #add mouse over text and progress icon
        for elem_name in self.elementsName:
            if elem_name.startswith("bgPanel_"):
                self.buttons.append(elem_name)
                but_elem = self.getGuiElement(elem_name)
                but_elem.setBackground(wx.Colour(203,203,203))
                suffix = elem_name[8:]
                text_elem = self.getGuiElement('text_%s' % suffix)
                perf_elem = self.getGuiElement('perf_%s' % suffix)
                icon_elem = self.getGuiElement('icon_%s' % suffix)
                if isinstance(self.getGuiElement(elem_name),tribler_topButton) :
                    if text_elem:
                        text_elem.Bind(wx.EVT_MOUSE_EVENTS, but_elem.mouseAction)
                    if perf_elem:
                        perf_elem.Bind(wx.EVT_MOUSE_EVENTS, but_elem.mouseAction)
                    if icon_elem:
                        icon_elem.Bind(wx. EVT_MOUSE_EVENTS, but_elem.mouseAction)
                else:
                    but_elem.Bind(wx.EVT_LEFT_UP, self.guiUtility.buttonClicked)
                if text_elem:
                    text_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
                if perf_elem:
                    perf_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
                if icon_elem:
                    icon_elem.Bind(wx.EVT_LEFT_UP, self.sendClick)
        self.initDone = True
        self.Refresh(True)
#        self.Update()
        self.timer = None
        wx.CallAfter(self.reloadData)
        
    def sendClick(self, event):
        source = event.GetEventObject()
        source_name = source.GetName()
#        print "<mluc> send event from",source_name
        if source_name.startswith('text_') or source_name.startswith('perf_') or source_name.startswith('icon_'):
            #send event to background button
            but_name = 'bgPanel_'+source_name[5:]
            self.selectNewButton(but_name)
#            print "<mluc> send event to",but_name
            new_owner = self.getGuiElement(but_name)
            event.SetEventObject(new_owner)
            wx.PostEvent( new_owner, event)
        elif source_name.startswith('bgPanel_'):
            self.selectNewButton(source_name)

    def selectNewButton(self, sel_but):
        for button in self.buttons:
            butElem = self.getGuiElement(button)
            if button == sel_but:
                if isinstance(butElem,tribler_topButton):
                    butElem.setSelected(True)
            elif isinstance(butElem, tribler_topButton) and butElem.isSelected():
                butElem.setSelected(False)

    def getGuiElement(self, name):
        if not self.elements.has_key(name) or not self.elements[name]:
#            print "[profileOverviewPanel] gui element %s not available" % name
            return None
        return self.elements[name]
    
    def reloadData(self, event=None):
        """updates the fields in the panel with new data if it has changed"""
        if not self.IsShown(): #should not update data if not shown
            return
        bShouldRefresh = False
        #set the overall ranking to a random number
#===============================================================================
#        new_index = random.randint(0,3) #used only for testing
#        elem = self.getGuiElement("icon_Overall")
#        if elem and new_index != elem.getIndex():
#            elem.setIndex(new_index)
#            bShouldRefresh = True
#===============================================================================
        overall_index = 0
        
        #get the number of downloads for this user
        count = self.guiUtility.data_manager.getDownloadHistCount()
        aux_count = count
        if aux_count > 100:
            aux_count = 101
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/20)+1
        overall_index = overall_index + new_index
        qualityElem = self.getGuiElement("perf_Quality")
        if qualityElem and new_index != qualityElem.getIndex():
            qualityElem.setIndex(new_index)
            self.data['downloaded_files'] = count
            bShouldRefresh = True
        
        #get the number of similar peers
        count = self.guiUtility.peer_manager.getCountOfSimilarPeers()
        aux_count = count
        if aux_count > 500:
            aux_count = 501
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/100)+1
        overall_index = overall_index + new_index
        elem = self.getGuiElement("perf_Persons")
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            self.data['similar_peers'] = count
            bShouldRefresh = True
        
        #get the number of similar files (tasteful)
        count = self.guiUtility.data_manager.getRecommendFilesCount()
        aux_count = count
        if aux_count > 100:
            aux_count = 101
        if aux_count < 0:
            aux_count = 0
        new_index = int((aux_count-1)/20)+1
        overall_index = overall_index + new_index
        elem = self.getGuiElement("perf_Files")
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            self.data['taste_files'] = count
            bShouldRefresh = True

        overall_index = int(overall_index)
        if overall_index > 6:
            overall_index = 6
        #set the overall performance to a random number
        new_index = overall_index #random.randint(0,5) #used only for testing
        elem = self.getGuiElement("perf_Overall")
        if elem and new_index != elem.getIndex():
            elem.setIndex(new_index)
            if new_index < 2:
                self.data['overall_rank'] = "beginner"
            elif new_index < 4:
                self.data['overall_rank'] = "experienced"
            elif new_index < 6:
                self.data['overall_rank'] = "top user"
            else:
                self.data['overall_rank'] = "master"
            bShouldRefresh = True
        
        if bShouldRefresh:
            self.Refresh()
            #also set data for details panel
            self.guiUtility.selectData(self.data)
        #wx.CallAfter(self.reloadData) #should be called from time to time
        if not self.timer:
            self.timer = wx.Timer(self, -1)
            self.Bind(wx.EVT_TIMER, self.reloadData, self.timer)
            self.timer.Start(5000)
        
        