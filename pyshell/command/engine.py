#!/usr/bin/python
# -*- coding: utf-8 -*-

from command import MultiOutput

#TODO
    #voir les notes dans le fichier TODO
        #il faut encore faire le mécanisme d'arret prématuré
            #par fonction
            #par exception

    #at this moment, multioutput is juste a list... 
        #must stay a list
        #TODO check if the multioutput is not converted into a simple list in the process
            #because there is a risk to lose the cmd limit
            

DEFAULT_EXECUTION_LIMIT = 255
PREPROCESS_INSTRUCTION  = 0
PROCESS_INSTRUCTION     = 1
POSTPROCESS_INSTRUCTION = 2
    
class engineV3(object):
### INIT ###
    def __init__(self, cmdList, env=None):
        #cmd must be a not empty list
        if cmdList == None or not isinstance(cmdList, list) or len(cmdList) == 0:
            raise executionInitException("(engine) init, command list is not a valid list")

        #reset every commands
        for c in cmdList:
            if not isinstance(c, MultiCommand):#only the MultiCommand are allowed in the list
                raise executionInitException("(engine) init, a object in the command list is not a MultiCommand instance, got <"+str(type(c))+">")
            
            c.reset()
        
        self.cmdList = cmdList #list of MultiCommand
        
        #check env variable
        if env == None:
            self.env = {}
        elif isinstance(env, dict):
            self.env  = env
        else:
            raise executionInitException("(engine) init, env must be a dictionnary or None, got <"+str(type(env))+">")

        #init stack
        self.stack = [([None], [0], PREPROCESS_INSTRUCTION,) ]
    
### COMMAND special meth ###
    
    def skipNextCommandOnTheCurrentData(self, skipCount=1):
        if self.isEmptyStack(): 
            raise executionException("(engine) skipNextCommand, no item on the stack")
        
        # can only skip the next command if the state is pre_process
        if self.getCurrentItemMethodeType() != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) skipNextCommand, can only skip method on PREPROCESS item")
        
        self.stack[-1][1][-1] += skipCount
    
    def flushArgs(self, index=None): #None index means current command
        if index == None:
            if self.isEmptyStack(): 
                raise executionException("(engine) flushArgs, no item on the stack")
        
            cmdID = len(self.stack[-1][1]) -1
        else:
            cmdID = index
        
        if cmdID >= len(self.cmdList) or cmdID < 0:
            raise executionException("(engine) flushArgs, invalid command index")
            
        self.cmdList[cmdID].flushArgs()
    
    def addSubCommand(self, cmd, onlyAddOnce = True, useArgs = True):    
        #is there still some items on the stack ?
        if self.isEmptyStack(): 
            raise executionException("(engine) addCommand, no item on the stack")
    
        #compute the current command index where the sub command will be insert, check the cmd path on the stack
        cmdID = len(self.stack[-1][1]) -1
        
        if cmdID >= len(self.cmdList):
            raise executionException("(engine) addCommand, invalid command index")
        
        topData = self.stack[-1][0]
        
        currentStartCmdIndex = 0
        if hasattr(topData,"cmdStartIndex"): #is there already a cmd start index ?
            currentStartCmdIndex = topData.cmdStartIndex
        
        currentStopCmdIndex = None
        if hasattr(topData,"cmdStopIndex"): #is there already a cmd stop index ?
            currentStopDataIndex = topData.cmdStopIndex
        
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
    
