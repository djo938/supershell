#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] < 2 or (sys.version_info[0] < 3 and sys.version_info[0] < 7):
    from pyshell.utils.ordereddict import OrderedDict #TODO get from pipy, so the path will change
else:
    from collections import OrderedDict 
    
from exception import *

###############################################################################################
##### ArgsChecker #############################################################################
###############################################################################################
class ArgsChecker():
    "abstract arg checker"

    #
    # @argsList, une liste de string
    # @return, un dico trie des arguments et de leur valeur : <name,value>
    # 
    def checkArgs(self,argsList, engine=None):
        pass #XXX to override
        
    def usage(self):
        pass #XXX to override
    
class ArgFeeder(ArgsChecker):

    #
    # @param argTypeList, une liste de tuple (Argname,ArgChecker) 
    #
    def __init__(self,argTypeList):
        #take an ordered dict as argTypeList parameter  
        if not isinstance(argTypeList,OrderedDict) and  ( not isinstance(argTypeList, dict) or len(argTypeList) != 0): 
            raise argInitializationException("(ArgFeeder) argTypeList must be a valid instance of an ordered dictionnary")
        
        self.argTypeList = argTypeList
        
    #
    # @argsList, une liste de string
    # @return, un dico trie des arguments et de leur valeur : <name,value>
    # 
    def checkArgs(self,argsList, engine=None):
        if not isinstance(argsList,list):
            # argsList must be a string
            if type(argsList) != str and type(argsList) != unicode:
                raise argException("(ArgFeeder) string list was expected, got <"+str(type(argsList))+">")
        
            argsList = [argsList]
            
            #no need to check the other args, they will be checked into the argcheckers
    
        ret             = {}
        argCheckerIndex = 0
        dataIndex       = 0
        
        for (name,checker) in self.argTypeList.iteritems():
            #set the engine
            checker.setEngine(engine)
        
            #is there a minimum limit
            if checker.minimumSize != None:
                #is there at least minimumSize item in the data stream?
                if len(argsList[dataIndex:]) < checker.minimumSize:
                    #no more string token, end of stream ?
                    if len(argsList[dataIndex:]) == 0:
                        #we will check if there is some default value
                        break 
                    else:
                        #there are data but not enough
                        raise argException("(ArgFeeder) not enough data for the argument <"+name+">")
            
            #is there a maximum limit?
            if checker.maximumSize == None:
                #No max limit, it consumes all remaining data
                ret[name] = checker.getValue(argsList[dataIndex:],dataIndex)
                dataIndex = len(argsList) #will not stop the loop but will notify that every data has been consumed
            else:
                #special case: checker only need one item? (most common case)
                if checker.minimumSize != None and checker.minimumSize == checker.maximumSize == 1:
                    value = argsList[dataIndex:(dataIndex+checker.maximumSize)][0]
                else:
                    value = argsList[dataIndex:(dataIndex+checker.maximumSize)]
                    
                ret[name] = checker.getValue(value,dataIndex)
                dataIndex += checker.maximumSize

            argCheckerIndex += 1
        
        # MORE THAN THE LAST ARG CHECKER HAVEN'T BEEN CONSUMED YET
        items_list = list(self.argTypeList.items())
        for i in range(argCheckerIndex,len(self.argTypeList)):
            (name,checker) = items_list[i]
                
            if checker.hasDefaultValue():
                ret[name] = checker.getDefaultValue()
            else:
                raise argException("(ArgFeeder) some arguments aren't bounded, missing data : <"+name+">")

        #don't care about unused data in argsList, if every parameter are binded, we are happy :)

        return ret
        
    def usage(self):
        if len(self.argTypeList) == 0:
            return "no args needed"
    
        ret = ""
        firstMandatory = False
        for (name,checker) in self.argTypeList.iteritems():
            if not checker.showInUsage:
                continue
        
            if checker.hasDefaultValue() and not firstMandatory:
                ret += "["
                firstMandatory = True
            
            ret += name+":"+checker.getUsage()+" "
        
        ret = ret.strip()
        
        if firstMandatory:
            ret += "]"
        
        return ret
