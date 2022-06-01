from __future__ import unicode_literals
try:

    import asyncio
    import os
    import re
    import pickle
    import sys
    from string import ascii_lowercase
    from typing import List
    import traceback
    #from discord.errors import Forbidden, HTTPException, NotFound
    #import discord
    import numpy
    #from discord.ext import commands
    #from discord.ext.commands import CommandNotFound, Bot
    from dotenv import load_dotenv
    from collections import namedtuple
    import signal
    import logging
    import random
    from io import StringIO
    #import gzip, getopt
    #try:
    #    from pafy import new
    #except:
    #    os.system("pip install youtube_dl")
    #    from pafy import new
    #    pass
    #from pyscreenshot import FailedBackendError
    from lxml import etree
    from bs4 import BeautifulSoup, SoupStrainer
    #from win32api import GetSystemMetrics
    #from mmappickle import mmapdict
    import socks
    import socket
    import requests
    #import fnmatch
    import json
    import re
    import codecs
    import urllib
    import time as t
    import urllib.request
    #import Logger



    botIterator = 0
    g3_counter = 0
    linksArray = []
    # bots[0].run(TOKEN)
    # Configuration
    # SOCKS5_PROXY_HOST = '10.0.1.10'
    # SOCKS5_PROXY_PORT = 9100
    proxies = [
        {
            'http': 'socks5h://10.0.1.10:9100',
            'https': 'socks5h://10.0.1.10:9100'
        }, {
            'http': 'socks5h://10.0.1.10:9106',
            'https': 'socks5h://10.0.1.10:9106'

        }, {
            'http': 'socks5h://10.0.1.10:9105',
            'https': 'socks5h://10.0.1.10:9105'
        }, {
            'http': 'socks5h://10.0.1.10:9104',
            'https': 'socks5h://10.0.1.10:9104'
        }, {
            'http': 'socks5h://10.0.1.10:9103',
            'https': 'socks5h://10.0.1.10:9103'
        }, {
            'http': 'socks5h://10.0.1.10:9102',
            'https': 'socks5h://10.0.1.10:9102'
        }, {
            'http': 'socks5h://10.0.1.10:9101',
            'https': 'socks5h://10.0.1.10:9101'
        }, {
            'http': 'socks5h://10.0.1.10:9109',
            'https': 'socks5h://10.0.1.10:9109'
        }, {
            'http': 'socks5h://10.0.1.10:9108',
            'https': 'socks5h://10.0.1.10:9108'
        }, {
            'http': 'socks5h://10.0.1.10:9111',
            'https': 'socks5h://10.0.1.10:9111'
        }, {
            'http': 'socks5h://10.0.1.10:9112',
            'https': 'socks5h://10.0.1.10:9112'
        }, {
            'http': 'socks5h://10.0.1.10:9113',
            'https': 'socks5h://10.0.1.10:9113'
        }, {
            'http': 'socks5h://10.0.1.10:9114',
            'https': 'socks5h://10.0.1.10:9114'
        }, {
            'http': 'socks5h://10.0.1.10:9115',
            'https': 'socks5h://10.0.1.10:9115'
        }, {
            'http': 'socks5h://10.0.1.10:9116',
            'https': 'socks5h://10.0.1.10:9116'
        }, {
            'http': 'socks5h://10.0.1.10:9117',
            'https': 'socks5h://10.0.1.10:9117'
        }, {
            'http': 'socks5h://10.0.1.10:9118',
            'https': 'socks5h://10.0.1.10:9118'
        }, {
            'http': 'socks5h://10.0.1.10:9119',
            'https': 'socks5h://10.0.1.10:9119'
        }
    ]

    proxy = {'http': 'socks5h://10.0.1.21:9068','https': 'socks5h://10.0.1.21:9068'}
    loop = asyncio.get_event_loop()
    taskloopsINIT = []

    # outputs proxy IP)
    dataSets = []

    proxyRetry = 0
    stopScrape = False

    def scrapeWithSoup0(URL):
        URL = url
        print(str(URL[27:]))
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }
        data = requests.get(URL, timeout=15, headers=headers).text
        soup = BeautifulSoup(data, features="lxml")

        linksArray = []
        img_tags = soup.find_all('img')
        if "imgur" in URL:
            urls = [img['src'] for img in img_tags]
        for url in urls:
            # print(url)
            if str(url)[:2] == "//":
                url = str(url)[2:]
            if ("imgur" in str(url) or "reddit" in str(url)):
                if not "http" in str(url):
                    url = f"https://{url}"
                    url = url.strip()
                    url = url.split(".com")
                    url = f"{url[0]}.com:443{url[1]}"
                linksArray.append(url)
        print(linksArray)
        return linksArray
        
    async def torscrape():
        with open(HomeDir + fr"\params.txt", "r") as paramFile:
            out = str(paramFile.read())
            varsSplit = str(out).split("\n")
        paramFile.close()
        counter = -1
        duplicateCheck = varsSplit[1]
        source = varsSplit[3]
        scrapeArray = []
        URL = varsSplit[5]
        file = varsSplit[7]
        #filePath = ""
        filePath = HomeDir + r"\\" + str(file)
        sourcePath = ""
        scrape = varsSplit[9]
        merge = varsSplit[11]
        linksArray = [URL]
        sourceArray = []
        iterationCount = int(varsSplit[13])
        strFileSourceURL = ""
        strModes = ""
        strIteration = ""
        ms2eString = ""
        #for each in str(ctx.message.content).split(" "):
        #    counter = counter + 1
        #    if counter != 0:
        #        if each == "-file": #torscrape -file someSaveFile -sourceOR-url /scrape
        #            file = str(ctx.message.content).split(" ")[counter + 1]
        #            #filePath = HomeDir + str(file) + ".npy"
        #            filePath = r"Saves/torScraper/" + str(file) + ".npy"
        #            print(str(filePath) + "\n")
        #            strFileSourceURL = strFileSourceURL + "File set as: " + str(filePath) + "\n"
        #        if each == "-source":
        #            source = str(ctx.message.content).split(" ")[counter + 1]
        #            sourcePath = HomeDir + str(source) + ".npy"
        #            print(str(sourcePath) + "\n")
        #            strFileSourceURL = strFileSourceURL + "Source set as: " + str(sourcePath) + "\n"
        #        if each == "-url":
        #            URL = str(ctx.message.content).split(" ")[counter + 1]
        #            print(str(URL))
        #            linksArray = [URL]
        #            print(str(linksArray) + "\n")
        #            strFileSourceURL = strFileSourceURL + "URL for source set as: " + str(URL) + "\n"
        #        if each == "/scrape":
        #            scrape = 1
        #            print("scrape" + str(scrape) + "\n")
        #            strModes = strModes + "Scrape set to: " + str(bool(scrape)) + "\n"
        #        if each == "/dupecheck":
        #            duplicateCheck = 1
        #            print("duplicateCheck" + str(duplicateCheck) + "\n")
        #            strModes = strModes + "duplicateCheck set to: " + str(bool(duplicateCheck)) + "\n"
        #        if each == "/merge":
        #            duplicateCheck = 1
        #            merge = 1
        #            print("merge" + str(merge))
        #            print("duplicateCheck" + str(duplicateCheck) + "\n")
        #            strModes = strModes + "merge set to: " + str(bool(merge)) + "\n"
        #        if each == "-count" and scrape == 1:
        #            try:
        #                iterationCount = int(str(ctx.message.content).split(" ")[counter + 1])
        #                if iterationCount < 1:
        #                    await ctx.send("iteration count can not be less than 1")
        #                    return
        #                print("iterationCount" + str(iterationCount) + "\n")
        #                strIteration = strIteration + "Iteration count set to: " + str(iterationCount) + "\n"
        #            except TypeError:
        #                await ctx.send("-count must specify a number and can only be used with /scrape")
        #                return

        if iterationCount >= 1 and scrape == 0:
            #await ctx.send("-count must specify a number and can only be used with /scrape")
            return
        if iterationCount == 0:
            iterationCount = 1
            strIteration = strIteration + "Iteration count not specified, Iteration set to: " + str(iterationCount) + "\n"
        msgString = strFileSourceURL + strModes + strIteration
        #await ctx.send("```json\n" + str(msgString) + "```")
        ##Sanity checks##
        if (duplicateCheck == 1 or merge == 1) and file == "" and source == "":
            #await ctx.send("must specify -file -source for dupe checking")
            return
        if URL == "" and source == "":
            #await ctx.send("must specify either URL OR Source AND file")
            return
        if file == source:
            #await ctx.send("file and source cannot be the same")
            return
        if file == "":
            #await ctx.send("must specify atleast a save file")
            return
        #get URL#
        if URL != "NaN" and source == "":
            #await ctx.send("scraping from scratch, no source file specified")
            newScrape = 1
            print(fr"newScrape {newScrape}")
        else:
            newScrape = 0
        if duplicateCheck == 1 or merge == 1:
            await dupeCheck(source, file)
            if merge == 1:
                scrapeArray = await combineScrapes(file, source)
        sourceSize = 0
        if source != "" or newScrape == 0 and duplicateCheck != 1:
            sourcePath = HomeDir + str(source) + ".npy"
            sourceArray = numpy.load(sourcePath, mmap_mode="r")#, allow_pickle=True)#allow_pickle=True, delimiter=r",")
            sourceArray2 = numpy.load(sourcePath)#, allow_pickle=True)#allow_pickle=True, delimiter=r",")
            #sourceSize = int(find_between(str(sourceArray2.shape), r"\(", r"\,"))
            sourceCounter = -1
            
            #print(sourceArray2)
            print(sourceArray2.shape)
            
            for each in sourceArray:
                str2list2source = find_between(str(each), "http", "onion")
                str2list2source = f"http{str2list2source}onion"
                if str2list2source != "httponion":
                    sourceCounter += 1
                    #print(f"##############\nSOURCE : {str2list2source}\n##############\n")
                    str2list = str(str(each)).split("http")
                    for key in str2list:
                        key = "http" + str(key)
                        link = find_between(str(key), r"http", r".onion")
                        if link != "http" and link != "http.onion" and r"//" in link and r"\\" not in link and r"<" not in link \
                                and ">" not in link and r"[" not in link and r"]" not in link and "\"" not in link and "|" not in link:
                            #print("http" + str(link) + ".onion")
                            linksArray.append("http" + str(link) + ".onion")
        if scrape == 1 or newScrape == 1:
                loops = 0
                link_counter2 = 0
                sourceCounter = -1
                counter = 0
                #message2edit = await ctx.send("Beginning iteration.")
                #print("here")
                LinksArrayTemp = []
                dataNone = 0
                while counter < iterationCount or int(sourceCounter+1) < sourceSize:
                    print(counter)
                    #if source != "":
                    #    #if counter > 0 and source == "":
                    #    #    sourceArray = 
                    #    sourceCounter += 1
                    #    #or each in sourceArray:
                    #    # ['[\'http://jhi4v5rjly75ggha26cu2eeyfhwvgbde4w6d75vepwxt2zht5sqfhuqd.onion/\',
                    #    str2list2source = find_between(str(sourceArray[sourceCounter]), "\'[\\\'http", "onion/\\\',")
                    #    str2list2source = f"http{str2list2source}onion"
                    #    if str2list2source != "httponion":
                    #        print(f"##############\nSOURCE : {str2list2source}\n##############\n")
                    #        #await asyncio.sleep(1)
                    #        str2list = str(sourceArray[sourceCounter]).split("http")
                    #        for key in str2list:
                    #            key = "http" + str(key)
                    #            link = find_between(str(key), r"http", r".onion")
                    #            if link != "http" and link != "http.onion" and r"//" in link and r"\\" not in link and r"<" not in link \
                    #                    and ">" not in link and r"[" not in link and r"]" not in link and "\"" not in link and "|" not in link:
                    #                print("http" + str(link) + ".onion")
                    #                linksArray.append("http" + str(link) + ".onion")
                    
                    counter += 1
                    counter2 = 0 # for checkpoints
                    LinksArrayTemp = []
                    for URL in linksArray:
                        dataNone = 0
                        counter2 = counter2 + 1
                        print(counter2)
                        #data = await getData(ctx, URL)
                        data = await getData(URL)
                        print(data)
                        link_counter = 0
                        if data != None:
                            loops = loops + 1
                            link_counter2 = link_counter2 + 1
                            linksArrayReturn, message2edit, numLinks = await scrapeWithSoup(data, URL)
                            for each in linksArrayReturn:
                                print(each)
                                LinksArrayTemp.append(each)
                            print("Found " + str(numLinks) + " onion URLs in " + str(URL))
                            linksArrayReturn = []
                            print("Page: " + str(URL) + " yielded " + str(link_counter2) + " New links")
                            #ctx2 = await getCTX2(ctx)
                            #await ctx2.send(f"```Found " + str(numLinks) + " onion URLs in " + str(URL) + "```")
                            await asyncio.sleep(0.1)
                            link_counter2=0
                            for each in LinksArrayTemp:
                                link_counter += 1
                                scrapeArray.append([str(each), str(data)])
                            counter2 = 0
                            numpy.save(filePath + f".{loops}", scrapeArray)
                            scrapeArray = []
                            print(f"Saved scrapeArray ==> {filePath}.{loops}.npy")
                    linksArray = LinksArrayTemp
                print("\n\nDatabase " + str(filePath) + " finished. Found " + str(link_counter) + " new links, and corresponding data\n\n")

        return

    async def combineScrapes(source, file):
        ArraySource = numpy.load(HomeDir + r"\Saves\\" + f"{source}.npy")
        ArrayFile = numpy.load(HomeDir + r"\Saves\\" + f"{file}.npy")
        combinedArray = numpy.append(ArraySource, ArrayFile)
        if os.path.exists(HomeDir + r"\Saves\\" + f"{file}.npy"):
            os.rename(HomeDir + r"\Saves\\" + f"{file}.npy", HomeDir + r"\Saves\\" + f"{file}_{t.time()}.npy")
        numpy.save(HomeDir + r"\Saves\\" + f"{file}_predupecheck.npy")
        return combinedArray
            
    async def dupeCheck(sourceArray, file):
        counter = -1
        for each in sourceArray:
            counter = counter + 1
        strString2 = ""
        #await ctx.send(str(counter + 1) + " entries in local link database\n")
        #message2edit = await ctx.send("Beginning duplicate entry check.")
        counter4 = counter + 1
        counter5 = 0
        counter7 = 0
        counter6 = 0
        for each in sourceArray:
            print(str(counter5) + " entries in local link database checked.\n" +
                  str(int(counter4 - counter)) + " - Duplicate entries removed\n\n")
            counter5 = counter5 + 1
            counter7 = counter7 + 1
            if counter7 >= 10:
                counter7 = 0
                counter6 = counter6 + 1
                numpy.save(HomeDir + "\Saves\HUGE_FINAL.npy", sourceArray, allow_pickle=True)
                #if type(ctx) is not discord.TextChannel:
                #    message = ctx.message.channel.last_message
                #else:
                #    message = ctx.last_message
                #if message != message2edit:
                    #ctx = await getCTX(ctx)
                    #message2edit = await ctx.send("-")
            counter2 = counter
            counter3 = 0
            while counter2 >= 1:
                counter2 = counter2 - 1
                if each == sourceArray[counter2]:
                    if counter3 == 1:
                        print(str(sourceArray[counter2]) + " <-- Matches --> " + str(
                            each) + "\nRemoved entry at " + str(counter2))
                        strString2 = strString2 + str(
                            str(sourceArray[counter2])[:-10]) + " <-- Matches --> " + str(str(each)[:-10]) + \
                                     "\nRemoved entry at " + str(counter2) + "\n"
                        if len(strString2) >= 1500:
                            strString = ""
                            strString = strString + "Checkpoint: " + str(counter6) + "\n" + str(
                                counter5) + "/" + str(
                                int(counter4)) + " entries in local link database checked.\n" + \
                                        str(int(counter4 - counter)) + " - Duplicate entries removed\n\n"
                            #try:
                            #    if len(strString2 + strString) >= 2000:
                            #        msgStr = str(str(strString) + str(strString2))[:1969]
                            #        await message2edit.edit(content="```json\n" + msgStr + "```")
                            #    else:
                            #        await message2edit.edit(
                            #            content="```json\n" + strString + strString2 + "```")
                            #except HTTPException:
                            #    pass
                            strString2 = ""
                        sourceArray = numpy.delete(sourceArray, counter2)
                        counter = counter - 1
                    else:
                        counter3 = 1
        numpy.save(HomeDir + "\Saves\\" + f"{file}.npy", sourceArray, allow_pickle=True)
        counter4 = counter4 - counter
        print("\nRemoved: " + str(counter4) + " duplicate entries")
        #ctx = await getCTX(ctx)
        #await ctx.send("\nRemoved: " + str(counter4) + " duplicate entries")
        return

    async def scrapeWithSoup(data, URL):
        counter = 0
        counter2= 0
        dataSearch = "Disabled"
        #print("Data Search was here")
        #dataSearch = await keywordCheck(data, ctx)
        #ms2eString = str(ms2eString) + "\n\n" + str(URL)
        #ms2eString = str(ms2eString) + "\n" + "Data search: " + dataSearch + "\n"
        #ms2eString = ms2eString + "FOUND LINKS:\n"
        soup = BeautifulSoup(data, features="lxml")
        linksArray = []
        for link in soup.find_all('a'):
            #print(str(link))
            if ".onion" in str(link.get('href')) and str(link.get('href')) != str(URL):
                linksArray.append(str(link.get('href')))
                print(str(link.get('href')))
                counter += 1
                #print(str(link.get('href')))
                #ms2eString = str(ms2eString) + str(link.get('href')) + "\n"
                #if len(ms2eString) > 1000:
                #    try:
                #        await message2edit.edit(content="```" + ms2eString[:1750] + "```")
                #    except:
                #        ctx = await getCTX(ctx)
                #        message2edit = await ctx.send("```" + ms2eString[:1750] + "```")
                    #print(ms2eString)
                #    ms2eString = ""
                #    ms2eString = str(ms2eString) + "\n\n" + str(URL)
                #    ms2eString = str(ms2eString) + "\n" + "Data search: " + dataSearch + "\n"
                #    ms2eString = ms2eString + "FOUND LINKS:\n"

        return linksArray, None, counter
        #return linksArray, message2edit, ms2eString

    async def keywordCheck(data):
        dataSearch = "False"
        if "bridgeway" in str(data).lower() or "ponca" in str(data).lower():
            poggywoggyArray.append([data, URL])
            numpy.save(HomeDir + r"\Saves" + r"\Found_Keys_1.npy", poggywoggyArray)
            #await ctx.send("```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!``` \n ```FOUND: \n\n" + str(
            #    each[0]) + "\n\n```\n```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            dataSearch = "True"
        return dataSearch

        
    async def getData(URL):
        global proxy, proxyRetry
        socket.socket = socks.socksocket
        #print()
        #proxy = proxies[random.randint(1, len(proxies) - 1)]
        try:
            data = requests.get(URL, proxies=proxy, timeout=15).text
            print("1 - Got Data on: " + str(proxy) + f" \n for {URL}")
            #ctx = await getCTX2(ctx=ctx)
            #await ctx.send("```1 - Got Data on: " + str(proxy) + f" \n for {URL}```")
            return data
        except:
            proxyRetry += 1
            if proxyRetry < 3:
                print(proxyRetry)
                await getData(URL)
            else:
                proxyRetry = 0
                pass
        return None
        
    HomeDir = 'F:\!ALL SCRIPTS\_TorScraper'
    VarDir = HomeDir + r'\VariableVariables'
    LogDir = HomeDir + r'\Logs'
    StaticVarDir = HomeDir + r'\StaticVars'
    SoundDir = HomeDir + r'\Sound'
    ChromeDir = HomeDir + r'\Chrome'
    ScriptDir = HomeDir + r'\SkrippitySkripz'
    ImgDir = HomeDir + r'\ImageSearch'
    SerbzDir = HomeDir + r'\SerbzDir'

    StopIterationVar = 0
    loop.create_task(torscrape())
    loop.run_forever()
