
from WebAppDIRAC.Lib.WebHandler import WebHandler, WebSocketHandler, WErr, WOK, asyncGen
from DIRAC.Core.DISET.RPCClient import RPCClient
from WebAppDIRAC.Lib.SessionData import SessionData
from DIRAC import gConfig, S_OK, S_ERROR, gLogger
from DIRAC.Core.Utilities import Time, List, DictCache
from DIRAC.Core.Utilities.CFG import CFG
from DIRAC.ConfigurationSystem.private.Modificator import Modificator

import json
import types
import time

class ConfigurationManagerHandler(WebSocketHandler):

  AUTH_PROPS = "authenticated"

  def on_open(self):
    self.__configData = {}

  def on_message(self, msg):
    self.log.info("RECEIVED %s" % msg)
    try:
      params = json.loads(msg)
    except:
      gLogger.exception("No op defined")

    if params["op"] == "init":
      self.__getRemoteConfiguration("init")
    elif params["op"] == "getSubnodes":
      self.__getSubnodes(params["node"], params["nodePath"])
    elif params["op"] == "showConfigurationAsText":
      self.__showConfigurationAsText()
    elif params["op"] == "resetConfiguration":
      self.__getRemoteConfiguration("resetConfiguration")
    elif params["op"] == "getBulkExpandedNodeData":
      self.__getBulkExpandedNodeData(params["nodes"])
    elif params["op"] == "setOptionValue":
      self.__setOptionValue(params)
    elif params["op"] == "setComment":
      self.__setComment(params)
    elif params["op"] == "copyKey":
      self.__copyKey(params)
    elif params["op"] == "renameKey":
      self.__renameKey(params)
    elif params["op"] == "deleteKey":
      self.__deleteKey(params)
    elif params["op"] == "createSection":
      self.__createSection(params)
    elif params["op"] == "createOption":
      self.__createOption(params)
    elif params["op"] == "moveNode":
      self.__moveNode(params)
    elif params["op"] == "commitConfiguration":
      self.__commitConfiguration()
    elif params["op"] == "showCurrentDiff":
      self.__showCurrentDiff()

  def __getRemoteConfiguration(self, funcName):
    rpcClient = RPCClient(gConfig.getValue("/DIRAC/Configuration/MasterServer", "Configuration/Server"))
    modCfg = Modificator(rpcClient)
    retVal = modCfg.loadFromRemote()

    if retVal[ 'OK' ]:
      self.__configData[ 'cfgData' ] = modCfg
      self.__configData[ 'strCfgData' ] = str(modCfg)
      print modCfg.getOptions("/DIRAC/Configuration/Version")
      version = str(modCfg.getCFG()["DIRAC"]["Configuration"]["Version"])
      configName = str(modCfg.getCFG()["DIRAC"]["Configuration"]["Name"])
      self.write_message(json.dumps({"success":1, "op":funcName, "version":version, "name":configName}))
    else:
      self.write_message(json.dumps({"success":0, "op":"getSubnodes", "message":"The configuration cannot be read from the remote !"}))

  def __getSubnodes(self, parentNodeId, sectionPath):

    gLogger.info("Expanding section", "%s" % sectionPath)

    retData = []
    retVal = self.__getSubnodesForPath(sectionPath, retData)

    if not retVal:
      gLogger.exception("Section does not exist", "%s -> %s" % (sectionPath, str(v)))
      self.write_message(json.dumps({"success":0, "op":"getSubnodes", "message":"Section %s does not exist: %s" % (sectionPath, str(v))}))
      return

    self.write_message(json.dumps({"success":1, "op":"getSubnodes", "nodes":retData, "parentNodeId":parentNodeId}))

  def __getSubnodesForPath(self, sectionPath, retData):

    try:
      sectionCfg = self.__configData[ 'cfgData' ].getCFG()
      for section in [ section for section in sectionPath.split("/") if not section.strip() == "" ]:
        sectionCfg = sectionCfg[ section ]
    except Exception, v:
      return False

    for entryName in sectionCfg.listAll():
      comment = sectionCfg.getComment(entryName)
      nodeDef = { 'text' : entryName, 'csName' : entryName, 'csComment' : comment }
      nodeDef[ 'leaf' ] = False
      nodeDef[ 'expanded' ] = False
      if not sectionCfg.isSection(entryName):
         nodeDef[ 'leaf' ] = True
         nodeDef[ 'csValue' ] = sectionCfg[ entryName ]
         nodeDef[ 'text' ] = nodeDef[ 'text' ] + " = " + nodeDef[ 'csValue' ]

      # Comment magic
      htmlC = self.__htmlComment(comment)
      if htmlC:
        qtipDict = { 'text' : htmlC }
        nodeDef[ 'qtipCfg' ] = qtipDict
      retData.append(nodeDef)

    return True

  def __htmlComment(self, rawComment):
    commentLines = []
    commiter = ""
    rawLines = rawComment.strip().split("\n")
    if rawLines[-1].find("@@-") == 0:
      commiter = rawLines[-1][3:]
      rawLines.pop(-1)
    for line in rawLines:
      line = line.strip()
      if not line:
        continue
      commentLines.append(line)
    if commentLines or commiter:
      return "%s<small><strong>%s</strong></small>" % ("<br/>".join(commentLines), commiter)
    else:
      return False

  def __showConfigurationAsText(self):
    time.sleep(10)
    self.write_message(json.dumps({"success":1, "op":"showConfigurationAsText", "text":self.__configData[ 'strCfgData' ]}))

  def __getBulkExpandedNodeData(self, nodes):
    nodesPaths = nodes.split("<<||>>")
    returnData = []
    for nodePath in nodesPaths:
      pathData = []
      if self.__getSubnodesForPath(nodePath, pathData):
        returnData.append([nodePath, pathData])
    self.write_message(json.dumps({"success":1, "op":"getBulkExpandedNodeData", "data":returnData}))

  def __setOptionValue(self, params):
    try:
      optionPath = str(params[ 'path' ])
      optionValue = str(params[ 'value' ])
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"setOptionValue", "message":"Can't decode path or value: %s" % str(e)}))
      return

    self.__configData[ 'cfgData' ].setOptionValue(optionPath, optionValue)

    if self.__configData[ 'cfgData' ].getValue(optionPath) == optionValue:
      gLogger.info("Set option value", "%s = %s" % (optionPath, optionValue))
      self.write_message(json.dumps({"success":1, "op":"setOptionValue", "parentNodeId":params["parentNodeId"], "value":optionValue}))
    else:
      self.write_message(json.dumps({"success":0, "op":"setOptionValue", "message":"Can't update %s" % optionPath}))

  def __setComment(self, params):
    try:
      path = str(params[ 'path' ])
      value = str(params[ 'value' ])
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"setComment", "message":"Can't decode path or value: %s" % str(e)}))
      return

    self.__configData[ 'cfgData' ].setComment(path, value)
    gLogger.info("Set comment", "%s = %s" % (path, value))
    self.write_message(json.dumps({"success":1, "op":"setComment", "parentNodeId":params["parentNodeId"], "comment":self.__configData[ 'cfgData' ].getComment(path)}))

  def __copyKeyOld(self, params):
    try:
      originalPath = str(params[ 'copyFromPath' ]).strip()
      toCopyPath = str(params[ 'copyToPath' ]).strip()
      newName = str(params[ 'newName' ]).strip()
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Can't decode parameter: %s" % str(e)}))
      return
    try:
      if len(originalPath) == 0:
        self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Parent path is not valid"}))
        return
      if len(newName) == 0:
        self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Put any name for the new key!"}))
        return
      if self.__configData[ 'cfgData' ].copyKey(originalPath, newName):
        pathList = List.fromChar(originalPath, "/")
