#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2011 analogue@yahoo.com
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import logging
import os
import socket
import sys
import xbmc
import xbmcaddon

log = logging.getLogger('mythbox.core')

__instance = None


def getPlatform():
    global __instance
    if not __instance:
        if 'win32' in sys.platform:
            __instance = WindowsPlatform()
        elif 'linux' in sys.platform:
            __instance = UnixPlatform()
        elif 'darwin' in sys.platform:
            # gotta be a better way to detect ipad/iphone/atv2
            if 'USER' in os.environ and os.environ['USER'] in ('mobile','frontrow',):
                __instance = IOSPlatform()
            else: 
                __instance = MacPlatform()
        else:
            log.error('ERROR: Platform check did not match win32, linux, darwin, or iOS. Was %s instead' % sys.platform)
            __instance = UnixPlatform()
    return __instance


def requireDir(dir):
    '''Create dir with missing path segments and return for chaining'''
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


class Platform(object):

    def __init__(self, *args, **kwargs):
        self.addon = xbmcaddon.Addon('script.mythbox')
        requireDir(self.getScriptDataDir())
        requireDir(self.getCacheDir())

    def xbmcVersion(self):
        build = xbmc.getInfoLabel('System.BuildVersion')
     
        # TODO: regex'ify
        # methods to extract version as number given build string   
        methods = [
            lambda b: float(b.split()[0]),               # sample input: 10.1 Git:Unknown  
            lambda b: float(b.split()[0].split('-')[1]), # sample input: PRE-11.0 Git:Unknown
            lambda b: float(b.split()[0].split('-')[0]), # sample input: 11.0-BETA1 Git:20111222-22ad8e4
            lambda b: 0.0
        ]
        
        for m in methods:
            try:
                version = m(build)
                break
            except ValueError:
                # parsing failed, try next method
                pass
            
        return version
            
    def addLibsToSysPath(self):
        '''Add 3rd party libs in ${scriptdir}/resources/lib to the PYTHONPATH'''
        lib_paths = [
            ('decorator',), 
            ('odict',),
            ('bidict',), 
            ('elementtree',), 
            ('tvdb_api',), 
            ('tvrage',),
            ('themoviedb',), 
            ('IMDbPY',), 
            ('simplejson',), 
            ('mysql-connector-python','python2'),
            ('python-twitter',),
            ('twisted',),
            ('zope.interface',),
            ('mockito',),
            ('unittest2',),
            ('unittest',)]
        
        for lib_path in lib_paths:
            path = os.path.join(self.getScriptDir(), 'resources', 'lib', *lib_path)
            if os.path.exists(path):
                sys.path.insert(0, path)
        
        testPath = os.path.join(self.getScriptDir(), 'resources', 'test')
        if os.path.exists(testPath):
            sys.path.insert(0, testPath)
            
        for i, path in enumerate(sys.path):    
            log.debug('syspath[%d] = %s' % (i, path))
    
    def getName(self):
        return "N/A"
    
    def getXbmcLog(self):
        raise Exception('abstract method')
    
    def getScriptDir(self):
        '''
        @return: directory that this xbmc script resides in.
        
        linux  : ~/.xbmc/addons/script.mythbox
        windows: c:\Documents and Settings\[user]\Application Data\XBMC\addons\script.mythbox
        mac    : ~/Library/Application Support/XBMC/addons/script.mythbox
        '''
        return self.addon.getAddonInfo('path')
    
    def getScriptDataDir(self):
        '''
        @return: directory for storing user settings for this xbmc script.
        
        linux  : ~/.xbmc/userdata/addon_data/script.mythbox
        windows: c:\Documents and Settings\[user]\Application Data\XBMC\UserData\addon_data\script.mythbox
        mac    : ~/Library/Application Support/XBMC/UserData/addon_data/script.mythbox
        '''
        return xbmc.translatePath(self.addon.getAddonInfo('profile'))
    
    def getCacheDir(self):
        return os.path.join(self.getScriptDataDir(), 'cache')
    
    def getUserDataDir(self):
        return xbmc.translatePath('special://userdata')
    
    def getHostname(self):
        try:
            return socket.gethostname()
        except:
            return xbmc.getIPAddress()
     
    def isUnix(self):
        return False
    
    def addonVersion(self):
        return self.addon.getAddonInfo('version')
            
    def __repr__(self):
        bar = "=" * 80
        s = bar + \
