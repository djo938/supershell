#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if sys.version_info[0] < 2 or (sys.version_info[0] < 3 and sys.version_info[0] < 7):
    from pyshell.utils.ordereddict import OrderedDict #TODO get from pipy, so the path will change
else:
    from collections import OrderedDict 
    
from argchecker import ArgChecker, defaultValueChecker
from argfeeder import ArgFeeder
from exception import decoratorException
import inspect, types

###############################################################################################
##### UTIL FUNCTION ###########################################################################
###############################################################################################

class funAnalyser(object):
    def __init__(self, fun):
        #is a function ?
        if type(fun) == types.MethodType:
            self.classMethod = True
        elif type(fun) != types.FunctionType:
            raise decoratorException("(funAnalyser) init faile, need a function instance, got <"+str(type(fun))+">")
        else:
            self.classMethod = False
        
        self.fun = fun
        self.inspect_result = inspect.getargspec(fun)
        

        #how much default value ?
        if self.inspect_result.defaults == None:
            self.lendefault = 0
        else:
            self.lendefault = len(self.inspect_result.defaults)

    def has_default(self, argname):
        #existing argument ?
        if argname not in self.inspect_result.args:
            raise decoratorException("(decorator) unknonw argument <"+str(argname)+"> at function <"+self.fun.__name__+">")

        return not ( (self.inspect_result.args.index(argname) < (len(self.inspect_result.args) - self.lendefault)) )

    def get_default(self,argname):
        #existing argument ?
        if argname not in self.inspect_result.args:
            raise decoratorException("(decorator) unknonw argument <"+str(argname)+"> at function <"+self.fun.__name__+">")

        index = self.inspect_result.args.index(argname)
        if not (index < (len(self.inspect_result.args) - self.lendefault)):
            return self.inspect_result.defaults[index - (len(self.inspect_result.args) - len(self.inspect_result.defaults))]
        
        raise decoratorException("(decorator) no default value to the argument <"+str(argname)+"> at function <"+self.fun.__name__+">")

    def setCheckerDefault(self, argname,checker):
        if self.has_default(argname):
            checker.setDefaultValue(self.get_default(argname))

        return checker


###############################################################################################
##### DECORATOR ###############################################################################
###############################################################################################

#def shellMethod(suffix,**argList):
def shellMethod(**argList):
    #no need to check collision key, it's a dictionary

    #check the checkers
    for key,checker in argList.iteritems():
        if not isinstance(checker,ArgChecker):
            raise decoratorException("(shellMethod decorator) the checker linked to the key <"+key+"> is not an instance of ArgChecker")

    #define decorator method
    def decorator(fun):
        #is there already a decorator ?
        if hasattr(fun, "checker"):
            raise decoratorException("(decorator) the function <"+fun.__name__+"> has already a shellMethod decorator")
    
        #inspect the function
        analyzed_fun = funAnalyser(fun)
        
        argCheckerList = OrderedDict()
        for i in range(0,len(analyzed_fun.inspect_result.args)):
        #for argname in analyzed_fun.inspect_result.args:
            argname = analyzed_fun.inspect_result.args[i]
            
            #don't care about the self arg, the python framework will manage it
            if i == 0 and analyzed_fun.classMethod and argname == "self":
                continue
            
            if argname in argList: #check if the argname is in the argList
                #print argList
                checker = argList[argname]
                del argList[argname]
                
                #check the compatibilty with the previous argument checker
                if checker.needData() and len(argCheckerList) > 0:
                    previousName,previousChecker = list(a.items())[-1]
                    
                    #check if the previous checker remain a few arg to the following or not
                    if previousChecker.isVariableSize() and previousChecker.maximumSize == None:
                        raise decoratorException("(decorator) the previous argument <"+str(previousName)+"> has an infinite variable size, you can't add a new argment <"+str(argname)+"> at function <"+fun.__name__+">")
            
                argCheckerList[argname] = analyzed_fun.setCheckerDefault(argname,checker)
            elif analyzed_fun.has_default(argname): #check if the arg has a DEFAULT value
                argCheckerList[argname] = defaultValueChecker(analyzed_fun.get_default(argname))
            else:
                raise decoratorException("(shellMethod decorator) the arg <"+argname+"> is not used and has no default value")
        
        #All the key are used in the function call?
        keys = argList.keys()
        if len(keys) > 0:
            string = ",".join(argList.keys())
            raise decoratorException("(shellMethod decorator) the following key(s) had no match in the function prototype : <"+string+">")
        
        #set the checker on the function
        fun.checker = ArgFeeder(argCheckerList)
    
        return fun
    
    return decorator

