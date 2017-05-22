# -*- coding: ISO-8859-1 -*-
#
# This script is in charge with incorporating external SDKs referenced in HELiOS into the working copy.
#
# Versions of incorporated SDKs are saved in the cache file: fetchedExternalSDKs_HELiOS.cache
# A fetch is omitted in case the version to fetch matches the fetched version.
#
# Caution: This script is intended to be called both manually from command line or by an svn update hook.
#          Letting ${hicadDevDir} point to the current working directory '.' produces
#          undesired results when called by a hook, as a svn update on e.g. ${HICAD_DEV_DIR}/Source/projekte/${A_PROJECT} 
#          incorporates the external sdks relative to ${HICAD_DEV_DIR}/Source/projekte/${A_PROJECT}.
#          On the other hand we don't want to hard wire the ${HICAD_DEV_DIR} path, since a bunch of developers unfortunately don't 
#          checkout HiCAD under the standard path. Doing so would require 'em to adjust the path to meet their configuration.
#          Reading ${CWD} isn't a solution to the problem either as one could call this script from a subdirectory (python ../../../${this_script})
#          letting the sdks being copied into a wrong path.
#          Least hurting compromise: This script assumes to always be in ${HICAD_DEV_DIR} and hence has an orientation point which is sufficient to find 
#                                    the correct targets for the sdks.
#                                    ==> Script currently needs to be in ${HICAD_DEV_DIR} to work until we find a better solution!

import ConfigParser, os.path
import datetime
import shutil
import subprocess
import sys

############ Customizable block (begin) #########
'''
Package settings
================

Notes:
For normal entries, do not set 'destrelto' or set it to 'dev'
for HiCAD's dev base dir (default); do not set a 'package' value.
Naming convention for package files: "%prefix_%version.%ext"

Optional fields:
'destrelto' : can be one of 'dev', 'disk' or 'absolute' (disk and absolute should normally not be necessary).

'package' : use this to directly specify the package file name (not necessary if package follows naming conventions).

'ext'     : the extension of the package file name (only valid if 'package' is not set); defaults to 'zip'.
'''
sdkList = {

    "sqlite" : {
        "fetch"   : True,
        "prefix"  : "sqlite",
        "version" : "1_0_93_0_static",
        "ext"     : "7z",
        "dest"    : "externalSDKs",
    },

    "boost" : {
        "fetch"   : True,
        "prefix"  : "boost",
        "version" : "1_61_0_vs140_sp4",
        "ext"     : "7z",
        "dest"    : "externalSDKs",
    },

    "cppunit" : {
        "fetch"   : True,
        "prefix"  : "cppunit",
        "version" : "1_12_1_vs140_sp3",
        "ext"     : "7z",
        "dest"    : "externalSDKs",
    },

    "zlib" : {
        "fetch"   : True,
        "prefix"  : "zlib",
        "version" : "1_2_8_vs140_sp3",
        "ext"     : "zip",
        "dest"    : "externalSDKs",
    },



    "TopGeomHilfe" : {
        "fetch"   : True,
        "prefix"  : "TopGeomHilfe",
        "version" : "6",
        "dest"    : "externalSDKs",
    },

    "dummylibs" : {
        "fetch"   : True,
        "prefix"  : "dummylibs",
        "version" : "2_vs140_sp3",
        "dest"    : "externalSDKs",
    },
    
}
############ Customizable block (end) ###########

serverOld = "srv011"
serverOldDir = r"\\%s\Binaries\external_sdks" % serverOld
serverNew = "intl"
serverNewDir = r"\\%s\Networked Files\R&D\External Build SDKs" % serverNew

server = ""
serverDir = ""
msbuild = "%SystemRoot%\\Microsoft.NET\\Framework\\v4.0.30319\\MSBuild.exe"

cacheFileUrl = ""

NO_ENTRY_EXISTING = 'NO_ENTRY_EXISTING'
NOT_FETCHED = 'NOT_FETCHED'
CACHE_FILE_OUTDATED = -1
CACHE_FILE_UPTODATE =  1