except ModuleNotFoundError:
    import os
    try:
        import re
    except:
        os.system("python39 -m pip install re")
        os.execv(sys.executable, ['python'] + sys.argv)
        SystemExit()
        sys.exit()
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
    strStr = ModuleNotFoundError
    #print(traceback.format_exc())
    stringy = find_between( traceback.format_exc(), "\'", "\'" )
    print(traceback.format_exc())
    #print(str(stringy))
    if stringy == "dotenv":
        try:
            os.system("F:\!Tools\Python39\python.exe -m pip install --upgrade pip")
            os.system("F:\!Tools\Python39\python.exe -m pip install pipwin --compile --no-cache-dir")
            #os.system("pipwin refresh")
            os.system("pipwin install wheel")
            #os.system("pip install dotenv --disable-pip-version-check --force-reinstall --compile --no-cache-dir")
            try:
                os.system("F:\!Tools\Python39\python.exe -m pip install python-" + stringy + " --compile --no-cache-dir")
                os.execv(sys.executable, ['python'] + sys.argv)
                SystemExit()
                sys.exit()
            except:
                pass
        except:
            pass
    if stringy == "pafy":
        try:
            os.system("F:\!Tools\Python39\python.exe -m pip install youtube_dl")
        except:
            pass
        try:
            os.system("F:\!Tools\Python39\python.exe -m pip install pafy")
        except:
            pass
        os.execv(sys.executable, ['python'] + sys.argv)
        SystemExit()
        sys.exit()
    if stringy == "win32api":
        try:
            os.system("F:\!Tools\Python39\python.exe -m pip install pywin32")
        except:
            pass
        os.execv(sys.executable, ['python'] + sys.argv)
        SystemExit()
        sys.exit()
    if stringy == "fcntl":
        print("fuck")
        SystemExit()
        sys.exit()

    try:
        os.system("F:\!Tools\Python39\python.exe -m pip install " + stringy + " --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("F:\!Tools\Python39\python.exe -m pip install python-" + stringy + " --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("F:\!Tools\Python39\python.exe -m pip install " + stringy + "-python --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("F:\!Tools\Python39\python.exe -m pip install py" + stringy + " --compile --no-cache-dir")
    except:
        pass

    os.execv(sys.executable, ['python'] + sys.argv)
    SystemExit()
    sys.exit()
    pass

