#!/usr/bin/python
# -*- coding: utf-8 -*-

from command import MultiOutput, MultiCommand
from exception import *

#TODO
    #voir les notes dans le fichier TODO
        #il faut encore faire le mécanisme d'arret prématuré
            #par fonction
				#faire une fonction qui interrompt le engine process
            #par exception
				#juste declarer deux exceptions
					#abnormalStopException
					#normalStopException

    #at this moment, multioutput is juste a list... 
        #must stay a list
        #TODO check if the multioutput is not converted into a simple list in the process
            #because there is a risk to lose the cmd limit
	
	#be able to merge anywhere on the stack, not only on the top
		#pour setDataCmdRange aussi

DEFAULT_EXECUTION_LIMIT = 255
PREPROCESS_INSTRUCTION  = 0
PROCESS_INSTRUCTION     = 1
POSTPROCESS_INSTRUCTION = 2

class engineStack(List):		
	def push(self, data, cmdPath, instructionType):
		self.append([(data, cmdPath, instructionType,) ])
		
	def raiseIfEmpty(self, methName = None):
		if len(self) == 0:
			if methName == None:
				raise executionException("(engine) engineStack, no item on the stack")
			else:
				raise executionException("(engine) "+cmdName+", no item on the stack")

	def size(self):
		return len(self)

	def top(self):
		return self[-1]

	def dataOnTop(self):
		return self[-1][0]
		
	def pathOnTop(self):
		return self[-1][1]
		
	def typeOnTop(self):
		return self[-1][2]
		
	def cmdIndexOnTop(self):
		return len(self[-1][0]) - 1

class engineV3(object):
### INIT ###
    def __init__(self, cmdList, env=None):
        #cmd must be a not empty list
        if cmdList == None or not isinstance(cmdList, list) or len(cmdList) == 0:
            raise executionInitException("(engine) init, command list is not a valid populated list")

        #reset every commands
        for c in cmdList:
            if not isinstance(c, MultiCommand):#only the MultiCommand are allowed in the list
                raise executionInitException("(engine) init, a object in the command list is not a MultiCommand instance, got <"+str(type(c))+">")
            
            if len(c) == 0: #empty multi command are not allowed
                raise executionInitException("(engine) init, a command is empty")
            
            #reset the information stored in the command from a previous execution
            c.reset()
        
        self.cmdList = cmdList #list of MultiCommand
        
        #check env variable
        if env == None:
            self.env = {}
        elif isinstance(env, dict):
            self.env  = env
        else:
            raise executionInitException("(engine) init, env must be a dictionnary or None, got <"+str(type(env))+">")

        #init stack with a None data, on the subcmd 0 of the command 0, with a preprocess action
        self.stack = engineStack()
        self.stack.push([None], [0], PREPROCESS_INSTRUCTION)

### TODO Command Special Meth With Abstraction TODO ###
    #okay so the problem is, we want to be able to 
        #add more subcommand
            #can occur everywhere, the command will execute the remaining data in the bound of the existing limit
        
        #add more data
            #to what ? next command ? next subcommand ?
            #how to insert data to a specific command that does not have any data on stack
				#explore the stack and insert a a right place
				#be able to insert to a specific command
				#be able to insert to a range of specific command
					#include : be able to insert to a specific subcommand
					
        #skip a sub command
			#define the scope of the skipping
			
        #...
        
    #BUT we don't care about the data abstration, the stack and others things...
        #so its very difficult to execute these operation on the whole stack for a precise command
            #currently the command limit are stored on the stack, they could be stored in the command itself
        #a command can occur at several level of the stack, or even later and it't quite difficult to manage these command with this structure
        
    #IDEA
        #only allow theses actions on the first command of the list ?
            #because its initial state is always stack[0]
                #and even splitted, they will be next to each other, from stack[0] to stack[n]
        
        #reuse the existing command on the data bunch

	def injectData(self, data, cmdPath, startIndex = 0, endIndex = None):			
		#Don't care if the stack is empty or not
		#find THE place to insert these data, there is always only one place to insert data
			#or find an existing data bunch that corresponds to the args
		#then inject the data
		
		#TODO this method must be used in the stack append, or the stack will be unordered
		length = len(self.stack)
		for i in xrange(0,length):
            currentStackItem = self.stack[length - 1 - i]
		
			#TODO
	