def incorporateSDK(sdk, sdkToKeyMap, keyValueMap):

    try:
        print("---------------------------------------------------------------------------")        

        global sdkList

        sdkVersion = ""
        sdkExtractionDest = ""
        sdkPackage = ""
        sdkSubDir = ""
        key = ""
        if sdk in sdkList:
            key = sdkToKeyMap[sdk]
            fetchedSdkVersion = keyValueMap[key]
            sdkSettings = sdkList[sdk]
            sdkVersion = sdkSettings['version']
            sdkExtractionDest = sdkSettings['_dest']
            sdkPackage = sdkSettings['package']
            sdkSubDir = sdkSettings['prefix']
        else:
            return 
          
        if fetchedSdkVersion != sdkVersion:
                        
            print("Current " + sdk + " version [" + sdkVersion + "] is different than the fetched [" + fetchedSdkVersion + "] " + sdk + " version.")
          
            # Make sure the package we want to fetch really exists:  
            serverSdkUrl = os.path.join(serverDir, sdkPackage)
            if False == os.path.exists(serverSdkUrl):
                print("Error: Didn't find " + serverSdkUrl + ". Make sure it exists.")
                print("Failed to fetch " + sdk + " in version: " + sdkVersion) 
                return

            # Delete the already fetched version:
            localSdkUrl = os.path.join(sdkExtractionDest, sdkSubDir)
            if True == os.path.isdir(localSdkUrl):
                print("Deleting previous version..")            
                shutil.rmtree(localSdkUrl, ignore_errors=True)
          
            print("Going to fetch the current version..")
            print("")      
            now = datetime.datetime.now()
            print("")
            print("Fetching 3rd party library [" + sdk + "] from " + serverDir + " into " + sdkExtractionDest)
            print(now)
            osCommand = "7z.exe -y x \""+ serverSdkUrl + "\" -o" + sdkExtractionDest
            if True != os.path.isdir(sdkExtractionDest):
                print("Path [" + sdkExtractionDest + "] does not exist. Going to create it..")
                os.makedirs(sdkExtractionDest)

            os.system(osCommand)

            now = datetime.datetime.now()
            print("")
            print(now)
            print("Finished fetching 3rd party library [" + sdk + "]")
            
            # Update cache file:
            keyValueMap[key] = sdkVersion
            persistCacheFile(keyValueMap)                
        else:
            print ('Fetching the ' + sdk + ' sdk skipped as the current version [' + sdkVersion + '] equals the fetched [' + fetchedSdkVersion + '] version.')                

    except Exception, e:
        print("Execution of function incorporateSDK failed:", e) 
        updateCacheFile("external_sdks", sdkConfigFileKey, NOT_FETCHED)
        raise #re-raise the exact same exception that was thrown


# Parses existing configuration file
def parseCacheFile(keyValueMap):

    fileHandle = open(cacheFileUrl)
    
    configParser = ConfigParser.ConfigParser()
    configParser.read(cacheFileUrl)
    

    exceptionText = 'Exception thrown when trying to read an entry from cache file: '    
    section = 'external_sdks'
    
    # Update the key value map with the contents of the cache file:
    for key, value in keyValueMap.iteritems():        
        if configParser.has_option(section, key):
            value = configParser.get(section, key)
            keyValueMap[key] = value           
    
    fileHandle.close()
    
    # Is our cache file outdated (e.g. has less keys than 'this' script wants to persist)?
    cacheFileAntiqued = False
    for key, value in keyValueMap.iteritems():        
        if value == NO_ENTRY_EXISTING:
            keyValueMap[key] = NOT_FETCHED
            cacheFileAntiqued = True            

    # Update cache file if outdated:
    if True == cacheFileAntiqued:        
        return CACHE_FILE_OUTDATED
    else:
        return CACHE_FILE_UPTODATE



# Persists key value pairs into a specified section of the cache file
def persistCacheFile(keyValueMap):
  
    try:
        section = 'external_sdks'
        fileHandle = open(cacheFileUrl, 'wb') 
        configParser = ConfigParser.ConfigParser()
        configParser.read(cacheFileUrl)
        configParser.add_section(section)
        
        for key, value in keyValueMap.iteritems():            
            configParser.set(section, key, value)
        
        configParser.write(fileHandle)
        
        print('Updated config file.')
        
        fileHandle.close()

    except Exception, e:
        print("Execution of function updateCacheFile failed:", e) 
        raise #re-raise the exact same exception that was thrown  



# Tests whether a cache file is available
def cacheFileExists(hicadDevDir):
    
    # Convert fetchedExternalSDKs.conf to fetchedExternalSDKs.cache:
    oldConfigFile = hicadDevDir + "/fetchedExternalSDKs.conf" 
    if os.path.exists(oldConfigFile) and os.path.isfile(oldConfigFile):
        shutil.move(oldConfigFile, cacheFileUrl)

    
    if os.path.exists(cacheFileUrl) and os.path.isfile(cacheFileUrl):
      return True
    else:
      return False

      
      
