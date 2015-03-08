#!/usr/bin/python
# -*- coding: utf-8 -*-

#Copyright (C) 2014  Jonathan Delvaux <pyshell@djoproject.net>

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

from apdu.readers.acr38u         import acr38uAPDUBuilder
from pyshell.loader.command      import registerStopHelpTraversalAt, registerCommand, registerSetGlobalPrefix, registerSetTempPrefix
from pyshell.arg.decorator       import shellMethod
from pyshell.arg.argchecker      import defaultInstanceArgChecker,listArgChecker, IntegerArgChecker, tokenValueArgChecker, booleanValueArgChecker, keyStoreTranslatorArgChecker
from pyshell.command.exception   import engineInterruptionException
from pyshell.utils.postProcess   import printStringCharResult, printBytesAsString

@shellMethod(anything=listArgChecker(defaultInstanceArgChecker.getArgCheckerInstance()))
def stopAsMainProcess(anything):
    #TODO in place of printing an error, print a description of the apdu (class, ins, length, ...)

    raise engineInterruptionException("An acr38 command can not be directly executed, this command need to be piped into a transmit command",False)

@shellMethod(cardType = tokenValueArgChecker(acr38uAPDUBuilder.SELECT_TYPE))
def selectFun(cardType = "AUTO"):
    return acr38uAPDUBuilder.selectType(cardType)

"""@shellMethod(address = IntegerArgChecker(0,0x3ff),
             length  = IntegerArgChecker(0,0xff))
def readFun(address = 0, length = 0):
    return acr38uAPDUBuilder.read(address, length)

@shellMethod(datas   = listArgChecker(IntegerArgChecker(0,255)),
             address = IntegerArgChecker(0,65535))
def writeFun(datas, address=0):
    return acr38uAPDUBuilder.write(address, datas)

@shellMethod(pin = listArgChecker(IntegerArgChecker(0,255),2,2))
def checkPin(pin):
    return acr38uAPDUBuilder.checkPinCode(pin)"""


## I2C ##
    #TODO should be splited into 16k and 1024k ??? 

@shellMethod(cardType=tokenValueArgChecker({"I2C_1KTO16K" : acr38uAPDUBuilder.TYPE_I2C_1KTO16K,"I2C_32KTO1024K" : acr38uAPDUBuilder.TYPE_I2C_32KTO1024K}))
def I2C_select(cardType = "I2C_1KTO16K"):
    return acr38uAPDUBuilder.selectType(cardType)

@shellMethod(size=tokenValueArgChecker(acr38uAPDUBuilder.I2C_PAGE_SIZE))
def I2C_selectPageSize(size = "8BYTES"):
    return acr38uAPDUBuilder.I2C_selectPageSize(size)

@shellMethod(adress = IntegerArgChecker(0,0x1ffff),
             length = IntegerArgChecker(0,0xff))
def I2C_read(adress = 0, length = 0):
    return acr38uAPDUBuilder.read(adress, length)

@shellMethod(adress = IntegerArgChecker(0,0x1ffff),
             datas = listArgChecker(IntegerArgChecker(0,255)))
def I2C_write(datas, adress = 0):
    return acr38uAPDUBuilder.write(adress, datas)

## SLE ##

## ATMEL ##

### REGISTERING PART ###

## MISC ##

registerSetGlobalPrefix( ("acr38", ) )
registerCommand( ( "select",),   pre=selectFun, pro=stopAsMainProcess) 
#registerCommand( ( "read",),  pre=readFun, pro=stopAsMainProcess) 
#registerCommand( ( "write",),  pre=writeFun, pro=stopAsMainProcess) 
#registerSetTempPrefix( ("pin", ) )
#registerCommand( ( "check",),  pre=checkPin, pro=stopAsMainProcess) 

## IC2 ##

registerSetTempPrefix( ("ic2",) )
registerCommand( ( "select",),     pre=I2C_select,         pro=stopAsMainProcess)
registerCommand( ( "pagesize",),   pre=I2C_selectPageSize, pro=stopAsMainProcess)
registerCommand( ( "read",),       pre=I2C_read,           pro=stopAsMainProcess)
registerCommand( ( "write",),      pre=I2C_write,          pro=stopAsMainProcess)





