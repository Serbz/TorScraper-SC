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
    try:
        from pafy import new
    except:
        os.system("pip install youtube_dl")
        from pafy import new
        pass
    from pyscreenshot import FailedBackendError
    from lxml import etree
    from bs4 import BeautifulSoup, SoupStrainer
    #from win32api import GetSystemMetrics
    from mmappickle import mmapdict
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
            #try:
            #    if bot.user.id == bots[0].user.id:
            #        try:
            #            print("RECV: " + str(msg.decode("utf-8", "replace")))
            #        except:
            #            pass
            #except:
            #    pass
            return

        # @bot.event
        # async def on_message(message):
        #    return

        @bot.event
        async def on_typing(channel, user, when):
            if bot.user.id == bots[0].user.id:
                print("ONTYPE: " + str(channel) + " - " + str(user) + " - " + str(when))
            return

        @bot.event
        async def on_guild_channel_delete(channel):
            if bot.user.id == bots[0].user.id:
                print("GUILDCHANDEL: " + str(channel))
            return

        @bot.event
        async def on_guild_channel_create(channel):
            if bot.user.id == bots[0].user.id:
                print("GUILDCHANCREATE: " + str(channel))
            return

        @bot.event
        async def on_guild_channel_update(before, after):
            if bot.user.id == bots[0].user.id:
                print("GUILDCHANUPDATE: " + str(before) + " - " + str(after))
            return

        @bot.event
        async def on_member_join(member):
            if bot.user.id == bots[0].user.id:
                print("MEMBRJOIN" + str(member))
            return

        @bot.event
        async def on_member_remove(member):
            if bot.user.id == bots[0].user.id:
                print("MEMBRREMOVE" + str(member))
            return

        #@bot.event
        #async def on_ready():
        #    taskloops = []
        #    if bot.user.id == bots[0].user.id:
        #        for bot in bots:
        #            taskloops.append(yourArmyAwaits(bot))
        #    #print(str(taskloops))
        #    await asyncio.gather(*taskloops)
        #    return

        @bot.event
        async def on_command_error(ctx, error):
            global sysChannelID
            #sysChannel = await bots[0].fetch_channel(sysChannelID)
            if isinstance(error, CommandNotFound):
                #await ctx.send("command " + str(str(ctx.message.content).split(" ")[0]) + " not found.")
                return
            if isinstance(error, KeyError):
                return
            if isinstance(error, UnboundLocalError):
                return
            var = traceback.format_exc()
            #await Messages(str(var), None, sysChannel, None)
            raise error

        @bot.event
        async def on_ready():
            global bots
            taskloops = []
            counter = 0
            if bot.user.id == bots[0].user.id:
                for botius in bots:
                    counter += 1
                    taskloops.append(loop.create_task(yourArmyAwaits(botius)))
                    #print(counter)
                #taskloops.append(taskityTaskers(bot))
                #print(str(taskloops))
            #print(str(taskloops))

            await asyncio.gather(*taskloops)
            return

        async def yourArmyAwaits(bot):
            global sysChannelID, sysChannel
            print(str(bot.user.id) + " || " + str(bot.user.name) + "#" + str(bot.user.discriminator))
            #print(len(bots))
            for guild in bot.guilds:
                for textChannel in guild.text_channels:
                    if textChannel.id == sysChannelID:
                        sysChannel = await bot.fetch_channel(sysChannelID)

                        return

            #msg_str = "```"
            #msg_str = msg_str + "\n#-#-#-#-#-# Initialization #-#-#-#-#-# \n #-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#  \n"
            #############################################

            #Logger.LogPrint(discord.__version__)
            #strgB = ""
            #for guild in botius.guilds:
            #    strgB = strgB + "\n" + str(guild)
            #msg_str = msg_str + '\n' + r"logged in as: " + str(
            #    botius.user.name) + "\n" + str(
            #    botius.user.id) + '\n ------' + '\n Servers connected to:' + '\n #-#-#-#-#-#-#-#-#-#-#-#-#-' + strgB + "```"
            #############################################
            # await Messages(str(msg_str), None, sysChannel, None)
        #    return
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
                            #print(str(found_keywords))
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

        async def keywordCheck(data, ctx):
            dataSearch = "False"
            if "bridgeway" in str(data).lower() or "ponca" in str(data).lower():
                poggywoggyArray.append([data, URL])
                numpy.save(HomeDir + r"\Saves" + r"\Found_Keys_1.npy", poggywoggyArray)
                await ctx.send("```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!``` \n ```FOUND: \n\n" + str(
                    each[0]) + "\n\n```\n```!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                dataSearch = "True"
            return dataSearch


        async def getData(URL):
            socket.socket = socks.socksocket
            proxy = proxies[random.randint(1, len(proxies) - 1)]
            try:
                data = requests.get(URL, proxies=proxy, timeout=5).text
                print("Got Data on: " + str(proxy) + f" \n for {URL}")
                return data
            except:
                #print("problem getting data on: " + str(proxy))
                counter = 0
                for key in proxies:
                    #print("Trying proxy: " + str(key))
                    counter = counter + 1
                    try:
                        data = requests.get(each[0], proxies=key, timeout=5).text
                        print("Got Data on: " + str(key) + f" \n for {URL}")
                        return data
                    except:
                        pass
            return None

        async def scrapeWithSoup(data, message2edit, URL, ms2eString, ctx):
            counter = 0
            counter2= 0
            dataSearch = "Disabled"
            #print("Data Search was here")
            #dataSearch = await keywordCheck(data, ctx)
            #ms2eString = str(ms2eString) + "\n\n" + str(URL)
            #ms2eString = str(ms2eString) + "\n" + "Data search: " + dataSearch + "\n"
            #ms2eString = ms2eString + "FOUND LINKS:\n"
            soup = BeautifulSoup(data, features="lxml")
            for link in soup.find_all('a'):
                #print(str(link))
                if ".onion" in str(link.get('href')) and str(link.get('href')) != str(URL):
                    linksArray.append([str(link.get('href')), data])
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
            if bot.user.id == bots[0].user.id:
                if ctx.message.author.id != 246892047284436992 and ctx.author.id != 855613733854642237:
                    return
                counter = -1
                duplicateCheck = 0
                source = ""
                scrapeArray = []
                URL = "NaN"
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
                        if each == "-file": #torscrape -file someSaveFile -sourceOR-url /scrape
                            file = str(ctx.message.content).split(" ")[counter + 1]
                            filePath = HomeDir + r"/Saves/torScraper/" + str(file) + ".npy"
                            print(str(filePath) + "\n")
                            strFileSourceURL = strFileSourceURL + "File set as: " + str(filePath) + "\n"
                        if each == "-source":
                            source = str(ctx.message.content).split(" ")[counter + 1]
                            sourcePath = HomeDir + r"/Saves/torScraper/" + str(source) + ".npy"
                            print(str(sourcePath) + "\n")
                            strFileSourceURL = strFileSourceURL + "Source set as: " + str(sourcePath) + "\n"
                        if each == "-url":
                            URL = str(ctx.message.content).split(" ")[counter + 1]
                            print(str(URL))
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
                    strIteration = strIteration + "Iteration count not specified, Iteration set to: " + str(iterationCount) + "\n"

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
                if URL != "NaN" and source == "":
                    await ctx.send("scraping from scratch, no source file specified")
                    newScrape = 1
                else:
                    newScrape = 0



                if duplicateCheck == 1 or merge == 1:
                    await dupeCheck(source, file, ctx)
                    if merge == 1:
                        scrapeArray = await combineScrapes(file, source, ctx)
                sourceSize = 0
                if source != "" or newScrape == 0 and duplicateCheck != 1:
                    # load source#
                    print("here")
                    sourceArray = numpy.load(sourcePath, mmap_mode="r")#, allow_pickle=True)#allow_pickle=True, delimiter=r",")
                    sourceSize = int(find_between(str(sourceArray.shape), r"(", r","))
                    print(sourceSize)
                    sourceCounter = -1
                    for each in sourceArray:
            #            #['[\'http://jhi4v5rjly75ggha26cu2eeyfhwvgbde4w6d75vepwxt2zht5sqfhuqd.onion/\',
            #            str2list2source = find_between(str(each), "\'[\\\'http", "onion/\\\',")
            #            str2list2source = f"http{str2list2source}onion"
            #            if str2list2source != "httponion":
                            sourceCounter += 1
            #                #print(f"##############\nSOURCE : {str2list2source}\n##############\n")
            #                #await asyncio.sleep(0.1)
            #                str2list = str(str(each)).split("http")
            #                for key in str2list:
            #                    key = "http" + str(key)
            #                    link = find_between(str(key), r"http", r".onion")
            #                    if link != "http" and link != "http.onion" and r"//" in link and r"\\" not in link and r"<" not in link \
            #                            and ">" not in link and r"[" not in link and r"]" not in link and "\"" not in link and "|" not in link:
            #                        print("http" + str(link) + ".onion")
            #                        #await asyncio.sleep(0.25)
                else:
                    await ctx.send("idk how you got here but no.")
                    return
                if scrape == 1 or newScrape == 1:
                    #if source != "":
                        #source = ""
                        #for each in sourceArray:
                        #    linksArray.append(each[0])
                        #sourceArray = []

                    loops = 0
                    link_counter2 = 0
                    sourceCounter = -1
                    counter = 0
                    message2edit = await ctx.send("Beginning iteration.")
                    #print("here")
                    LinksArrayTemp = []
                    dataNone = 0
                    while counter < iterationCount or int(sourceCounter+1) < sourceSize:
                        if source != "":
                            sourceCounter += 1
                            #or each in sourceArray:
                            # ['[\'http://jhi4v5rjly75ggha26cu2eeyfhwvgbde4w6d75vepwxt2zht5sqfhuqd.onion/\',
                            str2list2source = find_between(str(sourceArray[sourceCounter]), "\'[\\\'http", "onion/\\\',")
                            str2list2source = f"http{str2list2source}onion"
                            if str2list2source != "httponion":
                                print(f"##############\nSOURCE : {str2list2source}\n##############\n")
                                #await asyncio.sleep(1)
                                str2list = str(str(sourceArray[sourceCounter])).split("http")
                                for key in str2list:
                                    key = "http" + str(key)
                                    link = find_between(str(key), r"http", r".onion")
                                    if link != "http" and link != "http.onion" and r"//" in link and r"\\" not in link and r"<" not in link \
                                            and ">" not in link and r"[" not in link and r"]" not in link and "\"" not in link and "|" not in link:
                                        print("http" + str(link) + ".onion")
                                        linksArray.append("http" + str(link) + ".onion")

                        counter += 1
                        counter2 = 0 # for checkpoints
                        LinksArrayTemp = []
                        for URL in linksArray:
                            dataNone = 0
                            #await asyncio.sleep(0.1)
                            counter2 = counter2 + 1
                            data = await getData(URL)
                            link_counter = 0
                            if data != None:
                                loops = loops + 1
                                link_counter2 = link_counter2 + 1
                                linksArrayReturn, message2edit, numLinks = await scrapeWithSoup(data, message2edit, URL, ms2eString, ctx)
                                LinksArrayTemp.extend(linksArrayReturn)
                                print("Found " + str(numLinks) + " onion URLs in " + str(URL))
                                linksArrayReturn = []
                                #print("\n\nPage: " + str(URL) + " yielded " + str(link_counter2) + " New links\n\n")
                                #await asyncio.sleep(1.75)
                                link_counter2=0
                                for URL in LinksArrayTemp:
                                    #print("LINKS ARRAY TEMP - " + str(URL))
                                    link_counter += 1
                                    scrapeArray.append([str(URL), str(data)])
                                counter2 = 0
                                numpy.save(filePath + f".{loops}.npy", scrapeArray)
                                scrapeArray = []
                                print(f"Saved scrapeArray ==> {filePath}.{loops}.npy")
                            else:
                                print(str("Data returned None!"))
                                print(str(URL))
                                dataNone = 1
                                #LinksArrayTemp = []

                            if dataNone != 1:
                                print("\n")
                                #linksArray = LinksArrayTemp
                                #LinksArrayTemp = []
                            else:
                                linksArray.remove(URL)
                    linksArray = LinksArrayTemp
                    LinksArrayTemp = []

                    #numpy.save(filePath, scrapeArray)
                    #await ctx.send("Database " + str(filePath) + " finished. Found " + str(link_counter) + " new links, and corresponding data")
                    print("\n\nDatabase " + str(filePath) + " finished. Found " + str(link_counter) + " new links, and corresponding data\n\n")

            return

        def find_between(s, first, last):
            try:
                start = s.index(first) + len(first)
                end = s.index(last, start)
                return s[start:end]
            except ValueError:
                return ""

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
            #print("```" + str(payload) + "```")
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
    #HomeDir = 'Z:\_Cloner'
    HomeDir = '/media/sf_X_DRIVE/_Cloner'
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
    lastChanneled = [3]
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
            bots.append(commands.Bot(command_prefix='^', help_command=None))
        else:
            bots.append(commands.Bot(command_prefix='!@#', help_command=None))
        entries.append([bots[counter], each])
        loop.create_task(wrapped_connect2(entries[counter]))
        loop.create_task(wrapped_connect(entries[counter], bots))
    #counter = -1
    #for each in TOKENS:
    #    counter = counter + 1

    globalIteratorLimit = counter
    botIndexCounter = 0
    #try:
        #loop.create_task(os.system("waitress-serve --listen=*:8000 torscraper:torscraper"))
    #except:
    #    try:
    #        os.system("pip install waitress")
    #    except:
    #        pass
    #    os.execv(sys.executable, ['python'] + sys.argv)
    #    SystemExit()
    #    sys.exit()
    #import mmappickle

    StopIterationVar = 0

    #for e in entries:


    # for bot in bots:
    #    loop.create_task(globalIteratorListener(bot))
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
    #print(str(stringy))
    if stringy == "dotenv":
        try:
            os.system("python3.9 -m pip install --upgrade pip")
            os.system("python3.9 -m pip install pipwin --compile --no-cache-dir")
            #os.system("pipwin refresh")
            os.system("pipwin install wheel")
            #os.system("pip install dotenv --disable-pip-version-check --force-reinstall --compile --no-cache-dir")
            try:
                os.system("python3.9 -m pip install python-" + stringy + " --compile --no-cache-dir")
                os.execv(sys.executable, ['python'] + sys.argv)
                SystemExit()
                sys.exit()
            except:
                pass
        except:
            pass
    if stringy == "pafy":
        try:
            os.system("python3.9 -m pip install youtube_dl")
        except:
            pass
        try:
            os.system("python3.9 -m pip install pafy")
        except:
            pass
        os.execv(sys.executable, ['python'] + sys.argv)
        SystemExit()
        sys.exit()
    if stringy == "win32api":
        try:
            os.system("python3.9 -m pip install pywin32")
        except:
            pass
        os.execv(sys.executable, ['python'] + sys.argv)
        SystemExit()
        sys.exit()
    #if stringy == "fcntl":
    #    try:
    #        os.system("pip install waitress")
    #    except:
    #        pass
    #    os.execv(sys.executable, ['python'] + sys.argv)
    #    SystemExit()
    #    sys.exit()
    try:
        os.system("python3.9 -m pip install " + stringy + " --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("python3.9 -m pip install python-" + stringy + " --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("python3.9 -m pip install " + stringy + "-python --compile --no-cache-dir")
    except:
        pass
    try:
        os.system("python3.9 -m pip install py" + stringy + " --compile --no-cache-dir")
    except:
        pass

    os.execv(sys.executable, ['python'] + sys.argv)
    SystemExit()
    sys.exit()
    pass