### COMMAND special meth ###

    def skipNextSubCommandOnTheCurrentData(self, skipCount=1):
        self.stack.raiseIfEmpty("skipNextCommandOnTheCurrentData")
        # can only skip the next command if the state is pre_process
        if self.getCurrentItemMethodeType() != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) skipNextCommandOnTheCurrentData, can only skip method on PREPROCESS item")
        
        self.stack[-1][1][-1] += skipCount
    
    def skipNextSubCommandForTheEntireDataBunch(self, skipCount=1):
        #TODO set a command limit on this data bunch
        
        #TODO no cmd limit must be already set
    
        pass #TODO
        
    def skipNextSubCommandForTheEntireExecution(self, skipCount=1):
        #TODO remove temporarly the command from the multiCommand parent object
    
        #XXX what are the implication of this ?
    
        pass #TODO
    
    def flushArgs(self, index=None): #None index means current command
        if index == None:
			self.stack.raiseIfEmpty("flushArgs")
            cmdID = self.stack.cmdIndexOnTop()
        else:
            cmdID = index
        
        if cmdID >= len(self.cmdList) or cmdID < 0:
            raise executionException("(engine) flushArgs, invalid command index")
            
        self.cmdList[cmdID].flushArgs()
    
    def addSubCommand(self, cmd, onlyAddOnce = True, useArgs = True):        
        #is there still some items on the stack ?
		self.stack.raiseIfEmpty("addSubCommand")
		
        #compute the current command index where the sub command will be insert, check the cmd path on the stack
        cmdID = self.stack.cmdIndexOnTop()
        
        if cmdID >= len(self.cmdList):
            raise executionException("(engine) addCommand, invalid command index")
                
        currentStartCmdIndex, currentStopCmdIndex = self.getEffectiveCurrentItemSubCmdLimit()
        
        newCmdIndex = len(self.cmdList[cmdID])
        
        if newCmdIndex < currentStartCmdIndex or (currentStopCmdIndex != None and currentStopCmdIndex < newCmdIndex):
            raise executionException("(engine) addCommand, the command bounds on this data do not enclose the new command") 
        
        #add the sub command
        self.cmdList[cmdID].addDynamicCommand(cmd, onlyAddOnce, useArgs)
    
    def addCommand(self, cmd):
        if not isinstance(cmd, MultiCommand):#only the MultiCommand are allowed in the list
            raise executionInitException("(engine) addCommand, cmd is not a MultiCommand instance, got <"+str(type(cmd))+">")
            
        cmd.reset()
        self.cmdList.append(cmd)
        
    def isCurrentRootCommand(self):
		self.stack.raiseIfEmpty("isCurrentRootCommand")
        return self.stack.cmdIndexOnTop() == 0
    
### COMMAND ultra ultra special meth ###
    
    def setDataCmdRange(self, startIndex = 0, endIndex=None, firstCmd = 0, cmdLength = None):        
        #stack can not be empty
        self.stack.raiseIfEmpty("setDataCmdRange")
        
        #check data range
        currentCmdLength = len(self.cmdList[self.stack.cmdIndexOnTop()])
		self._checkCmdRange(currentCmdLength,startIndex,endIndex)

        #compute split points and dept level
        if endIndex == None:
            dept = 0
            if startData == 0:
                pass #no need to split
            else:
                self.splitData(startData)
        else:
            dept = 1
            if startData == 0:
                self.splitData(endIndex-1)
            else:
                self.splitData(endIndex-1)
                self.splitData(startData)
        
            splitPoints.append(startData)

        #set cmd range
        self.setCmdRange(startIndex,endIndex,dept,False)
        
    def setDataCmdRangeAndMerge(self, startIndex = 0, endIndex = None, MergeCount = 2):
		#stack can't be empty
		self.stack.raiseIfEmpty("setDataCmdRangeAndMerge")
		
		#the cmd range must be valid
			#check only with the first item to merge
			#create a generic sub method and use it in setCommandRange too
		currentCmdLength = len(self.cmdList[self.stack.cmdIndexOnTop()])
		self._checkCmdRange(currentCmdLength,startIndex,endIndex)
		
		#try to merge
			#the command will check every needed thing before to merge
		self.mergeDataOnStack(MergeCount)
		
		#set cmd range
		self.setCmdRange(startIndex, endIndex,0, False)

