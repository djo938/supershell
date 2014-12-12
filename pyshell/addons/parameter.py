#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright (C) 2014  Jonathan Delvaux <pyshell@djoproject,net>

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#TODO
    #load/save 
        #if parameter is readonly AND exists
            #don't load anything from file for this parameter
                #except context index (if context)

            #so if readonly, no need to store object ?
                #no information is stored about the seed, so store it anyway
                    #seed could be addon or system

from pyshell.command.command   import UniCommand
from pyshell.loader.command    import registerStopHelpTraversalAt, registerCommand, registerSetTempPrefix
from pyshell.arg.decorator     import shellMethod
from pyshell.arg.argchecker    import defaultInstanceArgChecker,listArgChecker, environmentParameterChecker, tokenValueArgChecker, stringArgChecker, booleanValueArgChecker, contextParameterChecker
from pyshell.utils.parameter   import ParameterContainer,isAValidStringPath, Parameter, EnvironmentParameter, ContextParameter, VarParameter
from pyshell.utils.postProcess import stringListResultHandler,listResultHandler,printColumn, listFlatResultHandler
from pyshell.utils.constants   import PARAMETER_NAME, CONTEXT_ATTRIBUTE_NAME, ENVIRONMENT_ATTRIBUTE_NAME, ENVIRONMENT_PARAMETER_FILE_KEY, VARIABLE_ATTRIBUTE_NAME
from pyshell.utils.printing    import formatBolt, formatOrange
from pyshell.utils.exception   import ListOfException, DefaultPyshellException, PyshellException
import os 

## FUNCTION SECTION ##

#################################### GENERIC METHOD ####################################

def setProperties(key, propertyName, propertyValue, parameters, attributeType):
    param = getParameter(key, parameters, attributeType)
    
    if propertyName == "readonly":
        param.setReadOnly(propertyValue)
    elif propertyName == "removable":
        param.setRemovable(propertyValue)
    elif propertyName == "transient":
        param.setTransient(propertyValue)
    elif propertyName == "index_transient":
        param.setTransientIndex(propertyValue)
    else:
        raise Exception("Unknown property '"+str(propertyName)+"', one of these was expected: readonly/removable/transient/index_transient")

def getProperties(key, propertyName, parameters, attributeType):
    param = getParameter(key, parameters, attributeType)
    
    if propertyName == "readonly":
        return param.isReadOnly()
    elif propertyName == "removable":
        return param.isRemovable()
    elif propertyName == "transient":
        return param.isTransient()
    elif propertyName == "index_transient":
        return param.isTransientIndex()
    else:
        raise Exception("Unknown property '"+str(propertyName)+"', one of these was expected: readonly/removable/transient/index_transient")

def getParameter(key,parameters,attributeType):
    if not hasattr(parameters, attributeType):
        raise Exception("Unknow parameter type '"+str(attributeType)+"'")

    container = getattr(parameters, attributeType)

    if not container.hasParameter(key):
        raise Exception("Unknow parameter of type '"+str(attributeType)+"' with key '"+str(key)+"'")

    return container.getParameter(key)
    
def removeParameter(key, parameters, attributeType):
    if not hasattr(parameters, attributeType):
        raise Exception("Unknow parameter type '"+str(attributeType)+"'")

    container = getattr(parameters, attributeType)

    if not container.hasParameter(key):
        return #no job to do

    container.unsetParameter(key)

def _listGeneric(parameters, attributeType, key, formatValueFun, getTitleFun):
    #TODO re-apply a width limit on the printing, too big value will show a really big print on the terminal
        #use it in printing ?
            #nope because we maybe want to print something on the several line
            
        #a util function allow to retrieve the terminal width
            #if in shell only 
            #or script ? without output redirection

    if not hasattr(parameters, attributeType):
        raise Exception("Unknow parameter type '"+str(attributeType)+"'")

    container = getattr(parameters, attributeType)

    if key is None:
        key = ()
    else:
        state, result = isAValidStringPath(key)
        if not state:
            raise Exception(result)

        key = result

    #retrieve all value from corresponding mltries
    dico = container.mltries.buildDictionnary(key, True, True, False)

    toRet = [] 
    for subk,subv in dico.items():
        toRet.append( formatValueFun(subk, subv, formatOrange) )
    
    if len(toRet) == 0:
        return [("No var available",)]
    
    toRet.insert(0, getTitleFun(formatBolt) )
    return toRet