def checkForUnzipUtility():
    try: 
        output = subprocess.Popen(["7z"], stdout=subprocess.PIPE).communicate()[0]
        debugOutput = output
    except Exception, e:
        print("7z not found. Make sure it is in your path.")
        print("Execution failed:", e)
        return False


def run():

    try:
        absPath = os.path.abspath(sys.argv[0])        
        hicadDevDir = os.path.dirname(absPath)
        hicadDevDisk, hicadDevDirRelToDisk = os.path.splitdrive(hicadDevDir)
        
        # SDK name -> Config file key
        sdkToKeyMap = {}

        # Richtigen Servernamen verwenden (je nach Dom�ne)
        global server
        global serverDir
        serverNewD = os.path.join(serverNewDir, '')
        if os.path.exists(serverNewD):
           server = os.path.join(serverNew, '')
           serverDir = serverNewD
        else:
           server = serverOld
           serverDir = serverOldDir

        global sdkList
        for sdkName in sdkList.keys():
            sdkSettings = sdkList[sdkName]

            sdkToKeyMap[sdkName] = 'fetched_%s' % sdkName

            if not 'ext' in sdkSettings:
                sdkSettings['ext'] = "zip"

            if not 'package' in sdkSettings:
                sdkSettings['package'] = "%s_%s.%s" % (sdkSettings['prefix'], sdkSettings['version'], sdkSettings['ext'])

            if not 'destrelto' in sdkSettings:
                sdkSettings['destrelto'] = "dev"

            if sdkSettings['destrelto'] == "dev":
                sdkSettings['_dest'] = os.path.join(hicadDevDir, sdkSettings['dest'])
            elif sdkSettings['destrelto'] == "absolute":
                sdkSettings['_dest'] = sdkSettings['dest']
            elif sdkSettings['destrelto'] == "disk":
                sdkSettings['_dest'] = r"%s\%s" % (hicadDevDisk, sdkSettings['dest']) # (os.path.join does the wrong thing here)
            else:
                raise NameError("Illegal destination base")

        global cacheFileUrl
        cacheFileUrl = r"%s\fetchedExternalSDKs.cache" % hicadDevDir
        
        unzipUtilityFound = checkForUnzipUtility()
        if False == unzipUtilityFound:
            return False
         
        print ("")
        print ("######################  External SDK fetcher  ######################")
        print ("")
        print ("Hicad dev dir          : " + hicadDevDir)
        for sdkName in sdkList.keys():
            print "dest. %-16s : %s" % (sdkName, sdkList[sdkName]['_dest'])
        print ("Cache file url         : " + cacheFileUrl)
        print ("Download server        : " + server)
        print ("Download server dir    : " + serverDir)
        print ("###################################################################")
        print ("")
        
        configFileAvailable = False
        
        # Config file key -> Config file value
        keyValueMap = {}

        if cacheFileExists(hicadDevDir):
            print("Cache file " + cacheFileUrl + " exists.")
            
            for v in sdkToKeyMap.itervalues():
                keyValueMap[v] = NO_ENTRY_EXISTING
            
            retval = parseCacheFile(keyValueMap)
            if retval == CACHE_FILE_OUTDATED:
                print('Cache file is outdated. Going to upgrade it.')
                persistCacheFile(keyValueMap)             
            configFileAvailable = True
        else:
            print(cacheFileUrl + " does not exist. Will create it..")
            
            for v in sdkToKeyMap.itervalues():
                keyValueMap[v] = NOT_FETCHED
            
            persistCacheFile(keyValueMap)
            if cacheFileExists(hicadDevDir):
              configFileAvailable = True
            else:
              print("Error: Config file does not exist and I could not create a new one. Exiting.")
              sys.exit(-1)

        for key, value in keyValueMap.iteritems():
            print(key + ": " + value)

        sdkConfigFileKey = ''
        sdkConfigFileValue = ''

        for sdkName in sdkList.keys():
            sdkSettings = sdkList[sdkName]
            if sdkSettings['fetch']:
                incorporateSDK(sdkName, sdkToKeyMap, keyValueMap)
        
        print("")  
        print("Finished.")  
          
        return True  

    except Exception, e:
        print("Execution of function main failed:", e) 
        raise #re-raise the exact same exception that was thrown  



# main function
def main():
    run()


if __name__ == '__main__':
    main()

