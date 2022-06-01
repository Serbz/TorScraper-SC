from __future__ import unicode_literals
import asyncio
import os
import pickle
import sys
from string import ascii_lowercase
from typing import List
import traceback
from discord.errors import Forbidden, HTTPException, NotFound
import discord
import numpy
from discord.ext import commands
from discord.ext.commands import CommandNotFound, Bot
from dotenv import load_dotenv
from collections import namedtuple
import signal
import logging
import random
from io import StringIO
import gzip, getopt
from pafy import new
from pyscreenshot import FailedBackendError
from lxml import etree
from bs4 import BeautifulSoup, SoupStrainer
from win32api import GetSystemMetrics
import socks
import socket
import requests
import fnmatch
import json
import re
import codecs
import urllib
import time as t
import urllib.request
from urllib3.exceptions import ProtocolError
if os.path.exists(r"C:\MainPC.txt"):
    sys.path.insert(1, r'z:\\')
else:
    sys.path.insert(1, r'C:\Users\Administrator\PycharmProjects\pythonProject')
import Logger

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


loop = asyncio.get_event_loop()
taskloopsINIT = []

# outputs proxy IP)
dataSets = []


stopScrape = False


async def wrapped_connect(f, bots):
    bot = f[0]

    @bot.event
    async def on_socket_raw_send(payload):
        # print("SEND: " + str(payload))
        return

    @bot.event
    async def on_socket_raw_receive(msg):
        # print("RECV: " + str(msg))
        return

    # @bot.event
    # async def on_message(message):
    #    return

    @bot.event
    async def on_typing(channel, user, when):
        # print("ONTYPE: " + str(channel) + " - " + str(user) + " - " + str(when))
        return

    @bot.event
    async def on_guild_channel_delete(channel):
        # print("GUILDCHANDEL: " + str(channel))
        return

    @bot.event
    async def on_guild_channel_create(channel):
        # print("GUILDCHANCREATE: " + str(channel))
        return

    @bot.event
    async def on_guild_channel_update(before, after):
        # print("GUILDCHANUPDATE: " + str(before) + " - " + str(after))
        return

    @bot.event
    async def on_member_join(member):
        # print("MEMBRJOIN" + str(member))
        return

    @bot.event
    async def on_member_remove(member):
        # print("MEMBRREMOVE" + str(member))
        return

    @bot.event
    async def on_ready():
        taskloops = []
        for bot in bots:
            taskloops.append(yourArmyAwaits(bot))
        #print(str(taskloops))
        await asyncio.gather(*taskloops)
        return

    @bot.event
    async def on_command_error(ctx, error):
        global sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
        if isinstance(error, CommandNotFound):
            await ctx.send("command " + str(str(ctx.message.content).split(" ")[0]) + " not found.")
            return
        if isinstance(error, KeyError):
            return
        if isinstance(error, UnboundLocalError):
            return
        var = traceback.format_exc()
        await Messages(str(var), None, sysChannel, None)
        raise error

    #@bot.event
    #async def on_ready():
    #    taskloops = []
    #    for bot in bots:
    #        taskloops.append(yourArmyAwaits(bot))
    #        #taskloops.append(taskityTaskers(bot))
    #        #print(str(taskloops))
    #    print(str(taskloops))
    #    await asyncio.gather(*taskloops)
    #    return

    async def yourArmyAwaits(bot):
        global g2_counter, sysChannelID, sysChannel
        for bot in bots:
            for guild in bot.guilds:
                for textChannel in guild.text_channels:
                    if textChannel.id == sysChannelID:
                        sysChannel = await bot.fetch_channel(sysChannelID)
                        break
        msg_str = "```"
        msg_str = msg_str + "\n#-#-#-#-#-# Initialization #-#-#-#-#-# \n #-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#  \n"
        #############################################
        Logger.LogPrint(bot.user.id)
        Logger.LogPrint(discord.__version__)
        strgB = ""
        for guild in bot.guilds:
            strgB = strgB + "\n" + str(guild)
        msg_str = msg_str + '\n' + r"logged in as: " + str(
            bot.user.name) + "\n" + str(
            bot.user.id) + '\n ------' + '\n Servers connected to:' + '\n #-#-#-#-#-#-#-#-#-#-#-#-#-' + strgB + "```"
        #############################################
        # await Messages(str(msg_str), None, sysChannel, None)
        return

    @bot.command(name="pastescrape")
    async def pastescrape(ctx):
        global stopScrape
        keywords_file = open(HomeDir + r"\Saves\Keywords.txt")
        keywords = keywords_file.read()
        keywords = str(keywords).split(" ")
        crawl_total = None
        found_keywords = []
        paste_list = set([])
        root_url = 'http://pastebin.com'
        raw_url = 'http://pastebin.com/raw/'
        length = 0
        while stopScrape == 0:
            await asyncio.sleep(0.15)
            root_html = BeautifulSoup(await fetch_page(root_url), 'html.parser')
            nextPasteSet = await new_pastes(root_html)
            for paste in nextPasteSet:
                for paste in find_new_pastes(root_html):
                    length = len(paste_list)
                    paste_list.add(paste)
                    if len(paste_list) > length:
                        raw_paste = raw_url + paste
                        found_keywords.append([raw_paste, found_keywords, keywords])
                        print(str(found_keywords))
        found_keywords = numpy.asanyarray(found_keywords)
        numpy.save(HomeDir + r"\Saves\found_keywords.npy", found_keywords)
        return

    async def fetch_page(page):
        response = urllib.request.urlopen(page)
        if response.info().get('Content-Encoding') == 'gzip':
            response_buffer = StringIO(response.read())
            unzipped_content = gzip.GzipFile(fileobj=response_buffer)
            return unzipped_content.read()
        else:
            return response.read()

    async def new_pastes(root_html):
        new_pastes = []
        div = root_html.find('div', {'id': 'menu_2'})
        ul = div.find('ul', {'class': 'right_menu'})
        for li in ul.findChildren():
            if li.find('a'):
                new_pastes.append(str(li.find('a').get('href')).replace("/", ""))
        return new_pastes

    @bot.command(name="deletemsgs")
    async def deletemsgs(ctx):
        if ctx.message.author.id != 246892047284436992 and ctx.message.author.id != 855613733854642237:
            return
        else:
            number = str(ctx.message.content).split(" ")[1]
            if str(ctx.message.content).split(" ")[1] is not None and str(ctx.message.content).split(" ")[1] != [] and \
                    str(ctx.message.content).split(" ")[1] != "":
                iterationLimit = int(str(ctx.message.content).split(" ")[1])
                counter = 0
                strString = ""
                mgs = []  # Empty list to put all the messages in the log
                number = int(number)  # Converting the amount of messages to delete to an integer


                async for x in (await getCTX(ctx)).history(limit=number):
                    mgs.append(x)
                    #strString = ""
                for every in mgs:
                    ctx = await getCTX(ctx)
                    await every.delete()
                #await ctx.send(strString)
        return

    async def keywordCheck(data, ctx):
        dataSearch = "False"
        if "bridgeway" in str(data).lower() or "ponca" in str(data).lower():
            poggywoggyArray.append([data, URL])
            numpy.save(HomeDir + r"\Saves" + r"\Found_Keys_1.npy", poggywoggyArray)
            await ctx.send("```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!``` \n ```FOUND: \n\n" + str(
                each[0]) + "\n\n```\n```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            dataSearch = "True"
        return dataSearch

    async def backupScrape(file):
        # Backup previous npy and load it#
        file = HomeDir + r"\Saves\\" + str(file) + ".npy"
        if os.path.exists(file + ".bak"):
            os.rename(file + ".bak", file + f".bak.{t.time()}")
        if os.path.exists(file):
            if os.path.exists(file + f".bak.{t.time()}"):
                os.remove(file + f".bak.{t.time()}")
            os.rename(file, file + f"{t.time()}")
        return


    async def getData(URL):
        socket.socket = socks.socksocket
        proxy = proxies[random.randint(1, len(proxies) - 1)]
        try:

            data = requests.get(URL, proxies=proxy, timeout=2).text
            return data
        except:
            print("problem getting data on: " + str(proxy))
            counter = 0
            for key in proxies:
                print("Trying proxy: " + str(key))
                counter = counter + 1
                try:
                    data = requests.get(each[0], proxies=key, timeout=15).text
                    print("Got Data on: " + str(key))
                    return data
                except:
                    pass
        return None

    async def scrapeWithSoup(data, message2edit, URL, ms2eString, ctx):
        counter = 0
        counter2= 0
        dataSearch = await keywordCheck(data, ctx)
        ms2eString = str(ms2eString) + "\n\n" + str(URL)
        ms2eString = str(ms2eString) + "\n" + "Data search: " + dataSearch + "\n"
        ms2eString = ms2eString + "FOUND LINKS:\n"
        soup = BeautifulSoup(data, features="lxml")
        for link in soup.find_all('a'):
            print(str(link))
            if ".onion" in str(link.get('href')) and str(link.get('href')) != str(URL):
                linksArray.append([str(link.get('href')), data])
                print(str(link.get('href')))
                ms2eString = str(ms2eString) + str(link.get('href')) + "\n"
                if len(ms2eString) > 1000:
                    try:
                        await message2edit.edit(content="```" + ms2eString[:1750] + "```")
                    except:
                        ctx = await getCTX(ctx)
                        message2edit = await ctx.send("```" + ms2eString[:1750] + "```")
                    ms2eString = ""
                    ms2eString = str(ms2eString) + "\n\n" + str(URL)
                    ms2eString = str(ms2eString) + "\n" + "Data search: " + dataSearch + "\n"
                    ms2eString = ms2eString + "FOUND LINKS:\n"
        return linksArray, message2edit, ms2eString

    async def dupeCheck(sourceArray, file, ctx):
        counter = -1
        for each in sourceArray:
            counter = counter + 1
        strString2 = ""
        await ctx.send(str(counter + 1) + " entries in local link database\n")
        message2edit = await ctx.send("Beginning duplicate entry check.")
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
                if type(ctx) is not discord.TextChannel:
                    message = ctx.message.channel.last_message
                else:
                    message = ctx.last_message
                if message != message2edit:
                    ctx = await getCTX(ctx)
                    message2edit = await ctx.send("-")
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
                            try:
                                if len(strString2 + strString) >= 2000:
                                    msgStr = str(str(strString) + str(strString2))[:1969]
                                    await message2edit.edit(content="```json\n" + msgStr + "```")
                                else:
                                    await message2edit.edit(
                                        content="```json\n" + strString + strString2 + "```")
                            except HTTPException:
                                pass
                            strString2 = ""
                        sourceArray = numpy.delete(sourceArray, counter2)
                        counter = counter - 1
                    else:
                        counter3 = 1
        numpy.save(HomeDir + "\Saves\\" + f"{file}.npy", sourceArray, allow_pickle=True)
        counter4 = counter4 - counter
        print("\nRemoved: " + str(counter4) + " duplicate entries")
        ctx = await getCTX(ctx)
        await ctx.send("\nRemoved: " + str(counter4) + " duplicate entries")
        return

    async def combineScrapes(source, file, ctx):
        ArraySource = numpy.load(HomeDir + r"\Saves\\" + f"{source}.npy")
        ArrayFile = numpy.load(HomeDir + r"\Saves\\" + f"{file}.npy")
        combinedArray = numpy.append(ArraySource, ArrayFile)
        if os.path.exists(HomeDir + r"\Saves\\" + f"{file}.npy"):
            os.rename(HomeDir + r"\Saves\\" + f"{file}.npy", HomeDir + r"\Saves\\" + f"{file}_{t.time()}.npy")
        numpy.save(HomeDir + r"\Saves\\" + f"{file}_predupecheck.npy")
        return combinedArray

    @bot.command(name="torscrape")
    async def torscrape(ctx):
        if ctx.message.author.id != 246892047284436992 and ctx.author.id != 855613733854642237:
            return
        counter = -1
        duplicateCheck = 0
        source = ""
        scrapeArray = []
        URL = ""
        file = ""
        filePath = ""
        sourcePath = ""
        scrape = ""
        merge = ""
        linksArray = []
        sourceArray = []
        iterationCount = 0
        strFileSourceURL = ""
        strModes = ""
        strIteration = ""
        ms2eString = ""
        for each in str(ctx.message.content).split(" "):
            counter = counter + 1
            if counter != 0:
                if each == "-file":
                    file = str(ctx.message.content).split(" ")[counter + 1]
                    filePath = HomeDir + r"\Saves\\" + str(file) + ".npy"
                    print(str(filePath) + "\n")
                    strFileSourceURL = strFileSourceURL + "File set as: " + str(filePath) + "\n"
                if each == "-source":
                    source = str(ctx.message.content).split(" ")[counter + 1]
                    sourcePath = HomeDir + r"\Saves\\" + str(source) + ".npy"
                    print(str(sourcePath) + "\n")
                    strFileSourceURL = strFileSourceURL + "Source set as: " + str(sourcePath) + "\n"
                if each == "-url":
                    URL = ctx(ctx.message.content).split(" ")[counter + 1]
                    linksArray = [URL]
                    print(str(linksArray) + "\n")
                    strFileSourceURL = strFileSourceURL + "URL for source set as: " + str(URL) + "\n"
                if each == "/scrape":
                    scrape = 1
                    print("scrape" + str(scrape) + "\n")
                    strModes = strModes + "Scrape set to: " + str(bool(scrape)) + "\n"
                if each == "/dupecheck":
                    duplicateCheck = 1
                    print("duplicateCheck" + str(duplicateCheck) + "\n")
                    strModes = strModes + "duplicateCheck set to: " + str(bool(duplicateCheck)) + "\n"
                if each == "/merge":
                    duplicateCheck = 1
                    merge = 1
                    print("merge" + str(merge))
                    print("duplicateCheck" + str(duplicateCheck) + "\n")
                    strModes = strModes + "merge set to: " + str(bool(merge)) + "\n"
                if each == "-count" and scrape == 1:
                    try:
                        iterationCount = int(str(ctx.message.content).split(" ")[counter + 1])
                        if iterationCount < 1:
                            await ctx.send("iteration count can not be less than 1")
                            return
                        print("iterationCount" + str(iterationCount) + "\n")
                        strIteration = strIteration + "Iteration count set to: " + str(iterationCount) + "\n"
                    except TypeError:
                        await ctx.send("-count must specify a number and can only be used with /scrape")
                        return

        if iterationCount >= 1 and scrape == 0:
            await ctx.send("-count must specify a number and can only be used with /scrape")
            return

        if iterationCount == 0:
            iterationCount = 1
            strIteration = strIteration + "Iteration count not specified, Interation set to: " + str(iterationCount) + "\n"

        msgString = strFileSourceURL + strModes + strIteration
        await ctx.send("```json\n" + str(msgString) + "```")

        ##Sanity checks##
        if (duplicateCheck == 1 or merge == 1) and file == "" and source == "":
            await ctx.send("must specify -file -source for dupe checking")
            return
        if URL == "" and source == "":
            await ctx.send("must specify either URL OR Source AND file")
            return
        if file == source:
            await ctx.send("file and source cannot be the same")
            return
        if file == "":
            await ctx.send("must specify atleast a save file")
            return
        #get URL#
        if URL != "" and source == "":
            await ctx.send("scraping from scratch, no source file specified")
            newScrape = 1
        else:
            newScrape = 0



        if duplicateCheck == 1 or merge == 1:
            await dupeCheck(source, file, ctx)
            if merge == 1:
                scrapeArray = await combineScrapes(file, source, ctx)

        if source != "" or newScrape == 0 and duplicateCheck != 1:
            sourceArray = numpy.load(sourcePath)
        else:
            await ctx.send("idk how you got here but no.")
            return

        if scrape == 1 or newScrape == 1:
            if source != "":
                source = ""
                for each in sourceArray:
                    linksArray.append(each[0])


            counter = 0
            message2edit = await ctx.send("Beginning iteration.")
            while counter < iterationCount:
                counter = counter + 1 #for iteration
                counter2 = 0 # for checkpoints
                LinksArrayTemp = []
                linksArrayReturn = []
                for URL in linksArray:
                    await asyncio.sleep(0.1)
                    counter2 = counter2 + 1
                    data = await getData(URL)
                    if data != None:
                        keywordList = str(open(HomeDir + r"\Saves\Keywords.txt").read()).split("\n")
                        for each in keywordList:
                            if str(each).lower() in str(data).lower():
                                if os.path.exists(HomeDir + r"\Saves\KeyResults.npy"):
                                    keywordArray = numpy.load(HomeDir + r"\Saves\KeyResults.npy")
                                    keywordArray = keywordArray.tolist()
                                else:
                                    keywordArray = []
                                keywordArray.append([URL, data])
                                numpy.save(HomeDir + r"\Saves\KeyResults.npy")
                                keywordArray = []
                        linksArrayReturn, message2edit, ms2eString = await scrapeWithSoup(data, message2edit, URL, ms2eString, ctx)
                        LinksArrayTemp.extend(linksArrayReturn)
                        linksArrayReturn = []
                        for URL in LinksArrayTemp:
                            scrapeArray.append([URL, data])
                        if counter2 > 5:
                            counter2 = 0
                            numpy.save(filePath, scrapeArray)

                linksArray = linksArrayTemp
            numpy.save(filePath, scrapeArray)


        return



    @bot.command("stopscrape")
    async def stopscrape(ctx):
        global StopIterationVar
        if ctx.message.author.id == 855613733854642237:
            StopIterationVar = 1
        else:
            return


    @bot.command(name="string")
    async def splitsBotsStrings(ctx):
        global bots
        splStringsBots = str(ctx.message.content).split(" ")
        counter = -1
        for bot in bots:
            counter = counter + 1
        taskloops = []
        counter2 = -1
        for key in splStringsBots:
            counter2 = counter2 + 1
            if counter2 > counter:
                counter2 = 0
            # bots[counter2]
            taskloops.append(stringSplBots(ctx, bots[counter2], key))
        await asyncio.gather(*taskloops)
        return

    async def stringSplBots(ctx, bot, stringy):
        try:
            await (await bot.fetch_channel(int(ctx.message.channel.id))).send(str(bot.user.id) + "\n" + str(stringy))
        except:
            pass
        return

    @bot.event
    async def on_socket_raw_send(payload):
        global globalIterator, globalIteratorLimit
        print("```" + str(payload) + "```")
        return
    @bot.command(name='oauth')
    async def oauths(ctx):
        for bot in bots:
            ctx = await getCTX(ctx)
            await ctx.send(f"https://discord.com/api/oauth2/authorize?client_id={str(bot.user.id)}&permissions=8&scope=bot")
        return

    @bot.event
    async def on_message(message):
        global pop, stopScrape
        global globalIteratorLimit, botIterator
        sysChannelIDS = [871650162655780864, 871650184881401876, 871650226828619808]
        if int(message.author.id) == int(855613733854642237) or \
                int(message.author.id) == int(246892047284436992):
            if str(message.content).lower()[1:] == "stopscrape":
                stopScrape = not stopScrape

        if not bot == bots[0]:
            await asyncio.sleep(0.1)
        if bot == bots[0] and message.channel.id != 873869646573502514 and message.channel.id != 866356303626240050:
            botIterator = botIterator + 1
            # botIterator2 = botIterator + 1
            if botIterator > globalIteratorLimit:
                botIterator = 0
            # if botIterator2 > globalIteratorLimit:
            # botIterator2 = 0
        else:
            await asyncio.sleep(0.1)
        if bot == bots[botIterator]:  # or bot == bots[botIterator2]:
            # combinedSysChannel2 = await bots[botIterator2].fetch_channel(873869646573502514)
            combinedSysChannel = await bots[botIterator].fetch_channel(866356303626240050)
            for id in sysChannelIDS:
                # print(str(id))
                # print(str(message.channel.id))
                if int(id) == int(message.channel.id):
                    txt = str(message.content).replace("@", "<AT>")
                    txt = txt.replace("```", "")
                    await combinedSysChannel.send(
                        "#" + str(bots[botIterator].user.discriminator) + "```" + str(message.channel.name) + " - " \
                        + r"#" + str(message.author.name) + str(message.author.discriminator) \
                        + r": " + str(message.content) + "```")
                    break

        if bot == bots[0]:
            print(str(message.content))
        if pop == False or str(message.content).lower()[1:] == "restart":
            await bot.process_commands(message)
        return

    @bot.command(name='restart')
    async def restart(ctx):
        if str(ctx.author.name).lower() == 'serbz' and (
                str(ctx.author.discriminator) == '0001' or str(ctx.author.discriminator) == '0002'):
            await Messages("#-#-#-#-#-# Restarting. #-#-#-#-#-#", ctx, None, None)
            os.execv(sys.executable, ['python'] + sys.argv)
            SystemExit()
            sys.exit()
        return

    @bot.command(name="claim")
    async def claim(ctx):
        ctxSpl = str(ctx.message.content).split(" ")
        counter = -1
        for each in ctxSpl:
            guildName = "NaN"
            skip = 0
            counter = counter + 1
            if counter != 0:
                claim, claimedBy, claimedByID = await checkClaim(ctx, int(each))
                for guild in bots[0].guilds:
                    if int(guild.id) == int(each):
                        guildName = str(guild)
                if guildName == "NaN":
                    await ctx.send("No Access to any guild with ID: " + str(each))
                    skip = 1
                if claim:
                    await ctx.send("Guild " + str(guildName) + " **is already** claimed by: " + str(
                        claimedBy) + " with user ID: " + str(claimedByID) + "**")
                    skip = 1
                if skip != 1:
                    with open(HomeDir + r"\Saves\Claims.txt", "a", encoding='utf8', errors="ignore") as text_file:
                        text_file.write("\n" + str(ctx.message.author.id) + " " + str(each) + " " +
                                        str(ctx.message.author.name) + " " + str(guildName))
                        await ctx.send("Guild: " + str(guildName) + " **is now** claimed by: " + str(
                            ctx.message.author.name) + " with user ID: " \
                                       + str(ctx.message.author.id))
                        await asyncio.sleep(1.75)
                    text_file.close()
        return

    @bot.command(name="unclaim")
    async def unclaim(ctx):
        ctxSpl = str(ctx.message.content).split(" ")
        for each in ctxSpl:
            skip = 1
            guildName = "NaN"
            for guild in bots[0].guilds:
                if str(guild.id) == str(each):
                    guildName = guild
            if str(each).lower() != "unclaim" and guildName != "NaN":
                claimed, claimed_user, claimed_userID = await checkClaim(ctx, str(each))
                if str(claimed_userID) == str(ctx.message.author.id) and claimed:
                    line = await getClaimLine(each)
                    await claimsUpdater(line)
                    await asyncio.sleep(2)
                    await ctx.send("Guild: " + str(guildName) + " with ID: " + str(each) + " **unclaimed**.")
                    break
                elif not claimed:
                    await asyncio.sleep(2)
                    await ctx.send(
                        "Guild: " + str(guildName) + " with ID: " + str(each) + " **was already unclaimed**.")
                elif str(claimed_userID) != str(ctx.message.author.id):
                    await asyncio.sleep(2)
                    await ctx.send(
                        "Guild: " + str(guildName) + " with ID: " + str(each) + " **is already claimed by: " +
                        str(claimed_user) + " with ID: " + str(claimed_userID) + "**")
        return


    @bot.command(name='pop')
    async def populate_lists_L(ctx):
        global pop, bots, sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
        await Messages("\n########################\nBEGIN TargetsAndSource\n########################", sysChannel,
                       None, None)
        TargetGuildList, SourceGuild = await TargetsAndSource(ctx, "pop")
        #ctxSplSk = str(ctx.message.content.split("//"))
        #ctxSplSkV = 0
        #if len(ctxSplSk) > 2:
        #    ctxSplSkV = 1
        #    await ctx.send("found // Skipping builds")
        if TargetGuildList == [] or type(TargetGuildList) == type(None) or SourceGuild == type(None):
            return
        print(str(TargetGuildList))
        botList = []
        bot_counter = -1
        for bot in bots:
            exists = 0
            for guild in bot.guilds:
                for tguild in TargetGuildList:
                    if int(guild.id) == int(tguild) and exists == 0:
                        for guild in bot.guilds:
                            if int(guild.id) == int(SourceGuild.id):
                                for botClient in botList:
                                    if bot == botClient:
                                        exists = 1
                                        break
                                if exists == 0:
                                    # sourceBots.append(bot)
                                    bot_counter = bot_counter + 1
                                    print("botList: " + str(bot.user.id))
                                    botList.append(bot)
                                    break
                        break
        if len(botList) <= 0:
            return
        pop = True
        taskloops = []
        waitCount = 1
        task_counter = -1
        await Messages("\n########################\nBEGIN buildChannels\n########################", sysChannel,
                       None, None)
        for eachGuild in TargetGuildList:
            for guild in botList[0].guilds:
                if eachGuild == guild.id:
                    task_counter = task_counter + 1
                    if task_counter > bot_counter:
                        waitCount = waitCount + 1
                        task_counter = 0
                    TargetGuild = guild
                    taskloops.append(buildChannels(ctx, TargetGuild, SourceGuild, waitCount, botList[task_counter]))
                    print(str(botList[task_counter].user) + "buildChannels")
        # print(str(taskloops))
        createRolesArray = []
        await asyncio.gather(*taskloops)
        await Messages("\n########################\nBEGIN getCreateRolesArray/applyRoles\n########################",
                       sysChannel,
                       None, None)
        await asyncio.sleep(20)
        # for eachGuild in TargetGuildList:
        for guild in botList[0].guilds:
            if int(SourceGuild.id) == int(guild.id):
                task_counter = task_counter + 1
                if task_counter > bot_counter:
                    waitCount = waitCount + 1
                    task_counter = 0
                TargetGuild = guild
                tarded = await getCreateRolesArray(ctx, SourceGuild, TargetGuild, waitCount, botList[task_counter])
                createRolesArray = tarded
                break
        pop = True
        taskloops = []
        waitCount = 1
        task_counter = -1
        for eachGuild in TargetGuildList:
            for guild in botList[0].guilds:
                if eachGuild == guild.id:
                    task_counter = task_counter + 1
                    if task_counter > bot_counter:
                        waitCount = waitCount + 1
                        task_counter = 0
                    TargetGuild = guild
                    print(str(createRolesArray))
                    taskloops.append(
                        removeAllRoles(ctx, TargetGuild, SourceGuild, waitCount, botList[task_counter]))
        await asyncio.gather(*taskloops)
        pop = True
        taskloops = []
        waitCount = 1
        task_counter = -1
        for eachGuild in TargetGuildList:
            for guild in botList[0].guilds:
                if eachGuild == guild.id:
                    task_counter = task_counter + 1
                    if task_counter > bot_counter:
                        waitCount = waitCount + 1
                        task_counter = 0
                    TargetGuild = guild
                    print(str(createRolesArray))
                    taskloops.append(
                        applyRoles(ctx, TargetGuild, SourceGuild, waitCount, createRolesArray,
                                   botList[task_counter]))
                    print(str(botList[task_counter].user) + "applyRoles")
        # print(str(taskloops))
        await asyncio.gather(*taskloops)
        pop = True
        taskloops = []
        waitCount = 1
        task_counter = -1
        ######################################### COLLECT MEMBER DATA AND THEIR ROLES!!!!! #########################################
        await Messages("\n########################\nBEGIN checkroles\n########################", sysChannel,
                       None, None)
        for eachGuild in TargetGuildList:
            for guild in bots[0].guilds:
                if eachGuild == guild.id:
                    task_counter = task_counter + 1
                    if task_counter > bot_counter:
                        waitCount = waitCount + 1
                        task_counter = 0
                    TargetGuild = guild
                    taskloops.append(checkroles(ctx, TargetGuild, SourceGuild, waitCount, botList[task_counter]))
                    print(str(botList[task_counter].user) + "checkroles")
        # print(str(taskloops))
        await asyncio.gather(*taskloops)
        pop = True
        taskloops = []
        waitCount = 1
        task_counter = -1
        ######################################### ROLES AND MEMBERS EXIST PROPERLY #########################################
        ######################################### CAN PERFORM CHANNEL OVERWRITES NOW #########################################
        await Messages("\n########################\nBEGIN channelPermSync\n########################", sysChannel,
                       None, None)
        for eachGuild in TargetGuildList:
            for guild in bots[0].guilds:
                if eachGuild == guild.id:
                    task_counter = task_counter + 1
                    if task_counter > bot_counter:
                        waitCount = waitCount + 1
                        task_counter = 0
                    TargetGuild = guild
                    taskloops.append(
                        channelPermSync(ctx, TargetGuild, SourceGuild, waitCount, botList[task_counter]))
                    print(str(botList[task_counter].user) + "channelPermSync")
        # print(str(taskloops))
        await asyncio.gather(*taskloops)
        await Messages("End.", ctx, sysChannel, None)
        pop = False
        return

    @bot.command(name="auth")
    async def oauth(ctx):
        await ctx.send(
            "```***THIS BOT USES ADMIN PERMISSIONS TO READ DATA FROM SOURCES AND MANAGE ROLES/CHANNELS/ETC ON TARGETS***\n"
            "\nPlease use it's commands with caution. It will NEVER modify a server that it is using as a source server\n"
            "the commands are all formatted #command as such:\n\n #command -t TARGETID TARGETID ASMANYTARGETIDS ASYOUWANT -s SOURCEID\n"
            "```\nhttps://discord.com/api/oauth2/authorize?client_id=870463527020797963&permissions=8&scope=bot")
        return

    @bot.command(name="help")
    async def helpcmd(ctx):
        await ctx.send("```  "
                       "\n\n-------- || #auth\n -- || Returns the OAuth2 link for adding the bot to a server"
                       "\n\n-------- || #Checkroles -t [Target Server(s))] -s [Source Server]\n-- || applies roles to target from source"
                       "\n\n-------- || #channelperms -t [Target Server(s)] -s [Source Server]\n-- || applies channel permissions from source"
                       "\n\n-------- || #rebuildroles -t [Target Server(s)] -s [Source Server]\n-- || REMOVES and completely rebuilds roles on target(s) from source"
                       "\n\n-------- || #pop -t [Target Server(s)] -s [Source Server]\n-- || FULL REBUILD OF TARGETS FROM SOURCE"
                       "\n\n-------- || #claim [Server(s)]\n-- || Claims Server(s) to be only managed by you"
                       "\n\n-------- || #unclaim [Server(s)]\n-- || Unclaims Server(s) you have claimed\n\n"
                       " ```")

    async def checkClaim(ctx, id):
        global pop, sysChannelID
        # sysChannel = await bot.fetch_channel(sysChannelID)
        # TargetGuild = await bot.fetch_guild(TargetGuild.id)
        # SourceGuild = await bot.fetch_guild(SourceGuild.id)
        text_file = open(HomeDir + r"\Saves\Claims.txt", "r", encoding='utf8', errors="ignore")
        claims = text_file.read()
        text_file.close()
        ##await ctx.send(str(claims))
        # print(str(claims))
        if claims.isspace() or claims == "":
            return False, str("NaN"), 0
        claimsSpl = str(claims).split("\n")
        for each in claimsSpl:
            counter = -1
            eachSpl = str(each).split(" ")
            for key in eachSpl:
                counter = counter + 1
                if not str(key).isspace() and str(key) != "":
                    if str(key[0])[:1] != r"#" and str(str(key[0])[:1]).isdigit():
                        if str(eachSpl[counter]) == str(id):
                            try:
                                if str(key) == str(ctx.message.author.id):
                                    return True, str(eachSpl[counter + 1]), str(eachSpl[counter - 1])
                                else:
                                    return True, str(eachSpl[counter + 1]), str(eachSpl[counter - 1])
                            except IndexError:
                                pass
        # not claimed
        return False, str("NaN"), 0

    async def getClaimLine(stringy, start=-1):
        global pop, sysChannelID
        # sysChannel = await bot.fetch_channel(sysChannelID)
        # TargetGuild = await bot.fetch_guild(TargetGuild.id)
        # SourceGuild = await bot.fetch_guild(SourceGuild.id)
        # ctx2 = ctx
        # ctx = ctx2.message.channel
        counter = start
        counter2 = start
        with open(HomeDir + r"\Saves\Claims.txt", "r", encoding='utf8', errors="ignore") as text_file:
            data = text_file.readlines()
        text_file.close()
        dataSpl = str(data).split("\n")
        for key in dataSpl:
            counter2 = counter2 + 1
        for key in dataSpl:
            counter = counter + 1
            keySpl = str(key).split(" ")
            for element in keySpl:
                if str(element) == str(stringy):
                    return counter
        return -1

    async def claimsUpdater(line, filez=HomeDir + r"\Saves\Claims.txt"):
        global pop, sysChannelID
        # sysChannel = await bot.fetch_channel(sysChannelID)
        # TargetGuild = await bot.fetch_guild(TargetGuild.id)
        # SourceGuild = await bot.fetch_guild(SourceGuild.id)
        with open(filez, "r", encoding='utf8', errors="ignore") as file:
            data = file.readlines()
        counter = 1
        with open(filez, 'w', encoding='utf8', errors="ignore") as text_file:
            # text_file = open(HomeDir + r"\variables.txt", "w")
            text_file.write("#!#DO_NOT_REMOVE_OR_ADD_LINES#@#\n")
            for key in data:
                counter = counter + 1
                if counter >= len(data):
                    break
                if counter != line:
                    text_file.write(str(data[counter]))
        return

    async def postRolesCheck(ctx, id, target_source):
        global pop, sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
        # TargetGuild = await bot.fetch_guild(TargetGuild.id)
        # SourceGuild = await bot.fetch_guild(SourceGuild.id)
        guildName = ""
        claim, claimed_user, claimed_userID = await checkClaim(ctx, id)
        if claim:
            for guild in bots[0].guilds:
                if str(claimed_userID) == str(ctx.message.author.id):
                    if str(guild.id) == str(id):
                        if target_source.lower() == "source":
                            SourceGuild = guild
                        guildName = guild
                        await Messages(target_source + " Set: " + str(guildName) + " ID: " + str(id), ctx,
                                       sysChannel, None)
                        return True
                else:
                    await ctx.send(
                        str(target_source) + ": " + str(guildName) + " **is claimed** by: " + str(
                            claimed_user) + " with ID: " + str(
                            claimed_userID))
                    return False
        else:
            for guild in bots[0].guilds:
                if id == guild.id:
                    await ctx.send("**" + str(target_source) + " guild is unclaimed.**")
                    return False
            await ctx.send("**No access to " + str(target_source) + " guild**")
            return False

    async def TargetsAndSource(ctx, commandName):
        global pop, sysChannelID
        # sysChannel = await bot.fetch_channel(sysChannelID)
        # TargetGuild = await bot.fetch_guild(TargetGuild.id)
        # SourceGuild = await bot.fetch_guild(SourceGuild.id)
        TargetGuildList = []
        ctxSpl = str(ctx.message.content).split(" ")
        NoSource = 1
        t_pass = False
        counter = 1
        counter2 = 1
        NoSource = 1
        SourceGuild = None
        for each in ctxSpl:
            if str(each).lower() == "-t":
                t_pass = True
            if t_pass:
                counter2 = counter2 + 1
        t_pass = False
        for each in ctxSpl:
            if NoSource == 0:
                break
            if str(each).lower() == "-t":
                t_pass = True
            if t_pass and str(each).lower() != "-t":
                counter = counter + 1
                if str(each).lower() == "-s":
                    checkRolesSourceID = int(ctxSpl[counter + 1])
                    sourceCheck = await postRolesCheck(ctx, checkRolesSourceID, "Source")
                    if sourceCheck == False:
                        return None, None
                    else:
                        for guild in bots[0].guilds:
                            if guild.id == checkRolesSourceID:
                                SourceGuild = guild
                                NoSource = 0
                                break
                        if NoSource == 1:
                            await ctx.send(
                                "Either access to that guild has been removed, or something else went wrong.")
                        break
                checkRolesTargetID = int(str(each))
                targetCheck = await postRolesCheck(ctx, checkRolesTargetID, "Target")
                if targetCheck == True:
                    TargetGuildList.append(int(each))
        if counter2 == counter:
            await ctx.send("Use " + str(commandName) + " -t [list of target ids space delimited] -s [source id]")
            return None, None
        if NoSource == 1:
            await ctx.send("Problem with Source Guild.")
            return None, None
        return TargetGuildList, SourceGuild

    async def buildChannels(ctx, TargetGuild, SourceGuild, waitCount, bot):
        global pop, sysChannelID
        sysChannel = await bot.fetch_channel(sysChannelID)
        TargetGuild = await bot.fetch_guild(TargetGuild.id)
        SourceGuild = await bot.fetch_guild(SourceGuild.id)
        ctx2 = ctx
        ctx = ctx2.message.channel
        pop = True
        await Messages("```Removing any and all existing channels on Target.\nTarget Guild: " + str(
            TargetGuild.name) + "\nSourceGuild: " + str(SourceGuild.name) + "```", ctx, sysChannel, None)
        ######################################### DELETE CHANNELS #########################################
        for guild in bot.guilds:
            if guild.id == TargetGuild.id:
                TargetGuildT = guild
                for temp in TargetGuildT.categories:
                    if not temp.name == '_constant_':
                        try:
                            await temp.delete()
                        except HTTPException:
                            pass
                        await asyncio.sleep(1.75 * waitCount)
                for temp in TargetGuildT.text_channels:
                    if not temp.name == '_constant_' and not temp.name == '_sys_':
                        try:
                            await temp.delete()
                        except HTTPException:
                            pass
                        await asyncio.sleep(1.75 * waitCount)
                for temp in TargetGuildT.voice_channels:
                    if not temp.name == '_constant_':
                        try:
                            await temp.delete()
                        except HTTPException:
                            pass
                        await asyncio.sleep(1.75 * waitCount)
                break
        #########################################
        await Messages(
            "```Building channels from source.\nTarget Guild: " + str(TargetGuild.name) + "\nSourceGuild: " + str(
                SourceGuild.name) + "```", ctx, sysChannel, None)
        await asyncio.sleep(1.75 * waitCount)
        # await sysChannel2.send("```Building channels from source.\nTarget Guild: " + str(TargetGuild.name) + "\nSourceGuild: " + str(SourceGuild.name) + "```")
        await asyncio.sleep(1.75 * waitCount)
        ######################################### LOG CHANNELS TO ARRAY #########################################
        categoryArray = []
        textChannelArray = []
        voiceChannelArray = []
        for guild in bot.guilds:
            if guild.id == SourceGuild.id:
                SourceGuildC = guild
                for category in SourceGuildC.categories:
                    categoryArray.append(category)
                for Tchannel in SourceGuildC.text_channels:
                    try:
                        textChannelArray.append([Tchannel, Tchannel.category.name])
                    except (HTTPException, AttributeError) as e:
                        textChannelArray.append([Tchannel, None])
                        pass
                for vchannel in SourceGuildC.voice_channels:
                    try:
                        voiceChannelArray.append([vchannel, vchannel.category.name])
                    except (HTTPException, AttributeError) as e:
                        voiceChannelArray.append([vchannel, None])
                        pass
                break
        print(str(categoryArray))
        print(str(textChannelArray))
        print(str(voiceChannelArray))
        ######################################### CREATE CHANNELS WITHOUT PERMISSIONS #########################################
        for guild in bot.guilds:
            if guild.id == TargetGuild.id:
                TargetGuildC2 = guild
                for each in categoryArray:
                    if each.name != '_constant_':
                        await TargetGuildC2.create_category_channel(each.name)
                        await asyncio.sleep(1.75 * waitCount)
        #########################################
        for guild in bot.guilds:
            if guild.id == TargetGuild.id:
                TargetGuildC = guild
                print(str(TargetGuildC))
                counter = -1
                for each in textChannelArray:
                    counter = counter + 1
                    if each[1] is not None and each[0].name != '_constant_' and each[0].name != '_sys_':
                        cat = discord.utils.get(TargetGuildC.channels, name=each[1])
                        try:
                            await TargetGuildC.create_text_channel(each[0].name, category=cat)
                        except:
                            await TargetGuildC.create_text_channel(each[0].name)
                            pass
                        await asyncio.sleep(1.75 * waitCount)
                    elif each[0].name != '_constant_' and each[0].name != '_sys_':
                        await TargetGuildC.create_text_channel(each[0].name)
                        await asyncio.sleep(1.75 * waitCount)
                break
        #########################################
        for guild in bot.guilds:
            if guild.id == TargetGuild.id:
                TargetGuildC3 = guild
                print(str(TargetGuildC3))
                counter = -1
                for each in voiceChannelArray:
                    counter = counter + 1
                    if each[1] is not None and each[0].name != '_constant_':
                        cat = discord.utils.get(TargetGuildC3.channels, name=each[1])
                        try:
                            await TargetGuildC3.create_voice_channel(each[0].name, category=cat)
                        except HTTPException:
                            await TargetGuildC3.create_voice_channel(each[0].name)
                            pass
                        await asyncio.sleep(1.75 * waitCount)
                    elif each[0].name != '_constant_':
                        await TargetGuildC3.create_voice_channel(each[0].name)
                        await asyncio.sleep(1.75 * waitCount)
                break
        return "Finished"

    async def removeAllRoles(ctx, TargetGuild, SourceGuild, waitCount, bot):
        global pop, sysChannelID
        sysChannel = await bot.fetch_channel(sysChannelID)
        TargetGuild = await bot.fetch_guild(TargetGuild.id)
        SourceGuild = await bot.fetch_guild(SourceGuild.id)
        ctx2 = ctx
        ctx = ctx2.message.channel
        ######################################### REMOVE ALL ROLES FROM TARGET SERVER #########################################
        await Messages("```Removing any and all existing roles on Target.\nTarget Guild: " + str(
            TargetGuild.name) + "\nSourceGuild: " + str(SourceGuild.name) + "```", ctx, sysChannel, None)
        await asyncio.sleep(1.75 * waitCount)
        await asyncio.sleep(1.75 * waitCount)
        delstr = ""
        roles_str = ""
        for role in TargetGuild.roles:
            if str(role.name).lower() != '@everyone':
                roles_str = roles_str + " " + str(role)
                try:
                    await role.delete()
                    await asyncio.sleep(1.75 * waitCount)
                    delstr = delstr + "\n\nDeleted: " + str(role.name) + " with permissions: " + str(
                        role.permissions) \
                             + " on server: " + str(TargetGuild)
                except HTTPException:
                    pass
                await asyncio.sleep(1.75 * waitCount)
        #########################################
        x = 1500
        res = [delstr[y - x:y] for y in range(x, len(delstr) + x, x)]
        for strings in res:
            await Messages("```" + str(strings) + "```", ctx, sysChannel, None)
            await asyncio.sleep(1.75 * waitCount)
            await asyncio.sleep(1.75 * waitCount)
        return "Finished"

    # @bot.command(name="channelperms")
    # async def channelpermsynccom(ctx):
    async def channelPermSync(ctx, TargetGuild, SourceGuild, waitCount, bot):
        global pop, sysChannelID
        sysChannel = await bot.fetch_channel(sysChannelID)
        #TargetGuild = await bot.fetch_guild(TargetGuild.id)
        #SourceGuild = await bot.fetch_guild(SourceGuild.id)
        #ctx2 = ctx
        #ctx = ctx2.message.channel
        SourceID = SourceGuild.id
        pop = True
        categoryArray = []
        textChannelArray = []
        voiceChannelArray = []
        for guild in bot.guilds:
            if stopcmd == 1:
                break
            if guild.id == SourceID:
                ChannelSource = guild
                ######################################### LOG CHANNELS TO ARRAY #########################################
                for each in ChannelSource.categories:
                    for key in each.overwrites:
                        overwritefor = key
                        ovrRIGHTS = each.overwrites_for(overwritefor)
                        await asyncio.sleep(1.75 * waitCount)
                        categoryArray.append([each, overwritefor, ovrRIGHTS])
                        print(str(each) + " \n" + str(overwritefor) + " \n" + str(ovrRIGHTS) + "\n\n")
                #########################################
                for each in ChannelSource.text_channels:
                    ovrRIGHTS = None
                    overwritefor = None  #####LAW FIRM
                    for key in each.overwrites:
                        overwritefor = key
                        ovrRIGHTS = each.overwrites_for(overwritefor)
                        await asyncio.sleep(1.75 * waitCount)
                    try:
                        textChannelArray.append([each, each.category.name, overwritefor, ovrRIGHTS])
                        print(str(each) + str(each.category) + " \n" + str(overwritefor) + " \n" + str(
                            ovrRIGHTS) + "\n\n")
                    except (HTTPException, AttributeError) as e:
                        textChannelArray.append([each, None, each.overwrites])
                        print(str(each) + "\nNONE\n" + str(overwritefor) + " \n" + str(ovrRIGHTS) + "\n\n")
                        pass
                #########################################
                for each in ChannelSource.voice_channels:
                    ovrRIGHTS = None
                    overwritefor = None
                    for key in each.overwrites:
                        overwritefor = key
                        ovrRIGHTS = each.overwrites_for(overwritefor)
                        await asyncio.sleep(1.75 * waitCount)
                    try:
                        voiceChannelArray.append([each, each.category.name, overwritefor, ovrRIGHTS])
                        print(str(each) + str(each.category) + " \n" + str(overwritefor) + " \n" + str(
                            ovrRIGHTS) + "\n\n")
                    except (HTTPException, AttributeError) as e:
                        voiceChannelArray.append([each, None, overwritefor, ovrRIGHTS])
                        print(str(each) + "\nNONE\n" + str(overwritefor) + " \n" + str(ovrRIGHTS) + "\n\n")
                        pass
        for guild in bot.guilds:  #####LAW FIRM
            if guild.id == TargetGuild.id:
                for each in categoryArray:
                    if stopcmd == 1:
                        break
                    if each[1] is not None:
                        if len(str(each[1])) > 1:
                            await Messages(
                                "```" + "-- || Channel: " + str(each[0].name) + "\n-- || Perm Key: " + str(
                                    each[1]) + \
                                "\n-----------------------------------------\n" + str(each[2]) + \
                                "\n-----------------------------------------\nTarget Guild: " + str(
                                    TargetGuild.name) + \
                                "\nSourceGuild: " + str(SourceGuild.name) + "```", ctx, sysChannel, None)
                            await asyncio.sleep(1.75 * waitCount)
                            for cats in guild.categories:
                                print("Parsing... " + str(cats.name).lower() + "\nAgainst: " + str(
                                    each[0].name).lower())
                                if str(cats.name).lower() == str(each[0].name).lower():
                                    await Messages("```" + str(each[0].name) + "\nMatches\n" + str(cats.name) + \
                                                   "\napplying roles for:\n---" + str(
                                        each[2]) + "---\nif exists\nTarget Guild: " + str(TargetGuild.name) + \
                                                   "\nSourceGuild: " + str(SourceGuild.name) + "```", ctx,
                                                   sysChannel, None)
                                    await asyncio.sleep(1.75 * waitCount)
                                    for roles in guild.roles:
                                        if str(roles.name).lower() == str(each[1]).lower():
                                            for key in each[2]:
                                                print(str("for"))
                                                print(str(key))
                                                #try:
                                                #    await cats.set_permissions(roles, overwrite=key)
                                                #    await asyncio.sleep(1.75 * waitCount)
                                                #except:
                                                #    pass
                                            await cats.set_permissions(roles, overwrite=each[2])
                                            await asyncio.sleep(1.75 * waitCount)
                for each in voiceChannelArray:
                    if stopcmd == 1:
                        break
                    if each[2] is not None:
                        if len(str(each[2])) > 1:
                            await Messages("```" + "-- || " + str(each[0].name) + "\n" + str(each[2]) + \
                                           "\n-----------------------------------------\n" + str(each[3]) + \
                                           "\n-----------------------------------------\nTarget Guild: " + str(
                                TargetGuild.name) + \
                                           "\nSourceGuild: " + str(SourceGuild.name) + "```", ctx, sysChannel, None)
                            await asyncio.sleep(1.75 * waitCount)
                            for texts in guild.text_channels:
                                print("Parsing... " + str(texts.name).lower() + "\nAgainst: " + str(
                                    each[0].name).lower())
                                if str(texts.name).lower() == str(each[0].name).lower():
                                    await Messages("```" + str(each[0].name) + "\nMatches\n" + str(texts.name) + \
                                                   "\napplying roles for:\n---" + str(
                                        each[3]) + "---\nif exists\nTarget Guild: " + \
                                                   str(TargetGuild.name) + "\nSourceGuild: " + str(
                                        SourceGuild.name) + "```", ctx, sysChannel, None)
                                    await asyncio.sleep(1.75 * waitCount)
                                    for roles in guild.roles:
                                        if str(roles.name) == str(each[2]):
                                            for key in each[2]:
                                                print(str("for"))
                                                print(str(key))
                                            await texts.set_permissions(roles, overwrite=each[2])
                                            await asyncio.sleep(1.75 * waitCount)
                for each in textChannelArray:
                    if stopcmd == 1:
                        break
                    if each[2] is not None:
                        if len(str(each[3])) > 1:
                            await Messages("```" + "-- || " + str(each[0].name) + "\n" + str(each[2]) + \
                                           "\n-----------------------------------------\n" + str(each[3]) + \
                                           "\n-----------------------------------------\nTarget Guild: " + \
                                           str(TargetGuild.name) + "\nSourceGuild: " + str(
                                SourceGuild.name) + "```", ctx, sysChannel, None)
                            await asyncio.sleep(1.75 * waitCount)
                            for feces in guild.voice_channels:
                                print("Parsing... " + str(feces.name).lower() + "\nAgainst: " + str(
                                    each[0].name).lower())
                                if str(feces.name).lower() == str(each[0].name).lower():
                                    await Messages("```" + str(each[0].name) + "\nMatches\n" + str(feces.name) + \
                                                   "\napplying roles for:\n---" + str(
                                        each[3]) + "---\nif exists\nTarget Guild: " + \
                                                   str(TargetGuild.name) + "\nSourceGuild: " + str(
                                        SourceGuild.name) + "```", ctx, sysChannel, None)
                                    await asyncio.sleep(1.75 * waitCount)
                                    for roles in guild.roles:
                                        if str(roles.name) == str(each[2]):
                                            for key in each[2]:
                                                print(str("for"))
                                                print(str(key))
                                            await feces.set_permissions(roles, overwrite=each[2])
                                            await asyncio.sleep(1.75 * waitCount)
        return "Finished"

    # async def buildRoles(ctx, SourceGuild, TargetGuild):
    async def getCreateRolesArray(ctx, SourceGuild, TargetGuild, waitCount, bot):
        global pop, sysChannelID
        sysChannel = await bot.fetch_channel(sysChannelID)
        TargetGuild = await bot.fetch_guild(TargetGuild.id)
        SourceGuild = await bot.fetch_guild(SourceGuild.id)
        ctx2 = ctx
        ctx = ctx2.message.channel
        #####LAW FIRM
        pop = True
        createRolesArray = []
        for guild in bot.guilds:
            if guild.id == SourceGuild.id:  #########################################  CHANGE SOURCE FOR ROLES HERE
                for role in guild.roles:
                    await asyncio.sleep(1.75 * waitCount)
                    if str(role.name).lower() != '@everyone' and 'twitch' not in str(role.name).lower():
                        createRolesArray.append(
                            [role.colour, role.color, role.permissions, role.mentionable, role.name,
                             role.hoist, guild.name])
                        # rolesMembers.append([role.name, role.members])
                        print(str(guild.name) + "\n" + str(role.name) + "\n" + str(bot.user))
                        await asyncio.sleep(1.75 * waitCount)
                return createRolesArray
        return createRolesArray

    async def applyRoles(ctx, TargetGuild, SourceGuild, waitCount, createRolesArray, bot):
        global pop, sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
        #TargetGuild = await bot.fetch_guild(TargetGuild.id)
        #SourceGuild = await bot.fetch_guild(SourceGuild.id)
        ######################################### CREATE ROLES ON TARGET SERVER #########################################
        roleStr = ""
        roleCount = -1
        for key in createRolesArray:
            roleCount = roleCount + 1
        tempRoleArray = []
        for role in TargetGuild.roles:
            tempRoleArray.append(role.name)
        roleCount = roleCount + 1
        while roleCount >= 0:
            roleCount = roleCount - 1
            print(str(roleCount) + "\n" + str(createRolesArray[roleCount]))
            exists = 0
            for roleName in tempRoleArray:
                if str(roleName).lower() == str(createRolesArray[roleCount][4]).lower():
                    exists = 1
                    break
            if exists == 0:
                await TargetGuild.create_role(colour=createRolesArray[roleCount][0],
                                              color=createRolesArray[roleCount][1],
                                              permissions=createRolesArray[roleCount][2],
                                              mentionable=createRolesArray[roleCount][3],
                                              name=createRolesArray[roleCount][4],
                                              hoist=createRolesArray[roleCount][5])
                print(str(createRolesArray[roleCount]) + "\n\n")
                await asyncio.sleep(1.75 * waitCount)
                roleStr = roleStr + "\n\n" + str(createRolesArray[roleCount][4]) + " from: " + str(
                    createRolesArray[roleCount][6]) \
                          + " to: " + str(TargetGuild)
        #########################################
        x = 1500
        res = [roleStr[y - x:y] for y in range(x, len(roleStr) + x, x)]
        for strings in res:
            await Messages("```" + str(strings) + "```", ctx, sysChannel, None)
            await asyncio.sleep(1.75 * waitCount)
            await asyncio.sleep(1.75 * waitCount)
        return "Finished"  #####LAW FIRM
        #####LAW FIRM

    @bot.command(name="stop")
    async def stopcmd(ctx):
        global stopcmd
        stopcmd = 1
        return

    #####LAW FIRM
    async def checkroles(ctx, TargetGuild, SourceGuild, waitCount, bot):
        global pop, sysChannelID
        sysChannel = await bot.fetch_channel(sysChannelID)
        ctx2 = ctx
        ctx = ctx2.message.channel
        TargetGuild = await bot.fetch_guild(TargetGuild.id)
        SourceGuild = await bot.fetch_guild(SourceGuild.id)
        pop = True
        ######################################### COLLECT MEMBER DATA AND THEIR ROLES!!!!! #########################################
        ######################################### FILES EXIST IN \SAVES
        ############ SKIPPING DATA COLLECTION READING FILES APPLYING ROLES
        ############ LATER CHECK FOR CHANGES USE FILES TO CROSS REFERENCE WITH MEMBER COUNT
        if not os.path.exists(HomeDir + r"\Saves\\" + str(TargetGuild.id) + "\TargetMembers.npy"):
            try:
                os.mkdir(HomeDir + r"\Saves\\" + str(TargetGuild.id))
            except:
                pass
            await buildTargetMemberList(ctx, TargetGuild, SourceGuild, waitCount)
        if not os.path.exists(HomeDir + r"\Saves\\" + str(SourceGuild.id) + "\SourceMembers.npy"):
            try:
                os.mkdir(HomeDir + r"\Saves\\" + str(SourceGuild.id))
            except:
                pass
            await buildSourceMemberList(ctx, TargetGuild, SourceGuild, waitCount)
        TargetMembersPre = numpy.load(HomeDir + r"\Saves\\" + str(TargetGuild.id) + "\TargetMembers.npy")
        SourceMembersPre = numpy.load(HomeDir + r"\Saves\\" + str(SourceGuild.id) + "\SourceMembers.npy")
        rolesStr = ""
        for key in SourceMembersPre:
            for key2 in TargetMembersPre:
                if key[0] == key2[0]:
                    try:
                        member = await TargetGuild.fetch_member(key2[0])
                        await asyncio.sleep(1.75 * waitCount)
                        for roles in TargetGuild.roles:
                            if str(roles.name).lower() in str(key[2]).lower() and str(
                                    roles.name).lower() != '@everyone':
                                try:
                                    await member.add_roles(roles)
                                    # member.edit
                                    await asyncio.sleep(1.75 * waitCount)
                                    rolesStr = rolesStr + str(roles.name) + " " + str(member) + "\n"
                                    print(str(roles.name) + " " + str(member) + "\n")
                                except (NameError, Forbidden) as e:
                                    pass
                                await asyncio.sleep(1.75 * waitCount)
                    except NotFound:
                        pass
        x = 1500
        res = [rolesStr[y - x:y] for y in range(x, len(rolesStr) + x, x)]
        for strings in res:
            await Messages("```" + str(strings) + "```", ctx, sysChannel, None)
            await asyncio.sleep(1.75 * waitCount)
            await asyncio.sleep(1.75 * waitCount)
        return

    async def memberloper(string=""):
        PreCheckSourceMembers = []
        PreCheckSourceMembers2 = []
        for letter in ascii_lowercase:
            PreCheckSourceMembers.append(await SourceGuild.query_members(query=str(string + letter)))
            await asyncio.sleep(1.75 * waitCount)
            print(str(letter) + ": " + str(len(PreCheckSourceMembers)) + "\n" + str(PreCheckSourceMembers))
            if len(PreCheckSourceMembers) >= 5:
                PreCheckSourceMembers2.append(await memberlooper(letter))
                PreCheckSourceMembers.extend(PreCheckSourceMembers2)
                PreCheckSourceMembers2 = []
        return PrecheckSourceMembers




    async def buildSourceMemberList(ctx, TargetGuild, SourceGuild, waitCount):
        global pop, sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
#        TargetGuild = await bot.fetch_guild(TargetGuild.id)
#        SourceGuild = await bot.fetch_guild(SourceGuild.id)
#        ctx = await getCTX(ctx)
        SourceMembers = []
        SourceMembers2 = []
        s_mem_str = ""
        for letter in ascii_lowercase:
            PreCheckSourceMembers = await SourceGuild.query_members(query=str(letter))
            await asyncio.sleep(1.75 * waitCount)
            print(str(letter) + ": " + str(len(PreCheckSourceMembers)) + "\n" + str(PreCheckSourceMembers))
            if len(PreCheckSourceMembers) >= 5:
                await ctx.send("```" + str(letter) + ": " + str(len(PreCheckSourceMembers)) + "```")
                await asyncio.sleep(1.75 * waitCount)
                for letter2 in ascii_lowercase:
                    PreCheckSourceMembers = await SourceGuild.query_members(query=str(letter + letter2))
                    await asyncio.sleep(1.75 * waitCount)
                    print(
                        str(letter + letter2) + ": " + str(len(PreCheckSourceMembers)) + "\n" + str(
                            PreCheckSourceMembers))
                    if len(PreCheckSourceMembers) >= 5:
                        await ctx.send(
                            "```" + str(letter) + ": " + str(letter2) + " " + str(
                                len(PreCheckSourceMembers)) + "```")
                        await asyncio.sleep(1.75 * waitCount)
                        for letter3 in ascii_lowercase:
                            PreCheckSourceMembers = await SourceGuild.query_members(
                                query=str(letter + letter2 + letter3))
                            await asyncio.sleep(1.75 * waitCount)
                            print(str(letter + letter2 + letter3) + ": " + str(
                                len(PreCheckSourceMembers)) + "\n" + str(
                                PreCheckSourceMembers))
                            for p_member in PreCheckSourceMembers:
                                exists = 0
                                for c_member in SourceMembers:
                                    print(str(p_member.name) + " - " + str(c_member.name))
                                    if c_member.id == p_member.id:
                                        exists = 1
                                if exists == 0:
                                    SourceMembers.append(p_member)
                                    SourceMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                                    s_mem_str = s_mem_str + "\n" + " " + \
                                                str(p_member.name) + " " + str(p_member.roles) + "\n"
                    else:
                        for p_member in PreCheckSourceMembers:
                            exists = 0
                            for c_member in SourceMembers:
                                print(str(p_member.name) + " - " + str(c_member.name))
                                if c_member.id == p_member.id:
                                    exists = 1
                            if exists == 0:
                                SourceMembers.append(p_member)
                                SourceMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                                s_mem_str = s_mem_str + "\n" + " " + \
                                            str(p_member.name) + " " + str(p_member.roles) + "\n"
            else:
                for p_member in PreCheckSourceMembers:
                    exists = 0
                    for c_member in SourceMembers:
                        print(str(p_member.name) + " - " + str(c_member.name))
                        if c_member.id == p_member.id:
                            exists = 1
                    if exists == 0:
                        SourceMembers.append(p_member)
                        SourceMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                        s_mem_str = s_mem_str + "\n" + " " + str(p_member.name) + " " + str(p_member.roles) + "\n"
            await asyncio.sleep(3)
        numpy.save(HomeDir + r"\Saves\\" + str(SourceGuild.id) + "\SourceMembers.npy", SourceMembers2)
        await asyncio.sleep(3)
        x = 1500
        res = [s_mem_str[y - x:y] for y in range(x, len(s_mem_str) + x, x)]
        for strings in res:
            await Messages("```" + str(strings) + "```", ctx, sysChannel, None)
            await asyncio.sleep(1.75 * waitCount)
            await asyncio.sleep(1.75 * waitCount)
        return

    async def buildTargetMemberList(ctx, TargetGuild, SourceGuild, waitCount):
        global pop, sysChannelID
        sysChannel = await bots[0].fetch_channel(sysChannelID)
        #TargetGuild = await bot.fetch_guild(TargetGuild.id)
        #SourceGuild = await bot.fetch_guild(SourceGuild.id)
        TargetMembers = []
        TargetMembers2 = []
        t_mem_str = ""
        for letter in ascii_lowercase:
            PreCheckTargetMembers = await TargetGuild.query_members(query=str(letter))
            await asyncio.sleep(1.75 * waitCount)
            print(str(letter) + ": " + str(len(PreCheckTargetMembers)) + "\n" + str(PreCheckTargetMembers))
            if len(PreCheckTargetMembers) >= 5:
                await ctx.send("```" + str(letter) + ": " + str(len(PreCheckTargetMembers)) + "```")
                await asyncio.sleep(1.75 * waitCount)
                for letter2 in ascii_lowercase:
                    PreCheckTargetMembers = await TargetGuild.query_members(query=str(letter + letter2))
                    await asyncio.sleep(1.75 * waitCount)
                    print(str(letter + letter2) + ": " + str(len(PreCheckTargetMembers)) + "\n" + str(
                        PreCheckTargetMembers))
                    if len(PreCheckTargetMembers) >= 5:
                        await ctx.send("```" + str(letter) + ": " + str(letter2) + " " + str(
                            len(PreCheckTargetMembers)) + "```")
                        await asyncio.sleep(1.75 * waitCount)
                        for letter3 in ascii_lowercase:
                            PreCheckTargetMembers = await TargetGuild.query_members(
                                query=str(letter + letter2 + letter3))
                            await asyncio.sleep(1.75 * waitCount)
                            print(str(letter + letter2 + letter3) + ": " + str(
                                len(PreCheckTargetMembers)) + "\n" + str(PreCheckTargetMembers))
                            for p_member in PreCheckTargetMembers:
                                exists = 0
                                for c_member in TargetMembers:
                                    print(str(p_member.name) + " - " + str(c_member.name))
                                    if c_member.id == p_member.id:
                                        exists = 1
                                if exists == 0:
                                    TargetMembers.append(p_member)
                                    TargetMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                                    t_mem_str = t_mem_str + "\n" + " " + \
                                                str(p_member.name) + " " + str(p_member.roles) + "\n"
                    else:
                        for p_member in PreCheckTargetMembers:
                            exists = 0
                            for c_member in TargetMembers:
                                print(str(p_member.name) + " - " + str(c_member.name))
                                if c_member.id == p_member.id:
                                    exists = 1
                            if exists == 0:
                                TargetMembers.append(p_member)
                                TargetMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                                t_mem_str = t_mem_str + "\n" + " " + str(p_member.name) + " " + str(
                                    p_member.roles) + "\n"
            else:
                for p_member in PreCheckTargetMembers:
                    exists = 0
                    for c_member in TargetMembers:
                        print(str(p_member.name) + " - " + str(c_member.name))
                        if c_member.id == p_member.id:
                            exists = 1
                    if exists == 0:
                        TargetMembers.append(p_member)
                        TargetMembers2.append([p_member.id, p_member.name, str(p_member.roles)])
                        t_mem_str = t_mem_str + "\n" + " " + str(p_member.name) + " " + str(p_member.roles) + "\n"
        x = 1500
        res = [t_mem_str[y - x:y] for y in range(x, len(t_mem_str) + x, x)]
        for strings in res:
            await Messages("```" + str(strings) + "```", ctx, sysChannel, None)
            await asyncio.sleep(1.75 * waitCount)
            await asyncio.sleep(1.75 * waitCount)
        ######################################### APPLY ROLES TO MEMBERS #########################################
        numpy.save(HomeDir + r"\Saves\\" + str(TargetGuild.id) + "\TargetMembers.npy", TargetMembers2)
        await asyncio.sleep(3)
        return

    @bot.event
    async def on_guild_channel_edit():
        global SourceID, TargetID, TargetGuild, SourceGuild, lastChannel, pop, sysChannel
        global lastChanneled
        if channel.guild.id == 328357828526080002:
            return
        CurrentGuild = ""
        print("CHANNEL EDIT BOT EVENT?!")
        if int(channel.guild.id) != int(TargetID) and int(channel.guild.id) != int(SourceID):
            return
        if pop == True:
            return
        if channel.name == lastChanneled:
            return
        lastChanneled = channel.name
        try:
            cat = channel.category.name
        except:
            cat = None
        if channel.guild.id == TargetID:
            # chanGuild = TargetGuild
            CurrentGuild = SourceGuild
        if channel.guild.id == SourceID:
            # chanGuild = SourceGuild
            CurrentGuild = TargetGuild
        chnl2edit = discord.utils.get(CurrentGuild.channels, name=channel.name)
        cat2 = discord.utils.get(CurrentGuild.channels, name=channel.category.name)
        if str(cat) != str(cat2.name):
            try:
                await chnl2edit.edit(category=cat2)
            except:
                pass
        return

    @bot.event
    async def on_guild_channel_delete(channel):
        global SourceID, TargetID, TargetGuild, SourceGuild, lastChannel, pop, sysChannel
        global lastChannelde
        if True:
            return
        if pop == True:
            return
        if channel.guild.id == 328357828526080002:
            return
        CurrentGuild = ""
        chanGuild = ""
        if int(channel.guild.id) != int(TargetID) and int(channel.guild.id) != int(SourceID):
            return
        if channel.name == lastChannelde:
            return
        lastChannelde = channel.name
        if channel.guild.id == TargetID:
            chanGuild = TargetGuild
            CurrentGuild = SourceGuild
        if channel.guild.id == SourceID:
            chanGuild = SourceGuild
            CurrentGuild = TargetGuild
        chnl2del = discord.utils.get(CurrentGuild.channels, name=channel.name)
        try:
            await chnl2del.delete()
            await Messages("As - Channel: " + str(channel.name) + " was deleted in server: " + str(chanGuild) + \
                           "\nSo - Channel: " + str(channel.name) + " was deleted in server: " + str(CurrentGuild),
                           ctx, sysChannel, None)
            lastChannelde = channel.name
        except:
            pass
        return

    @bot.event
    async def on_guild_channel_create(channel):
        global SourceID, TargetID, TargetGuild, SourceGuild, lastChannelcr
        global pop, sysChannel, lastChannelcr
        if True:
            return
        if channel.guild.id == 328357828526080002:
            return
        if pop == True:
            return
        # counter = await gcount()
        if channel.name == lastChannelcr:
            #    if counter > 2:
            #        await gcount()
            #        await channel.delete()
            return
        # if counter > 2:
        #    await gcount(1)
        lastChannelcr = channel.name
        CurrentGuild = ""
        if int(channel.guild.id) != int(TargetID) and int(channel.guild.id) != int(SourceID):
            return
        if channel.guild.id == TargetID:
            chanGuild = TargetGuild
            CurrentGuild = SourceGuild
        if channel.guild.id == SourceID:
            chanGuild = SourceGuild
            CurrentGuild = TargetGuild
            await Messages("As - Channel: " + str(channel.name) + " was created in server: " + str(chanGuild) + \
                           "\nSo - Channel: " + str(channel.name) + " was created in server: " + str(CurrentGuild),
                           ctx, sysChannel, None)
        try:
            cat = discord.utils.get(CurrentGuild.channels, name=channel.category.name)
            if str(channel.type) == 'text':
                await CurrentGuild.create_text_channel(channel.name, category=cat)
                return
            if str(channel.type) == 'voice':
                await CurrentGuild.create_voice_channel(channel.name, category=cat)
                return
        except AttributeError:
            if str(channel.type) == 'text':
                await CurrentGuild.create_text_channel(channel.name)
                return
            if str(channel.type) == 'voice':
                await CurrentGuild.create_voice_channel(channel.name)
                return
            if str(channel.type) == 'category':
                await CurrentGuild.create_category_channel(channel.name)
                return
        # if channel.category == category:
        # run

    # if channel.category == category and type(channel) == discord.VoiceChannel:
    async def gcount(reset=0):
        global gcounter
        if reset == 1:
            gcounter = -1
        if reset == 0:
            return gcounter
        gcounter = gcounter + 1
        return gcounter

    async def Messages(msgstr=None, ctx=None, sys=None, SerbzFlag=None):
        global sysChannelID
        if ctx is not None:
            await ctx.send(str(msgstr))
            await asyncio.sleep(2)
        if sys is not None:
            await sys.send(str(msgstr))
            await asyncio.sleep(2)
        return


async def wrapped_connect2(f):
    await f[0].start(f[1])


ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
HomeDir = 'Z:\_Cloner'
VarDir = HomeDir + r'\VariableVariables'
LogDir = HomeDir + r'\Logs'
StaticVarDir = HomeDir + r'\StaticVars'
SoundDir = HomeDir + r'\Sound'
ChromeDir = HomeDir + r'\Chrome'
ScriptDir = HomeDir + r'\SkrippitySkripz'
ImgDir = HomeDir + r'\ImageSearch'
SerbzDir = HomeDir + r'\SerbzDir'
lastChannelcr = [1]
thisChannel = [0]
lastChannelde = [2]
pop = False
g2_counter = -1
lastChanneled = [3]
gcounter = 0
waitCount = 1
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TOKEN2 = os.getenv('DISCORD_TOKEN2')
TOKEN3 = os.getenv('DISCORD_TOKEN3')
TOKEN4 = os.getenv('DISCORD_TOKEN4')
TOKEN5 = os.getenv('DISCORD_TOKEN5')
TOKEN6 = os.getenv('DISCORD_TOKEN6')
bots: List[Bot] = []
entries = []
TOKENS = [
    os.getenv('DISCORD_TOKEN'),
    os.getenv('DISCORD_TOKEN2'),
    os.getenv('DISCORD_TOKEN3'),
    os.getenv('DISCORD_TOKEN4'),
    os.getenv('DISCORD_TOKEN5'),
    os.getenv('DISCORD_TOKEN6'),
]
sysChannelID = 871650184881401876
globalIterator = 0
counter = -1
for each in TOKENS:
    counter = counter + 1
    if counter == 0:
        bots.append(commands.Bot(command_prefix='$', help_command=None))
    else:
        bots.append(commands.Bot(command_prefix='!@#', help_command=None))
counter = -1
for each in TOKENS:
    counter = counter + 1
    entries.append([bots[counter], each])
globalIteratorLimit = counter
botIndexCounter = 0


StopIterationVar = 0
for e in entries:
    loop.create_task(wrapped_connect2(e))
    loop.create_task(wrapped_connect(e, bots))

# for bot in bots:
#    loop.create_task(globalIteratorListener(bot))
loop.run_forever()