def _parameterRowFormating(key, paramItem, valueFormatingFun):

    if paramItem.isAListType():
        value = ', '.join(str(x) for x in paramItem.getValue())
    else:
        value = str(paramItem.getValue())

    return ("  "+".".join(key), valueFormatingFun(value), )

def _parameterGetTitle(titleFormatingFun):
    return (" "+titleFormatingFun("Name"), titleFormatingFun("Value"), )


@shellMethod(parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker(),
             key       = stringArgChecker())
def listParameter(parameters, key=None): #TODO use with a print column without header
    toPrint = []
    toPrint.append("") #TODO remove this when "print column without header" will be ready
    for subcontainername in ParameterContainer.SUBCONTAINER_LIST:
        if not hasattr(parameters, subcontainername):
            raise Exception("Unknow parameter type '"+str(attributeType)+"'")
            
        toPrint.append(formatBolt(subcontainername.upper()))
        toPrint.extend(_listGeneric(parameters, subcontainername, key, _parameterRowFormating, _parameterGetTitle))
        
    return toPrint

@shellMethod(filePath  = environmentParameterChecker(ENVIRONMENT_PARAMETER_FILE_KEY),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def loadParameter(filePath, parameter):
    "load parameters from the settings file"

    pass #TODO execute config script

    """    
    filePath = filePath.getValue()
    
    #load params
    config = None
    if os.path.exists(filePath):
        config = ConfigParser.RawConfigParser()
        try:
            config.read(filePath)
        except Exception as ex:
            raise ParameterLoadingException("(ParameterManager) load, fail to read parameter file : "+str(ex))
    else:
        #is there at least one parameter in one of the existing category ?
        emptyParameter = True
        for parentCategoryName,categoryList in parameter.params.items():
            if len(parameter.params[parentCategoryName]) > 0:
                emptyParameter = False
                break
        
        #if no parameter file, try to create it, then return
        if not emptyParameter:
            try:
                save(filePath, parameter)
            except Exception as ex:
                raise ParameterLoadingException("(ParameterManager) load, parameter file does not exist, fail to create it"+str(ex))
            return

    #read and parse, for each section
    errorList = ListOfException()
    for section in config.sections():
        specialSectionClassToUse = None
        for specialSectionClass in RESOLVE_SPECIAL_SECTION_ORDER:
            if not specialSectionClass.isParsable(config, section):
                continue
                
            specialSectionClassToUse = specialSectionClass
            break
        if specialSectionClassToUse != None:
        
            #a parent category with a similar name can not already exist (because of the structure of the parameter file)
            if section in parameter.params:
                errorList.addException(ParameterLoadingException("Section '"+str(section)+"', a parent category with this name already exist, can not create a "+specialSectionClassToUse.getStaticName()+" with this name"))
                continue
            
            #try to parse the parameter
            try:
                argument_dico = specialSectionClassToUse.parse(config, section)
            except PyshellException as ale:
                errorList.addException(ale)
                continue
            
            if section in parameter.params[specialSectionClassToUse.getStaticName()]:
                try:
                    parameter.params[specialSectionClassToUse.getStaticName()][section].setFromFile(argument_dico)
                except Exception as ex:
                    errorList.addException(ParameterLoadingException("(ParameterManager) load, fail to set information on "+specialSectionClassToUse.getStaticName()+" '"+str(section)+"' : "+str(ex)))
                    
            else:
                try:
                    parameter.params[specialSectionClassToUse.getStaticName()][section] = specialSectionClassToUse(**argument_dico)
                except Exception as ex:
                    errorList.addException(ParameterLoadingException("(ParameterManager) load, fail to create new "+specialSectionClassToUse.getStaticName()+" '"+str(section)+"' : "+str(ex)))
                    continue
    
        ### GENERIC ### 
        else:
            if section in FORBIDEN_SECTION_NAME:
                errorList.addException(ParameterLoadingException( "(ParameterManager) load, parent section name '"+str(section)+"' not allowed"))
                continue
        
            #if section in 

            for option in config.options(section):
                if section not in parameter.params:
                    parameter.params[section] = {}
                
                parameter.params[section][option] = VarParameter(config.get(section, option))
    
    #manage errorList
    if errorList.isThrowable():
        raise errorList
    
    #parameter.load()"""

@shellMethod(filePath  = environmentParameterChecker(ENVIRONMENT_PARAMETER_FILE_KEY),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def saveParameter(filePath, parameters):
    "save not transient parameters to the settings file"

    filePath = filePath.getValue()

    #with open(filePath, 'wb') as configfile:
    for subcontainername in ParameterContainer.SUBCONTAINER_LIST:
        container = getattr(parameters, subcontainername)
        dico = container.mltries.buildDictionnary((), True, True, False)

        for key, value in dico.items():
            if value.isTransient():
                continue

            #TODO manage type list
            #TODO prblm

            creationString = subcontainername+" create "+key+" "+getTypeFromInstance(value.typ.checker)+" "+",".join(value.getValue())+" -noErrorIfExists false"

            #TODO 
                #build instruction to create item
                #build instruction to save each property of the item

            pass #TODO


    """filePath = filePath.getValue()

    #manage standard parameter
    config = ConfigParser.RawConfigParser()
    for parent, childs in parameter.params.items():   
        if parent in FORBIDEN_SECTION_NAME:
            continue
        
        if parent == None:
            parent = MAIN_CATEGORY
        
        for childName, childValue in childs.items():
            if isinstance(childValue, Parameter):
                if childValue.isTransient():
                    continue
            
            #    value = str(childValue.getValue())
            #else:
            
            value = str(childValue)
        
            if not config.has_section(parent):
                config.add_section(parent)

            config.set(parent, childName, value)
    
    #manage context and environment
    for s in FORBIDEN_SECTION_NAME:
        if s in parameter.params:
            for contextName, contextValue in parameter.params[s].items():
                if contextValue.isTransient():
                    continue
            
                if not config.has_section(contextName):
                    config.add_section(contextName)

                for name, value in contextValue.getParameterSerializableField().items():
                    config.set(contextName, name, value)
    
    #create config directory
    #TODO manage if the directory already exist or if it is a file
        #TODO manage it in the other place where config is saved
    if not os.path.exists(os.path.dirname(filePath)):
        os.makedirs(os.path.dirname(filePath))

    #save file
    with open(filePath, 'wb') as configfile:
        config.write(configfile)
    
    #parameter.save()"""
        
def _createValuesFun(valueType, key, values, classDef, attributeType, noErrorIfExists, parameters, listEnabled): 
    if not hasattr(parameters, attributeType):
        raise Exception("Unknow parameter type '"+str(attributeType)+"'")

    container = getattr(parameters, attributeType)

    #build checker
    if listEnabled:
        checker = listArgChecker(valueType(),1)
    else:
        checker = valueType()
    
    if container.hasParameter(key) and not noErrorIfExists:
        raise Exception("Try to create a "+str(attributeType)+" with an existing key name '"+str(key)+"'")

    #check value
    value = checker.getValue(values, None, str(attributeType).title()+" "+key)
    container.setParameter(key, classDef(value, checker))
    
#################################### env management#################################### 

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def subtractEnvironmentValuesFun(key, values, parameters):
    "remove some elements from an environment parameter"
    param = getParameter(key, parameters, ENVIRONMENT_ATTRIBUTE_NAME)
    param.removeValues(values)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def removeEnvironmentContextValues(key, parameters):
    "remove an environment parameter"
    removeParameter(key, parameters, ENVIRONMENT_ATTRIBUTE_NAME)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getEnvironmentValues(key, parameters):
    "get an environment parameter value" 
    return getParameter(key, parameters, ENVIRONMENT_ATTRIBUTE_NAME).getValue()

@shellMethod(key           = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values        = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance(),1),
             parameters    = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def setEnvironmentValuesFun(key, values, parameters):
    "set an environment parameter value"
    
    envParam = getParameter(key, parameters, ENVIRONMENT_ATTRIBUTE_NAME)

    if envParam.isAListType():
        envParam.setValue(values)
    else:
        envParam.setValue(values[0])

@shellMethod(valueType       = tokenValueArgChecker({"any"    :defaultInstanceArgChecker.getArgCheckerInstance,
                                                     "string" :defaultInstanceArgChecker.getStringArgCheckerInstance, 
                                                     "integer":defaultInstanceArgChecker.getIntegerArgCheckerInstance,
                                                     "boolean":defaultInstanceArgChecker.getbooleanValueArgCheckerInstance, 
                                                     "float"  :defaultInstanceArgChecker.getFloatTokenArgCheckerInstance}),
             key             = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             value           = defaultInstanceArgChecker.getArgCheckerInstance(),
             noErrorIfExists = booleanValueArgChecker(),
             parameters      = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def createEnvironmentValueFun(valueType, key, value, noErrorIfExists=False, parameters=None): 
    "create an environment parameter value" 
    _createValuesFun(valueType, key, value, EnvironmentParameter, ENVIRONMENT_ATTRIBUTE_NAME, noErrorIfExists, parameters, False)

@shellMethod(valueType  = tokenValueArgChecker({"any"    :defaultInstanceArgChecker.getArgCheckerInstance,
                                               "string" :defaultInstanceArgChecker.getStringArgCheckerInstance, 
                                               "integer":defaultInstanceArgChecker.getIntegerArgCheckerInstance,
                                               "boolean":defaultInstanceArgChecker.getbooleanValueArgCheckerInstance, 
                                               "float"  :defaultInstanceArgChecker.getFloatTokenArgCheckerInstance}), 
             key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             noErrorIfExists=booleanValueArgChecker(),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def createEnvironmentValuesFun(valueType, key, values, noErrorIfExists=False, parameters=None): 
    "create an environment parameter value list" 
    _createValuesFun(valueType, key, values, EnvironmentParameter, ENVIRONMENT_ATTRIBUTE_NAME, noErrorIfExists, parameters, True)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def addEnvironmentValuesFun(key, values, parameters):
    "add values to an environment parameter list"
    param = getParameter(key, parameters, ENVIRONMENT_ATTRIBUTE_NAME)
    param.addValues(values)

def _envRowFormating(key, envItem, valueFormatingFun):
    if envItem.isAListType():
        return (".".join(key), "true", valueFormatingFun(', '.join(str(x) for x in envItem.getValue())), ) 
    else:
        return (".".join(key), "false", valueFormatingFun(str(envItem.getValue())), ) 

def _envGetTitle(titleFormatingFun):
    return (titleFormatingFun("Name"), titleFormatingFun("IsList"), titleFormatingFun("Value(s)"), )

@shellMethod(parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker(),
             key       = stringArgChecker())
def listEnvs(parameter, key=None):
    return _listGeneric(parameter, ENVIRONMENT_ATTRIBUTE_NAME, key, _envRowFormating, _envGetTitle)
    
@shellMethod(key           = stringArgChecker(),
             propertyName  = tokenValueArgChecker({"readonly":"readonly",
                                                   "removable":"removable",
                                                   "transient":"transient"}),
             propertyValue = defaultInstanceArgChecker.getbooleanValueArgCheckerInstance(),
             parameter     = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def setEnvironmentProperties(key, propertyName, propertyValue, parameter):
    setProperties(key, propertyName, propertyValue, parameter, ENVIRONMENT_ATTRIBUTE_NAME)
    
@shellMethod(key           = stringArgChecker(),
             propertyName  = tokenValueArgChecker({"readonly":"readonly",
                                                   "removable":"removable",
                                                   "transient":"transient"}),
             parameter     = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getEnvironmentProperties(key, propertyName, parameter):
    return getProperties(key, propertyName, parameter, ENVIRONMENT_ATTRIBUTE_NAME)

#################################### context management #################################### 

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def subtractContextValuesFun(key, values, parameters):
    "remove some elements from a context parameter"
    param = getParameter(key, parameters, CONTEXT_ATTRIBUTE_NAME)
    param.removeValues(values)

@shellMethod(valueType       = tokenValueArgChecker({"any"    :defaultInstanceArgChecker.getArgCheckerInstance,
                                               "string" :defaultInstanceArgChecker.getStringArgCheckerInstance, 
                                               "integer":defaultInstanceArgChecker.getIntegerArgCheckerInstance,
                                               "boolean":defaultInstanceArgChecker.getbooleanValueArgCheckerInstance, 
                                               "float"  :defaultInstanceArgChecker.getFloatTokenArgCheckerInstance}), 
             key             = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values          = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             noErrorIfExists = booleanValueArgChecker(),
             parameter       = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def createContextValuesFun(valueType, key, values, noErrorIfExists=False, parameter=None): 
    "create a context parameter value list"
    _createValuesFun(valueType, key, values, ContextParameter, CONTEXT_ATTRIBUTE_NAME, noErrorIfExists, parameter, True)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter  = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def removeContextValues(key, parameter):
    "remove a context parameter"
    removeParameter(key, parameter, CONTEXT_ATTRIBUTE_NAME)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter  = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getContextValues(key, parameter): 
    "get a context parameter value" 
    return getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).getValue()

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance(),1),
             parameter  = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def setContextValuesFun(key, values, parameter):
    "set a context parameter value"
    getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).setValue(values)

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def addContextValuesFun(key, values, parameters):
    "add values to a context parameter list"    
    param = getParameter(key, parameters, CONTEXT_ATTRIBUTE_NAME)
    param.addValues(values)

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             value     = defaultInstanceArgChecker.getArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def selectValue(key, value, parameter):
    "select the value for the current context"
    getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).setIndexValue(value)
    
@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             index     = defaultInstanceArgChecker.getIntegerArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def selectValueIndex(key, index, parameter):
    "select the value index for the current context"
    getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).setIndex(index)

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getSelectedContextValue(key, parameter):
    "get the selected value for the current context"
    return getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).getSelectedValue()

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getSelectedContextIndex(key, parameter):
    "get the selected value index for the current context"
    return getParameter(key,parameter,CONTEXT_ATTRIBUTE_NAME).getIndex()

def _conRowFormating(key, conItem, valueFormatingFun):
    return (".".join(key), str(conItem.getIndex()), valueFormatingFun(str(conItem.getSelectedValue())), ', '.join(str(x) for x in conItem.getValue()), )

def _conGetTitle(titleFormatingFun):
    return (titleFormatingFun("Name"), titleFormatingFun("Index"), titleFormatingFun("Value"), titleFormatingFun("Values"), )

@shellMethod(parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker(),
             key       = stringArgChecker())
def listContexts(parameter, key=None):
    "list every existing contexts"
    return _listGeneric(parameter, CONTEXT_ATTRIBUTE_NAME, key, _conRowFormating, _conGetTitle)
    
@shellMethod(key           = stringArgChecker(),
             propertyName  = tokenValueArgChecker({"readonly":"readonly",
                                                   "removable":"removable",
                                                   "transient":"transient",
                                                   "index_transient":"index_transient"}),
             propertyValue = defaultInstanceArgChecker.getbooleanValueArgCheckerInstance(),
             parameter     = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def setContextProperties(key, propertyName, propertyValue, parameter):
    "set a context property"
    setProperties(key, propertyName, propertyValue, parameter, CONTEXT_ATTRIBUTE_NAME)
    
@shellMethod(key           = stringArgChecker(),
             propertyName  = tokenValueArgChecker({"readonly":"readonly",
                                                   "removable":"removable",
                                                   "transient":"transient",
                                                   "index_transient":"index_transient"}),
             parameter     = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getContextProperties(key, propertyName, parameter):
    "get a context property"
    return getProperties(key, propertyName , parameter, CONTEXT_ATTRIBUTE_NAME)

#################################### var management #################################### 

#################################################### beginning OF POC

@shellMethod(key    = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             engine = defaultInstanceArgChecker.getEngineChecker())
def pre_addValues(key, values, engine=None):
    
    cmd = engine.getCurrentCommand()
    cmd.dynamicParameter["key"]      = key
    cmd.dynamicParameter["disabled"] = False

    return values

@shellMethod(values = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             engine = defaultInstanceArgChecker.getEngineChecker())
def pro_addValues(values, engine):

    #if no previous command, default behaviour
    if not engine.hasPreviousCommand():
        return values

    #if not, clone this command and add it at the end of cmd list
    cmd = engine.getCurrentCommand()
    cmdClone = cmd.clone()
    engine.addCommand(cmdClone, convertProcessToPreProcess = True)

    for k,v in cmd.dynamicParameter.items():
        cmdClone.dynamicParameter[k] = v

    cmd.dynamicParameter["disabled"] = True
    cmdClone.dynamicParameter["disabled"] = True

    #TODO execute previous

    return values

@shellMethod(values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker(),
             engine     = defaultInstanceArgChecker.getEngineChecker())
def post_addValues(values, parameters=None, engine=None):
    "add values to a var"   
    
    cmd = engine.getCurrentCommand()

    if cmd.dynamicParameter["disabled"]:
        return values

    key = cmd.dynamicParameter["key"]

    if parameters.variable.hasParameter(key):
        param = getParameter(key, parameters, VARIABLE_ATTRIBUTE_NAME)
        param.addValues(values)
    else:
        parameters.variable.setParameter(key,VarParameter(values))

    return values

#################################################### END OF POC

@shellMethod(key        = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values     = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameters = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def subtractValuesVar(key, values, parameters=None):
    "remove existing value from a variable, remove first occurence met"
    param = getParameter(key, parameters, VARIABLE_ATTRIBUTE_NAME)
    param.removeValues(values)

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             values    = listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def setVar(key, values, parameter):
    "assign a value to a variable"
    parameter.variable.setParameter(key,VarParameter(values))

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def getVar(key, parameter):
    "get the value of a variable"
    return getParameter(key, parameter, VARIABLE_ATTRIBUTE_NAME).getValue()

@shellMethod(key       = defaultInstanceArgChecker.getStringArgCheckerInstance(),
             parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker())
def unsetVar(key, parameter):
    "unset a variable, no error if does not exist"
    removeParameter(key, parameter, VARIABLE_ATTRIBUTE_NAME)

def _varRowFormating(key, varItem, valueFormatingFun):
    return (".".join(key), valueFormatingFun(', '.join(str(x) for x in varItem.getValue())), )

def _varGetTitle(titleFormatingFun):
    return ( titleFormatingFun("Name"),titleFormatingFun("Values"), )

@shellMethod(parameter = defaultInstanceArgChecker.getCompleteEnvironmentChecker(),
             key       = stringArgChecker())
def listVars(parameter, key=None):
    "list every existing variables"
    return _listGeneric(parameter, VARIABLE_ATTRIBUTE_NAME, key, _varRowFormating, _varGetTitle)

#################################### REGISTER SECTION #################################### 

#var 
registerSetTempPrefix( ("var", ) )
registerCommand( ("set",) ,                    post=setVar)
registerCommand( ("get",) ,                    pre=getVar, pro=stringListResultHandler)
registerCommand( ("unset",) ,                  pro=unsetVar)
registerCommand( ("list",) ,                   pre=listVars, pro=printColumn)
registerCommand( ("add",) ,                    pre=pre_addValues, pro=pro_addValues, post=post_addValues)
registerCommand( ("subtract",) ,               post=subtractValuesVar)
registerStopHelpTraversalAt( ("var",) )

#context 
registerSetTempPrefix( (CONTEXT_ATTRIBUTE_NAME, ) )
registerCommand( ("unset",) ,              pro=removeContextValues)
registerCommand( ("get",) ,                pre=getContextValues, pro=listResultHandler)
registerCommand( ("set",) ,                post=setContextValuesFun)
registerCommand( ("create",) ,             post=createContextValuesFun)
registerCommand( ("add",) ,                post=addContextValuesFun)
registerCommand( ("subtract",) ,           post=subtractContextValuesFun)
registerCommand( ("value",) ,              pre=getSelectedContextValue, pro=listFlatResultHandler)
registerCommand( ("index",) ,              pre=getSelectedContextIndex, pro=listFlatResultHandler)
registerCommand( ("select", "index",) ,    post=selectValueIndex)
registerCommand( ("select", "value",) ,    post=selectValue)
registerCommand( ("list",) ,               pre=listContexts, pro=printColumn)
registerCommand( ("properties","set") ,    pro=setContextProperties)
registerCommand( ("properties","get"),     pre=getContextProperties, pro=listFlatResultHandler)
registerStopHelpTraversalAt( (CONTEXT_ATTRIBUTE_NAME,) )

#env 
registerSetTempPrefix( (ENVIRONMENT_ATTRIBUTE_NAME, ) )
registerCommand( ("list",) ,           pro=listEnvs,   post=printColumn )
registerCommand( ("create","single",), post=createEnvironmentValueFun)
registerCommand( ("create","list",),   post=createEnvironmentValuesFun)
registerCommand( ("get",) ,            pre=getEnvironmentValues, pro=listResultHandler)
registerCommand( ("unset",) ,          pro=removeEnvironmentContextValues)
registerCommand( ("set",) ,            post=setEnvironmentValuesFun)
registerCommand( ("add",) ,            post=addEnvironmentValuesFun)
registerCommand( ("subtract",) ,       post=subtractEnvironmentValuesFun)
registerCommand( ("properties","set"), pro=setEnvironmentProperties) 
registerCommand( ("properties","get"), pre=getEnvironmentProperties, pro=listFlatResultHandler) 
registerStopHelpTraversalAt( (ENVIRONMENT_ATTRIBUTE_NAME,) ) 

#parameter
registerSetTempPrefix( (PARAMETER_NAME, ) )
registerCommand( ("save",) ,           pro=saveParameter)
registerCommand( ("load",) ,           pro=loadParameter)
registerCommand( ("list",) ,           pro=listParameter, post=printColumn)
registerStopHelpTraversalAt( (PARAMETER_NAME,) )
    
