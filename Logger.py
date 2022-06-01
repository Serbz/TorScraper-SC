import os
import sys
import codecs
from colorama import init, Fore, Back, Style
import re
import asyncio
import io
HomeDir = r'Z:'
VarDir = HomeDir + r'\VariableVariables'
LogDir = HomeDir + r'\Logs'
StaticVarDir = HomeDir + r'\StaticVars'
SoundDir = HomeDir + r'\Sound'
ChromeDir = HomeDir + r'\Chrome'
ScriptDir = HomeDir + r'\SkrippitySkripz'
ImgDir = HomeDir + r'\ImageSearch'
SerbzDir = HomeDir + r'SerbzDir'

bcolorvar=0
init()








def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)







def LogPrint(Input):
    global bcolorvar
    strObj = str(Input).split('-')
    #print(str(strObj[0]))
    if (str(strObj[0]) == 'DM'):
        Input = f'{Style.RESET_ALL}{Fore.GREEN}{Input}{Style.RESET_ALL}'
        #Input = f'{Style.RESET_ALL}{Input}'
    if (('CheapHookah|6660' in str(Input)) or ('Melissa Viktoria|8228' in str(Input)) or ('Serbz|0001' in str(Input))):
        bcolorvar = 1
        Input = f'{Style.RESET_ALL}{Fore.RED}{Input}{Style.RESET_ALL}'
    if (('RedHunllef|6415' in str(Input)) or ('SerbzBBot|4800' in str(Input))):
        bcolorvar = 1
        Input = f'{Style.RESET_ALL}{Fore.YELLOW}{Input}{Style.RESET_ALL}'
        #Input = f'{Style.RESET_ALL}{Input}'
    if '328357828526080002' in str(Input) or '842215107467411478' in str(Input) or '842215105231585331' in str(Input):
        Input = f'{Style.RESET_ALL}{Fore.CYAN}{Input}{Style.RESET_ALL}'
        #Input = f'{Style.RESET_ALL}{Input}'
    else:
        if 'SerbzBBot|4800' in str(Input):
            Input = f'{Style.RESET_ALL}{Input}'
        else:
            bcolorvar = 0

    uprint(Input)
    StrConvert = str(Input).encode()
    with open(LogDir + r"pyOut2.txt", "a") as file_object:
        file_object.write(str(StrConvert) + "\n")
        file_object.close()
        return
        
        
        
        
#def AHK_Pass2(input):
#    StrConvert = str(input).encode()
#    with open(LogDir + "\pyOut.log", "a") as file_object:
#        file_object.write(str(StrConvert) + "\n")
#        file_object.close()
#    with open(VarDir + r"\command.txt", "a") as file_object:
#        file_object.write(input + "\n")
#        file_object.close()
#        return
#############################################
async def ValuesUpdater(line, val,filez=HomeDir + r"\variables.txt"):
    with open(filez, "r") as file:
        data = file.readlines()
    counter = 0
    with open(filez, 'w') as text_file:
    #text_file = open(HomeDir + r"\variables.txt", "w")
        text_file.write("#!#DO_NOT_REMOVE_OR_ADD_LINES#@#\n")
        counter = counter + 1
        for key in data:
            if counter >= len(data):
                break
            if counter == line:
                text_file.write(str(val) + "\n")
            else:
                text_file.write(str(data[counter]))
            counter = counter + 1
    return
#############################################
async def GetChanID():
    text_file = open(HomeDir + r"\variables.txt", "r")
    data = text_file.readlines()
    response = int(str(data[10]))
    return int(response)
#############################################
#def UpdateChanID(message):
#    text_file = open(VarDir + r"\ChannelID.txt", "w")
#    if message is not None:
#        response = str(message.channel.id)
#    text_file.write(str(response))
#    text_file.close()
#    return int(message.channel.id)
#############################################
#def AHK_Pass(command, ctx):
#    if command == "wake":
#        text_file = open(VarDir + r"wake.txt", "w")
#        text_file.write(str(ctx.author.name) + '|' + str(ctx.author.discriminator))
#        text_file.close()
#        return
#############################################
def MessageLogger(message):
    text_file = open(VarDir + r"\ChannelID.txt", "r")
    if message is not None:
        response = message.channel.name + '|' + message.author.name + '|' + message.author.discriminator + '|' + (
            message.content)
        LogPrint(response)
    tstring = text_file.read()
    text_file.close()
    return str(tstring)
#############################################
def Blacklist(message):
    text_file = open(StaticVarDir + r"\BlackList.txt")
    text_fileSplit = str(text_file.read()).strip().split("\n")
    for line in text_fileSplit:
        if line in message.content:
            text_file.close()
            return True
    text_file.close()
    return False
#############################################
def LogOSD(Input,guild=None,channel=None):
    StrConvert = str(Input).encode()
    #if guild != None:
        #if ('Samurai' in guild):
            #StrConvert = StrConvert[2:]
            #StrConvert = re.sub(r"|", " ", StrConvert)
    StrConvert = str(StrConvert)[2:]
    #StrConvert = re.sub(r"\|", "", StrConvert)
    text_file = open(HomeDir + "logs\OSDPrint.txt", "w")
    text_file.write(str(StrConvert))
    text_file.close()
    return