### COMMAND ultra special meth ###

#TODO update stack from here #####

    def mergeDataOnStack(self, count = 2):
        #need at least two item to merge
        if count < 1:
            return #no need to merge
        
        #the stack need to hol
        if len(self.stack) < count:
            raise executionException("(engine) mergeDataOnStack, no enough of data on stack to merge")

        #extract information from first item
        pathOnTop = self.stack[-1][1]
        actionToExecute = self.stack[-1][2]
        
        #extract start/end command for the top data
        firstStartCmdIndex, firstStopCmdIndex = self.getEffectiveCurrentItemSubCmdLimit()
        
        for i in range(1,count):
            currentStackItem = self.stack[len(self.stack) - 1 - i]
            
            #extract and compare start/end command
            currentStartCmdIndex = 0
            if hasattr(currentStackItem[0],"cmdStartIndex"): #is there already a cmd start index ?
                currentStartCmdIndex = currentStackItem[0].cmdStartIndex
            
            currentStopCmdIndex = None
            if hasattr(currentStackItem[0],"cmdStopIndex"): #is there already a cmd stop index ?
                currentStopCmdIndex = currentStackItem[0].cmdStopIndex
            
            if firstStartCmdIndex != currentStartCmdIndex and firstStopDataIndex != currentStopCmdIndex:
                raise executionException("(engine) mergeDataOnStack, the command limit of item "+str(i)+"are different of the limit of the top item 0")
            
            #the path must be the same for each item to merge
                #execpt for the last command, the items not at the top of the stack must have 0 or the cmdStartLimit
            if len(currentStackItem[1]) != len(pathOnTop):
                raise executionException("(engine) mergeDataOnStack, the command path is different for the item "+str(i))
            
            for j in range(0,len(pathOnTop)-1):
                if currentStackItem[1][i] != pathOnTop[i]:
                    raise executionException("(engine) mergeDataOnStack, a subcommand index is different for the item "+str(i))
            
            if currentStackItem[1][-1] != currentStartCmdIndex:
                raise executionException("(engine) mergeDataOnStack, the item "+str(i)+" different of the top has not its index set to default")
            
            #the action must be the same type
            if currentStackItem[2] != actionToExecute:
                raise executionException("(engine) mergeDataOnStack, the action of the item "+str(i)+"is different of the action ot the top item 0")

        #merge data and keep start/end command
        dataBunch = MultiOutput()
        for i in range(0,count):
            data = self.stack.pop()
            dataBunch.extend(data)
        
        dataBunch.cmdStartIndex = firstStartCmdIndex
        dataBunch.cmdStopIndex  = firstStopDataIndex
        self.stack.append( (dataBunch, pathOnTop, actionToExecute, ) )
    
    def _checkCmdRange(self, currentCmdLength, startIndex = 0, endIndex = None):
		#Check endIndex
        if endIndex != None:
			if startIndex > endIndex:
				raise executionException("(engine) _checkCmdRange, startIndex is bigger than endIndex, invalid bounds")
			
			if startIndex == endIndex:
				raise executionException("(engine) _checkCmdRange, startIndex is equal to endIndex, the command range can not be empty")
			
			#we can not set cmdLength to None because if the user set a limit then add new command
				#is different of set a None limit then add command
			if endIndex > currentCmdLength-1:
				raise executionException("(engine) _checkCmdRange, cmdLength is bigger than the command list size")

		#check startIndex
		if startIndex < 0:
            raise executionException("(engine) _checkCmdRange, startIndex index can not be a negative value") 
		
		#the new index must be in the cmd range
        if startIndex >= currentCmdLength:
            raise executionException("(engine) _checkCmdRange, startIndex index is not in the command bound") 
        
    
    def setCmdRange(self, startIndex = 0, endIndex = None, dataDepth = 0, checkRange=True):
        #is empty stack ?
        self.stack.raiseIfEmpty("setCmdRange")
        
        #is the dataDepth reachable
        if dataDepth < 0 or dataDepth > (len(self.stack)-1):
            raise executionException("(engine) setCmdRange, invalid depth value")
        
        #get the item where set the range
        stackItem = self.stack[(len(self.stack)-1)-dataDepth]
        
        #is it a pre ?
        if stackItem[2] != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) setCmdRange, no need to put a cmd range on a pro/post process, there is only one command to execute")
            #the cmd range is always of length 1, no need to set cmd range
        
        #check the cmd limit
        if checkRange:
			currentCmdLength = len(self.cmdList[len(stackItem[1]) - 1])
			self._checkCmdRange(currentCmdLength, startIndex, endIndex)
        
        if endIndex != None 
			endIndex -= 1
			
        #the current cmd index must be in the cmd range
        currentCmdIndex = self.stack[-1][1][-1]
        if currentCmdIndex < startIndex or (endIndex != None and endIndex < currentCmdIndex):
            raise executionException("(engine) setDataCmdRange, the bounds must enclose the current cmd index") 

        #set the cmd limit
        dataBunch = MultiOutput(stackItem[0])
        dataBunch.cmdStartIndex = startIndex
        dataBunch.cmdStopIndex  = endIndex
        self.stack[(len(self.stack)-1)-dataDepth] = (dataBunch,stackItem[1],stackItem[2],)
   
    def splitData(self,splitAtDataIndex=0): #split the data into two separate stack item at the index, but will not change anything in the process order
        #is empty stack ?
		self.stack.raiseIfEmpty("splitData")
		
        #is it a pre ? (?)
        if self.stack[-1][2] != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) splitData, can't split the data of a PRO/POST process because it will not change anything on the execution")

        topdata = self.stack[-1][0]
        #split point exist ?
        if splitAtDataIndex < 0 or splitAtDataIndex > (len(topdata)-1):
            raise executionException("(engine) splitData, split index out of bound")

        #has enought data to split ?
        if len(topdata) < 2 or splitAtDataIndex == 0:
            return

        # get current cmd limit #
        currentStartCmdIndex, currentStopCmdIndex = self.getEffectiveCurrentItemSubCmdLimit()

        top = self.stack.pop()
        
        #from 0 to splitAtDataIndex
        dataBunch = MultiOutput(top[0][splitAtDataIndex:])
        dataBunch.cmdStartIndex = currentStartCmdIndex
        dataBunch.cmdStopIndex  = currentStopCmdIndex
        path = top[1][:]
        path[-1] = 0 
        self.stack.append( (dataBunch, path, top[2], ) )
            
        #from splitAtDataIndex to the end
        dataBunch = MultiOutput(top[0][0:splitAtDataIndex])
        dataBunch.cmdStartIndex = currentStartCmdIndex
        dataBunch.cmdStopIndex  = currentStopCmdIndex
        self.stack.append( (dataBunch, top[1], top[2], ) )