#         newPath = "/%s/%s" % ( "/".join( pathList[:-1] ), newName )
        if self.__configData[ 'cfgData' ].existsSection(toCopyPath):
          self.write_message(json.dumps({"success":1, "op":"copyKey", "parentNodeToId":params["parentNodeToId"], "parentNodeFromId":params["parentNodeFromId"], "newName":newName, "comment":self.__configData[ 'cfgData' ].getComment(newPath)}))
          return
        else:
          self.write_message(json.dumps({"success":1, "op":"copyKey", "parentNodeToId":params["parentNodeToId"], "parentNodeFromId":params["parentNodeFromId"], "value":self.__configData[ 'cfgData' ].getValue(newPath), "newName":newName, "comment":self.__configData[ 'cfgData' ].getComment(newPath)}))
          return
      else:
        self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Path can't be created. Exists already?"}))
        return
    except Exception, e:
      raise
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Can't create path: %s" % str(e)}))

  def __renameKey(self, params):
    try:
      keyPath = str(params[ 'path' ]).strip()
      newName = str(params[ 'newName' ]).strip()
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"Can't decode parameter: %s" % str(e)}))
      return
    try:
      if len(keyPath) == 0:
        self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"Entity path is not valid"}))
        return
      if len(newName) == 0:
        self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"Put any name for the entity!"}))
        return

      if self.__configData[ 'cfgData' ].existsOption(keyPath) or self.__configData[ 'cfgData' ].existsSection(keyPath) :
        if self.__configData[ 'cfgData' ].renameKey(keyPath, newName):
          self.write_message(json.dumps({"success":1, "op":"renameKey", "parentNodeId":params["parentNodeId"], "newName":newName}))
          return
        else:
          self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"There was a problem while renaming"}))
          return
      else:
        self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"Path doesn't exist"}))
        return
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"renameKey", "message":"Can't rename entity: %s" % str(e)}))
      return

  def __deleteKey(self, params):
    try:
      keyPath = str(params[ 'path' ]).strip()
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"deleteKey", "message":"Can't decode parameter: %s" % str(e)}))
      return
    try:
      if len(keyPath) == 0:
        self.write_message(json.dumps({"success":0, "op":"deleteKey", "message":"Entity path is not valid"}))
        return
      if self.__configData[ 'cfgData' ].removeOption(keyPath) or self.__configData[ 'cfgData' ].removeSection(keyPath):
        self.write_message(json.dumps({"success":1, "op":"deleteKey", "parentNodeId":params["parentNodeId"]}))
        return
      else:
        self.write_message(json.dumps({"success":0, "op":"deleteKey", "message":"Entity doesn't exist"}))
        return
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"deleteKey", "message":"Can't rename entity: %s" % str(e)}))
      return

  def __createSection(self, params):
    try:
      parentPath = str(params[ 'path' ]).strip()
      sectionName = str(params[ 'name' ]).strip()
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"createSection", "message":"Can't decode parameter: %s" % str(e)}))
      return
    try:
      if len(parentPath) == 0:
        self.write_message(json.dumps({"success":0, "op":"createSection", "message":"Parent path is not valid"}))
        return
      if len(sectionName) == 0:
        self.write_message(json.dumps({"success":0, "op":"createSection", "message":"Put any name for the section!"}))
        return
      sectionPath = "%s/%s" % (parentPath, sectionName)
      gLogger.info("Creating section", "%s" % sectionPath)
      if self.__configData[ 'cfgData' ].createSection(sectionPath):
        nD = { 'text' : sectionName, 'csName' : sectionName, 'csComment' : self.__configData[ 'cfgData' ].getComment(sectionPath) }
        htmlC = self.__htmlComment(nD[ 'csComment' ])
        if htmlC:
          qtipDict = { 'text' : htmlC }
          nD[ 'qtipCfg' ] = qtipDict
        self.write_message(json.dumps({"success":1, "op":"createSection", "parentNodeId":params["parentNodeId"], "node":nD}))
        return
      else:
        self.write_message(json.dumps({"success":0, "op":"createSection", "message":"Section can't be created. It already exists?"}))
        return
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"createSection", "message":"Can't create section: %s" % str(e)}))

  def __createOption(self, params):
    try:
      parentPath = str(params[ 'path' ]).strip()
      optionName = str(params[ 'name' ]).strip()
      optionValue = str(params[ 'value' ]).strip()
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Can't decode parameter: %s" % str(e)}))
      return
    try:
      if len(parentPath) == 0:
        self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Parent path is not valid"}))
        return
      if len(optionName) == 0:
        self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Put any name for the option!"}))
        return
      if "/" in optionName:
        self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Options can't have a / in the name"}))
        return
      if len(optionValue) == 0:
        self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Options should have values!"}))
        return
      optionPath = "%s/%s" % (parentPath, optionName)
      gLogger.info("Creating option", "%s = %s" % (optionPath, optionValue))
      if not self.__configData[ 'cfgData' ].existsOption(optionPath):
        self.__configData[ 'cfgData' ].setOptionValue(optionPath, optionValue)
        self.write_message(json.dumps({"success":1, "op":"createOption", "parentNodeId":params["parentNodeId"], "optionName":optionName, "value":self.__configData[ 'cfgData' ].getValue(optionPath), "comment":self.__configData[ 'cfgData' ].getComment(optionPath)}))
        return
      else:
        self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Option can't be created. It already exists?"}))
        return
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"createOption", "message":"Can't create option: %s" % str(e)}))

  def __moveNode(self, params):
    try:
      nodePath = params[ 'nodePath' ]
      destinationParentPath = params[ 'newParentPath' ]
      beforeOfIndex = int(params[ 'beforeOfIndex' ])
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Can't decode parameter: %s" % str(e), "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return

    gLogger.info("Moving %s under %s before pos %s" % (nodePath, destinationParentPath, beforeOfIndex))
    cfgData = self.__configData[ 'cfgData' ].getCFG()

    nodeDict = cfgData.getRecursive(nodePath)
    if not nodeDict:
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Moving entity does not exist", "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return
    oldParentDict = cfgData.getRecursive(nodePath, -1)
    newParentDict = cfgData.getRecursive(destinationParentPath)
    if type(newParentDict) == types.StringType:
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Destination is not a section", "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return
    if not newParentDict:
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Destination does not exist", "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return
    # Calculate the old parent path
    oldParentPath = "/%s" % "/".join(List.fromChar(nodePath, "/")[:-1])
    if not oldParentPath == destinationParentPath and newParentDict['value'].existsKey(nodeDict['key']):
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Another entry with the same name already exists", "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return

    try:
      brothers = newParentDict[ 'value' ].listAll()
      if beforeOfIndex < len(brothers):
        nodeDict[ 'beforeKey' ] = brothers[ beforeOfIndex ]
        print "beforekey", nodeDict[ 'beforeKey' ]
      else:
        print "last pos"
      oldParentDict[ 'value' ].deleteKey(nodeDict[ 'key' ])
      addArgs = {}
      for key in ('comment', 'beforeKey', 'value', 'key'):
        if key in nodeDict:
          addArgs[ key ] = nodeDict[ key ]
      newParentDict[ 'value' ].addKey(**addArgs)
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"moveNode", "message":"Can't move node: %s" % str(e), "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "oldIndex":params["oldIndex"]}))
      return
    self.write_message(json.dumps({"success":1, "op":"moveNode", "nodeId":params["nodeId"], "parentOldId":params["parentOldId"], "parentNewId":params["parentNewId"], "beforeOfIndex":params["beforeOfIndex"]}))

  def __copyKey(self, params):
    try:
      nodePath = params[ 'copyFromPath' ]
      destinationParentPath = params[ 'copyToPath' ]
      newNodeName = params[ 'newName' ]
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Can't decode parameter: %s" % str(e)}))
      return