"""
hostname        = %s
platform        = %s 
script dir      = %s
script data dir = %s
""" % (self.getHostname(), type(self).__name__, self.getScriptDir(), self.getScriptDataDir())
        s += bar
        return s
    
    def getDefaultRecordingsDir(self):
        return ''

    def getMediaPath(self, mediaFile):
        # TODO: Fix when we support multiple skins
        return os.path.join(self.getScriptDir(), 'resources', 'skins', 'Default', 'media', mediaFile)
        
    def showPopup(self, title, text, millis=10000):
        # filter all commas out of text since they delimit args
        title = title.replace(',', ';')
        text = text.replace(',', ';')
        s = u'XBMC.Notification(%s,%s,%s)' % (title, text, millis)
        xbmc.executebuiltin(s)


class UnixPlatform(Platform):

    def __init__(self, *args, **kwargs):
        Platform.__init__(self, *args, **kwargs)
        
    def getName(self):
        return "unix"
    
    def isUnix(self):
        return True
        
    def getDefaultRecordingsDir(self):
        return '/var/lib/mythtv/recordings'

    def getXbmcLog(self):    
        return os.path.join(xbmc.translatePath('special://temp'), 'xbmc.log')
    

class WindowsPlatform(Platform):

    def __init__(self, *args, **kwargs):
        Platform.__init__(self, *args, **kwargs)
    
    def getName(self):
        return "windows"

    def getDefaultRecordingsDir(self):
        return 'c:\\change\\me'

    def getXbmcLog(self):    
        return os.path.join(xbmc.translatePath('special://home'), 'xbmc.log')
    
        
class MacPlatform(Platform):

    def __init__(self, *args, **kwargs):
        Platform.__init__(self, *args, **kwargs)
        
    def getName(self):
        return 'mac'

    def getDefaultRecordingsDir(self):
        return '/change/me'

    def getXbmcLog(self):
        # TODO: verify    
        return os.path.expanduser(os.path.join('~', 'Library', 'Logs', 'xbmc.log'))

    
class IOSPlatform(Platform):
    
    def __init__(self, *args, **kwargs):
        Platform.__init__(self, *args, **kwargs)
        
    def getName(self):
        return 'ios'

    def getDefaultRecordingsDir(self):
        return '/var/mobile'

    def getXbmcLog(self):
        #19:30:47 T:165597184 M: 73052160  NOTICE: Starting XBMC, Platform: Mac OS X (10.4.0 AppleTV2,1). Built on Feb 27 2011 (Git:6ba831d)
        #19:30:47 T:165597184 M: 73052160  NOTICE: special://xbmc/ is mapped to: /Applications/XBMC.frappliance/XBMCData/XBMCHome
        #19:30:47 T:165597184 M: 73052160  NOTICE: special://xbmcbin/ is mapped to: /Applications/XBMC.frappliance/XBMCData/XBMCHome
        #19:30:47 T:165597184 M: 72990720  NOTICE: special://masterprofile/ is mapped to: /var/mobile/Library/Preferences/XBMC/userdata
        #19:30:47 T:165597184 M: 72990720  NOTICE: special://home/ is mapped to: /var/mobile/Library/Preferences/XBMC
        #19:30:47 T:165597184 M: 72990720  NOTICE: special://temp/ is mapped to: /var/mobile/Library/Preferences/XBMC/temp
        #19:30:47 T:165597184 M: 72990720  NOTICE: The executable running is: /Applications/XBMC.frappliance/XBMC
        #19:30:47 T:165597184 M: 72990720  NOTICE: Log File is located: /var/mobile/Library/Preferences/xbmc.log        
        return os.path.expanduser(os.path.join('~', 'Library', 'Preferences', 'xbmc.log'))