### DATA special meth (data of the top item on the stack) ###
    
    def flushData(self):
	    self.stack.raiseIfEmpty("flushData")
        data = self.stack[-1][0]
        del data[:] #remove everything, the engine is able to manage an empty data bunch
    
    def addData(self, newdata, offset=1, forbideInsertionAtZero = True):    
		self.stack.raiseIfEmpty("addData")
        if forbideInsertionAtZero and offset == 0:
            raise executionException("(engine) addData, can't insert a data at offset 0, it could create infinite loop. it is possible to override this check with the boolean forbideInsertionAtZero, set it to False")
    
        self.stack[-1][0].insert(offset,newdata)
    
    def removeData(self, offset=0, resetSubCmdIndexIfOffsetZero=True):
		self.stack.raiseIfEmpty("removeData")
        data = self.stack[-1][0]
        
        #valid offset ?
        if offset >= len(data) or offset < (-1)*len(data): #allow offset with minus
            raise executionException("(engine) removeData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        #remove the data
        del data[offset]
        
        #set the current cmd index to startIndex -1 (the minus 1 is because the engine will make a plus 1 to execute the next command)
        if resetSubCmdIndexIfOffsetZero and (offset == 0 or (len(data) == 0 and offset == -1)):
            start, end = self.getEffectiveCurrentItemSubCmdLimit()
            self.stack[-1][1][-1] = start - 1
    
    def setData(self, newdata, offset=0):
		self.stack.raiseIfEmpty("setData")
        data = self.stack[-1][0]
        
        if offset >= len(data):
            raise executionException("(engine) setData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        data[offset] = newdata

    def getData(self, offset=0):
		self.stack.raiseIfEmpty("getData")
        data = self.stack[-1][0]
        
        if offset >= len(data):
            raise executionException("(engine) getData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        return data[offset]
        
    def hasNextData(self):
		self.stack.raiseIfEmpty("hasNextData")
        data = self.stack[-1][0]
        
        return len(data) > 1 #1 and not zero, because there are the current data and the next one
        
    def getRemainingDataCount(self):
		self.stack.raiseIfEmpty("getRemainingDataCount")
        data = self.stack[-1][0]
        return len(data)-1 # -1 because we don't care about the current data
        
    def getDataCount(self):
		self.stack.raiseIfEmpty("getDataCount")
        data = self.stack[-1][0]
        return len(data)

        
### STACK meth ###
    def isEmptyStack(self):
        return len(self.stack) == 0
        
    def isLastStackItem(self):
        return len(self.stack) == 1
        
    def getStackSize(self):
        return len(self.stack)
    
### STACK ITEM meth ###
    def getCurrentItemMethodeType(self):
		self.stack.raiseIfEmpty("getCurrentItemMethodeType")
        return self.stack[-1][2]
    
    def getCurrentItemData(self):
		self.stack.raiseIfEmpty("getCurrentItemData")
        return self.stack[-1][0][:] #return a copy, because these information can not be updated from the outside
        
    def getCurrentItemCmdPath(self):
		self.stack.raiseIfEmpty("getCurrentItemCmdPath")
        return self.stack[-1][1][:] #return a copy, because these information can not be updated from the outside
    
    def getRawCurrentItemSubCmdLimit(self):
        self.stack.raiseIfEmpty("getCurrentMethodeType")
        dataTop = self.stack[-1][0]
        starting = None
        if hasattr(dataTop,"cmdStartIndex"):
            starting = dataTop.cmdStartIndex

        end = None
        if hasattr(dataTop,"cmdStopIndex"):
            end = dataTop.cmdStopIndex
            
        return (starting, end, )
    
    def getEffectiveCurrentItemSubCmdLimit(self):
        rawStart, rawEnd = self.getRawCurrentItemSubCmdLimit()
        
        if rawStart == None:
            rawStart = 0
            
        #if rawEnd == None:
        #    rawEnd = len(self.cmdList[len(self.stack[-1][1]) -1]) - 1
        
        return (rawStart, rawEnd, )

### VARIOUS meth ###

    def getEnv(self):
        return self.env
    
### ENGINE meth ###
    
    def execute(self):
        #consume stack
        while len(self.stack) != 0: #while there is some item into the stack
            ### EXTRACT DATA FROM STACK ###
            top     = self.stack[-1]#.pop()
            #top[0] contain the current data of this item
            #top[1] contain the command path
            #top[2] contain the process type to execute
            
            cmd             = self.cmdList[len(top[1]) -1]
            subcmd, useArgs = cmd[top[1][-1]]
            
            ### EXECUTE command ###
            to_stack = None #prepare the var to push on the stack, if the var keep the none value, nothing will be stacked

            ## PRE PROCESS
            if top[2] == PREPROCESS_INSTRUCTION: #pre
                r = self.executeMethod(cmd, subcmd.preProcess, top, useArgs)
                subcmd.preCount += 1
                
                #manage result
                if len(top[1]) == len(self.cmdList): #no child, next step will be a process
                    to_stack = (r, top[1][:], PROCESS_INSTRUCTION, )
                else: #there are some child, next step will be another preprocess
                    new_path = top[1][:] #copy the path
                    new_path.append(0) #then add the first index of the next command
                    to_stack = (r, new_path, PREPROCESS_INSTRUCTION, )
            
            ## PROCESS ##
            elif top[2] == PROCESS_INSTRUCTION: #pro
                r = self.executeMethod(cmd, subcmd.process, top, useArgs)
                subcmd.proCount += 1
                
                #manage result
                to_stack = (r, top[1], POSTPROCESS_INSTRUCTION,)
            
            ## POST PROCESS ##
            elif top[2] == POSTPROCESS_INSTRUCTION: #post
                r = self.executeMethod(cmd, subcmd.postProcess, top, useArgs)
                subcmd.postCount += 1
                
                #manage result
                if len(top[1]) > 1: #not on the root node
                     to_stack = (r, top[1][:-1], POSTPROCESS_INSTRUCTION,) #just remove one item in the path to get the next postprocess to execute
            else:
                raise executionException("(engine) execute, unknwon process command <"+str(top[2])+">")
        
            if subcmd.preCount > DEFAULT_EXECUTION_LIMIT or subcmd.proCount > DEFAULT_EXECUTION_LIMIT or subcmd.postCount > DEFAULT_EXECUTION_LIMIT :
                raise executionException("(engine) execute, this subcommand reach the execution limit count")
            
            ### MANAGE STACK, need to repush the current item ? ###
            self.stack.pop()
            if top[2] == PROCESS_INSTRUCTION or top[2] == POSTPROCESS_INSTRUCTION: #process or postprocess ?
                if len(top[0]) > 1: #still data to execute ?
                    self.stack.append(  (top[0][1:],top[1],top[2],)  ) #remove the last used data and push on the stack
            else:# top[2] == 0 #preprocess, can't be anything else, a test has already occured sooner in the engine function
                
                #compute the limit of command to execute
                if hasattr(top[0],"cmdStopIndex") and top[0].cmdStopIndex != None:
                    limit = top[0].cmdStopIndex
                else:
                    limit = len(cmd)-1
            
                if top[1][-1] < limit: #still child to execute ?
                    if len(top[0]) > 0: #still data to execute ? the current data could be reuse with another cmd, so we need to known if there is at least one data
                        top[1][-1] += 1 #select the nex child id
                        self.stack.append(  (top[0],top[1],top[2],)  ) #push on the stack again
                else: #every child has been executed with this data, the current is the last one
                    if len(top[0]) > 1: #still data to execute ? the data 0 is the current, the current command already execute it, so we need more than one data to continue
                    
                        #compute the first command to execute
                        if hasattr(top[0],"cmdStartIndex") and top[0].cmdStartIndex != None:
                            starting = top[0].cmdStartIndex
                        else:
                            starting = 0
                        
                        #remove the data without doing any update on the cmd limit
                        del top[0][0]
                        
                        top[1][-1] = starting #select the first child
                        self.stack.append(  (top[0],top[1],top[2],)  ) #remove the last used data, because every cmd already used id, and push on the stack
            
            ### STACK THE RESULT of the current process if needed ###
            if to_stack != None:
                self.stack.append(to_stack)
                
    def executeMethod(self, cmd,subcmd, stackState, useArgs):
        nextData = stackState[0][0]

        #prepare data
        args = cmd.getArgs()
        if args != None and useArgs:
            if nextData != None:
                args = args[:]
                args.extend(nextData)
        elif nextData != None:
            args = nextData
        else:
            args = []

        #execute checker
        if hasattr(subcmd, "checker"):         
            data = subcmd.checker.checkArgs(args, self)
        else:
            data = {}

        #execute Xprocess
        r = subcmd(**data)
        
        #r must be a multi output
        if not isinstance(r, MultiOutput):
            return [r]

        return r

### DEBUG meth ###
    
    def getExecutionSnapshot(self):
        info = {}

        if self.isEmptyStack(): 
            info["cmdIndex"]    = -1
            info["cmd"]         = None
            info["subCmdIndex"] = -1
            info["subCmd"]      = None
            info["data"]        = None
            info["processType"] = -1
        else:
            top = self.stack[-1]

            info["cmdIndex"]    = len(top[1]) -1                           #the index of the current command in execution
            info["cmd"]         = self.cmdList[len(top[1]) -1]             #the object instance of the current command in execution
            info["subCmdIndex"] = top[1][-1]                               #the index of the current sub command in execution
            info["subCmd"]      = self.cmdList[len(top[1]) -1][top[1][-1]] #the object instance of the current sub command in execution
            info["data"]        = top[0][0]                                #the data of the current execution
            info["processType"] = top[2]                                   #the process type of the current execution
    
        return info

    def printStack(self):
        for i in range(0,len(self.stack)):
            topData = self.stack[i][0]
            currentStartCmdIndex = "Not defined"
            if hasattr(topData,"cmdStartIndex"): #is there already a cmd start index ?
                currentStartCmdIndex = topData.cmdStartIndex
            
            currentStopCmdIndex = "Not defined"
            if hasattr(topData,"cmdStopIndex"): #is there already a cmd stop index ?
                currentStopCmdIndex = topData.cmdStopIndex
        
            print "#["+str(i)+"] data=", self.stack[i][0], ", path=", self.stack[i][1], ", action=",self.stack[i][2], ", cmd range=",(currentStartCmdIndex, currentStopCmdIndex)