### DATA special meth (data of the top item on the stack) ###
    
    def flushData(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) flushData, no item on the stack")
    
        data = self.stack[-1][0]
        del data[:]
    
    def addData(self, newdata, offset=0):    
        if self.isEmptyStack(): 
            raise executionException("(engine) addData, no item on the stack")
    
        data = self.stack[-1][0]
        data.insert(offset,newdata)
    
    def removeData(self, offset=0):
        if self.isEmptyStack(): 
            raise executionException("(engine) removeData, no item on the stack")
    
        data = self.stack[-1][0]
        
        #valid offset ?
        if offset >= len(data) or offset < 0:
            raise executionException("(engine) setData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        #remove the data
        del data[offset]
    
    def setData(self, newdata, offset=0):
        if self.isEmptyStack(): 
            raise executionException("(engine) setData, no item on the stack")
    
        data = self.stack[-1][0]
        
        if offset >= len(data):
            raise executionException("(engine) setData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        data[offset] = newdata
    
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
        topData = self.stack[-1][0]
        
        #extract start/end command for the top data
        firstStartCmdIndex = 0
        if hasattr(topData,"cmdStartIndex"): #is there already a cmd start index ?
            firstStartCmdIndex = topData.cmdStartIndex
        
        firstStopCmdIndex = None
        if hasattr(topData,"cmdStopIndex"): #is there already a cmd stop index ?
            firstStopDataIndex = topData.cmdStopIndex
        
        for i in range(1,count):
            currentStackItem = self.stack[len(self.stack) - 1 - i]
            
            #extract and compare start/end command
            currentStartCmdIndex = 0
            if hasattr(currentStackItem[0],"cmdStartIndex"): #is there already a cmd start index ?
                currentStartCmdIndex = currentStackItem[0].cmdStartIndex
            
            currentStopCmdIndex = None
            if hasattr(currentStackItem[0],"cmdStopIndex"): #is there already a cmd stop index ?
                currentStopDataIndex = currentStackItem[0].cmdStopIndex
            
            if firstStartCmdIndex != currentStartCmdIndex and firstStopDataIndex != currentStopDataIndex:
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
        self.stack.append( (dataBunch, pathOnTop, actionToExecute, ) 
    
    def setCmdRange(self, firstCmd = 0, cmdLength = None, dataDepth = 0):
        #is empty stack ?
        if self.isEmptyStack(): 
            raise executionException("(engine) setCmdRange, no item on the stack")
        
        #is the dataDepth reachable
        if dataDepth < 0 or dataDepth > (len(self.stack)-1):
            raise executionException("(engine) setCmdRange, invalid depth value")
        
        stackItem = self.stack[(len(self.stack)-1)-dataDepth]
        #is it a pre ? (?)
        if stackItem[2] != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) setCmdRange, no need to put a cmd range on a pro/post process, there is only one command to execute")
            #the cmd range is always of length 1, no need to set cmd range
        
        #check the cmd limit
        currentCmdLength = len(self.cmdList[len(stackItem[1]) - 1])
    
        #the new index must be in the cmd range
        if firstCmd >= currentCmdLength:
            raise executionException("(engine) setCmdRange, firstCmd index is not in the command bound") 
        
        newStopIndex = None
        if cmdLength != None:
            if (firstCmd+cmdLength) > currentCmdLength:
                raise executionException("(engine) setCmdRange, cmdLength is bigger than the command list size")
                #we can not set cmdLength to None because if the user set a limit then add new command
                #is different of set a None limit then add command
            
            newStopIndex = firstCmd+cmdLength-1
        
        #the current cmd index must be in the cmd range
        currentCmdIndex = top[-1][1][-1]
        if currentCmdIndex < firstCmd or (cmdLength != None and (firstCmd+cmdLength-1) < currentCmdIndex):
            raise executionException("(engine) setDataCmdRange, the bounds must enclose the current cmd index") 
        
        ## get current limit ##
        currentStartCmdIndex = 0
        if hasattr(topData,"cmdStartIndex"): #is there already a cmd start index ?
            currentStartCmdIndex = topData.cmdStartIndex
        
        currentStopCmdIndex = None
        if hasattr(topData,"cmdStopIndex"): #is there already a cmd stop index ?
            currentStopDataIndex = topData.cmdStopIndex
        
        if currentStartCmdIndex == firstCmd and currentStopCmdIndex == newStopIndex:
            return #nothing to do, the limit are already set
        
        #set the cmd limit
        dataBunch = MultiOutput(stackItem[0])
        dataBunch.cmdStartIndex = firstCmd
        dataBunch.cmdStopIndex  = newStopIndex
        self.stack[(len(self.stack)-1)-dataDepth] = (dataBunch,stackItem[1],stackItem[2],)
        
    def splitData(self,splitAtDataIndex=0): #split the data into two separate stack item at the index, but will not change anything in the process order
        #is empty stack ?
        if self.isEmptyStack(): 
            raise executionException("(engine) splitData, no item on the stack")

        #is it a pre ? (?)
        if self.stack[-1][2] != PREPROCESS_INSTRUCTION:
            raise executionException("(engine) splitData, can't split the data of a PRO/POST process because it will not change anything on the execution")

        topdata = self.stack[-1][0]
        #split point exist ?
        if splitAtDataIndex < 0 or splitAtDataIndex > (len(topdata)-1):
            raise executionException("(engine) splitData, split index out of bound")

        #has enought data to split ?
        if len(topdata) < 2 or splitAtDataIndex = 0:
            return

        # get current cmd limit #
        currentStartCmdIndex = 0
        if hasattr(topData,"cmdStartIndex"): #is there already a cmd start index ?
            currentStartCmdIndex = topData.cmdStartIndex
        
        currentStopCmdIndex = None
        if hasattr(topData,"cmdStopIndex"): #is there already a cmd stop index ?
            currentStopDataIndex = topData.cmdStopIndex

        top = self.stack.pop()
        
        #from 0 to splitAtDataIndex
        dataBunch = MultiOutput(top[0][splitAtDataIndex:])
        dataBunch.cmdStartIndex = currentStartCmdIndex
        dataBunch.cmdStopIndex  = currentStopDataIndex
        path = top[1][:]
        path[-1] = 0 
        self.stack.append( (dataBunch, path, top[2], ) )
            
        #from splitAtDataIndex to the end
        dataBunch = MultiOutput(top[0][0:splitAtDataIndex])
        dataBunch.cmdStartIndex = currentStartCmdIndex
        dataBunch.cmdStopIndex  = currentStopDataIndex
        self.stack.append( (dataBunch, top[1], top[2], ) )
     
    def setDataCmdRange(self, startData = 0, dataLength=None, firstCmd = 0, cmdLength = None):
        if self.isEmptyStack(): 
            raise executionException("(engine) setDataCmdRange, no item on the stack")
        
        topData = self.stack[-1][0]
        
        if startData < 0:
            raise executionException("(engine) setDataCmdRange, startData must be bigger than zero")
        
        if startData > (len(topData)-1): #start index must be in the current data range
            raise executionException("(engine) setDataCmdRange, startData index is not in the data bounds")
        
        if dataLength < 1 and dataLength != None:
            raise executionException("(engine) setDataCmdRange, dataLength must be bigger than 1 or None")
    
        if dataLength != None and len(topData) < dataLength:
            raise executionException("(engine) setDataCmdRange, dataLength is too big in front of the size of the current data")

        #compute split points and dept level
        if dataLength == None:
            dept = 0
            if startData == 0:
                pass #no need to split
            else:
                self.splitData(startData)
        else:
            dept = 1
            if startData == 0:
                self.splitData(startData+dataLength)
            else:
                self.splitData(startData+dataLength)
                self.splitData(startData)
        
            splitPoints.append(startData)

        #set cmd range
        self.setCmdRange(firstCmd, cmdLength, dept)

    def getData(self, offset=0):
        if self.isEmptyStack(): 
            raise executionException("(engine) getData, no item on the stack")
            
        data = self.stack[-1][0]
        
        if offset >= len(data):
            raise executionException("(engine) getData, offset out of bound, the offset <"+str(offset)+"> can be reach because the data length is <"+str(len(data))+">")
        
        return data[offset]
        
    def hasNextData(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getData, no item on the stack")
            
        data = self.stack[-1][0]
        
        return len(data) > 1 #1 and not zero, because there are the current data and the next one
        
    def getRemainingDataCount(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getData, no item on the stack")
            
        data = self.stack[-1][0]
        
        return len(data)-1 # -1 because we don't care about the current data
        
        
### STACK meth ###
    def isEmptyStack(self):
        return len(self.stack) == 0
        
    def isLastStackItem(self):
        return len(self.stack) == 1
        
    def getStackSize(self):
        return len(self.stack)
        
### STACK ITEM meth ###
    def getCurrentItemMethodeType(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getCurrentMethodeType, no item on the stack")
    
        return self.stack[-1][2]
    
    def getCurrentItemData(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getCurrentMethodeType, no item on the stack")
            
        return self.stack[-1][0][:] #return a copy
        
    def getCurrentItemCmdPath(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getCurrentMethodeType, no item on the stack")
            
        return self.stack[-1][1][:] #return a copy
        
    def getCurrentItemCmdLimit(self):
        if self.isEmptyStack(): 
            raise executionException("(engine) getCurrentMethodeType, no item on the stack")
        
        dataTop = self.stack[-1][0]
        starting = 0
        if hasattr(dataTop,"cmdStartIndex") and dataTop.cmdStartIndex != None:
            starting = dataTop.cmdStartIndex

        end = len(self.cmdList[len(top[1]) -1]) - 1
        if hasattr(dataTop,"cmdStopIndex") and dataTop.cmdStopIndex != None:
            limit = dataTop.cmdStopIndex
            
        return (starting, end, )

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
            try:
                ## PRE PROCESS
                if top[2] == PREPROCESS_INSTRUCTION: #pre
                    r = self.executeMethod(subcmd.preProcess, top, useArgs)
                    subcmd.preCount += 1
                    
                    #manage result
                    if len(top[1]) == len(self.cmdList): #no child, next step will be a process
                        to_stack = (r, top[1], PROCESS_INSTRUCTION, )
                    else: #there are some child, next step will be another preprocess
                        new_path = top[1][:] #copy the path
                        new_path.append(0) #then add the first index of the next command
                        to_stack = (r, new_path, PREPROCESS_INSTRUCTION, )
                
                ## PROCESS ##
                elif top[2] == PROCESS_INSTRUCTION: #pro
                    r = self.executeMethod(subcmd.process, top, useArgs)
                    subcmd.proCount += 1
                    
                    #manage result
                    to_stack = (r, top[1], POSTPROCESS_INSTRUCTION,)
                
                ## POST PROCESS ##
                elif top[2] == POSTPROCESS_INSTRUCTION: #post
                    r = self.executeMethod(subcmd.postProcess, top, useArgs)
                    subcmd.postCount += 1
                    
                    #manage result
                    if len(top[1]) > 1: #not on the root node
                         to_stack = (r, top[1][:-1], POSTPROCESS_INSTRUCTION,) #just remove one item in the path to get the next postprocess to execute
                    
                else:
                    raise executionException("(engine) execute, unknwon process command <"+str(top[2])+">")
            
                if subcmd.preCount > DEFAULT_EXECUTION_LIMIT or subcmd.proCount > DEFAULT_EXECUTION_LIMIT or subcmd.postCount > DEFAULT_EXECUTION_LIMIT :
                    raise executionException("(engine) execute, this subcommand reach the execution limit count")
            
            except BaseException as e: #catch any execution exception, add more information then raise again
                e.EngineCmd          = cmd
                e.EngineSubCmdIndex  = top[1][-1]
                e.EngineData         = self.stack[-1][0][0]
                e.EngineProcess_type = top[2]
                
                raise e
            
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
                    
                        top[1][-1] = starting #select the first child
                        self.stack.append(  (top[0][1:],top[1],top[2],)  ) #remove the last used data, because every cmd already used id, and push on the stack
            
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
        if hasattr(cmd, "checker"):         
            data = cmd.checker.checkArgs(args, self)
        else:
            data = {}

        #execute Xprocess
        r = subcmd(**data)
        
        #r must be a multi output
        if not isinstance(r, MultiOutput):
            return [r]

        return r