#     gLogger.info( "Moving %s under %s before pos %s" % ( nodePath, destinationParentPath, beforeOfIndex ) )
    cfgData = self.__configData[ 'cfgData' ].getCFG()

    nodeDict = cfgData.getRecursive(nodePath)
    if not nodeDict:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Moving entity does not exist"}))
      return
    oldParentDict = cfgData.getRecursive(nodePath, -1)
    newParentDict = cfgData.getRecursive(destinationParentPath)
    if type(newParentDict) == types.StringType:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Destination is not a section"}))
      return
    if not newParentDict:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Destination does not exist"}))
      return
    # Calculate the old parent path
    oldParentPath = "/%s" % "/".join(List.fromChar(nodePath, "/")[:-1])
    if not oldParentPath == destinationParentPath and newParentDict['value'].existsKey(newNodeName):
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Another entry with the same name already exists"}))
      return

    try:
      brothers = newParentDict[ 'value' ].listAll()
      nodeDict["key"] = newNodeName
      addArgs = {}
      for key in ('comment', 'beforeKey', 'value', 'key'):
        if key in nodeDict:
          addArgs[ key ] = nodeDict[ key ]
      newParentDict[ 'value' ].addKey(**addArgs)
    except Exception, e:
      self.write_message(json.dumps({"success":0, "op":"copyKey", "message":"Can't move node: %s" % str(e)}))
      return
    self.write_message(json.dumps({"success":1, "op":"copyKey", "newName":nodeDict['key'], "nodeId":params["nodeId"], "parentNodeToId":params["parentNodeToId"]}))

  def __commitConfiguration(self):
    data = SessionData().getData()
    isAuth = False
    if "properties" in data["user"]:
      if "CSAdministrator" in data["user"]["properties"]:
        isAuth = True
    if not isAuth:
      self.write_message(json.dumps({"success":0, "op":"commitConfiguration", "message":"You are not authorized to commit configurations!! Bad boy!"}))
      return
    gLogger.always("User %s is commiting a new configuration version" % data["user"]["DN"])
    retDict = self.__configData[ 'cfgData' ].commit()
    if not retDict[ 'OK' ]:
      self.write_message(json.dumps({"success":0, "op":"commitConfiguration", "message":retDict[ 'Message' ]}))
      return
    self.write_message(json.dumps({"success":1, "op":"commitConfiguration"}))

  def __authorizeAction(self):
    data = SessionData().getData()
    isAuth = False
    if "properties" in data["user"]:
      if "CSAdministrator" in data["user"]["properties"]:
        isAuth = True
    return isAuth

  def __generateHTMLDiff(self, diffGen):
    diffList = []
    oldChange = False
    for diffLine in diffGen:
      if diffLine[0] == "-":
        diffList.append(("del", diffLine[1:], ""))
      elif diffLine[0] == "+":
        if oldChange:
          diffList[-1] = ("mod", diffList[-1][1], diffLine[1:])
          oldChange = False
        else:
          diffList.append(("add", "", diffLine[1:]))
      elif diffLine[0] == "?":
        if diffList[-1][0] == 'del':
          oldChange = True
        elif diffList[-1][0] == "mod":
          diffList[-1] = ("conflict", diffList[-1][1], diffList[-1][2])
        elif diffList[-1][0] == "add":
          diffList[-2] = ("mod", diffList[-2][1], diffList[-1][2])
          del(diffList[-1])
      else:
        diffList.append(("", diffLine[1:], diffLine[1:]))
    return diffList

  def __showCurrentDiff(self):
    if not self.__authorizeAction():
      return self.write_message(json.dumps({"success":0, "op":"showCurrentDiff", "message":"You are not authorized to commit configurations!! Bad boy!"}))
    diffGen = self.__configData[ 'cfgData' ].showCurrentDiff()
    return self.write_message(json.dumps({"success":1, "op":"showCurrentDiff", "html":self.render_string("ConfigurationManager/diffConfig.tpl",
                                                                                                         titles=("Server's version", "User's current version"),
                                                                                                         diffList=self.__generateHTMLDiff(diffGen))}))



