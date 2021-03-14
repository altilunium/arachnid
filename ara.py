"""
    A Python program that crawls a website and recursively checks links to map all internal and external links
"""

from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
from urllib.parse import urlparse
from collections import deque
import re
import sys
import os
import subprocess
import argparse
from os.path import splitext
import furl
import signal
import sys

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
bandwithUsage = 0

def crawler(domain, ofile, mute):
    global new_urls,bandwithUsage,foreign_urls
    try:
        # a queue of urls to be crawled
        new_urls = deque([domain])
        # a set of urls that we have already crawled
        processed_urls = set()
        # a set of domains inside the target website
        local_urls = set()
        # a set of domains outside the target website
        foreign_urls = set()
        # a set of broken urls
        broken_urls = set()

        # process urls one by one until we exhaust the queue
        while len(new_urls):

            # move next url from the queue to the set of processed urls
            #print("Queue length : "+str(len(new_urls)))
            url = new_urls.popleft()
            processed_urls.add(url)
            # get url's content
            

            try:
                response = requests.head(url)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                # add broken urls to it's own set, then continue
                broken_urls.add(url)
                continue


            if 'content-type' in response.headers:
                content_type = response.headers['content-type']
                #print("Content Type : "+ content_type)
                if not 'text/html' in content_type:
                    #print("Not html. Skipping")
                    continue

            #download!
            actualPayload = bytearray()
            try:
                #print(str(len(new_urls))+" ",end='')
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')
                dl = 0
                if total_length is not None:
                	print(sizeof_fmt(int(total_length)))
                	bandwithUsage += int(total_length)
                	for data in response.iter_content(chunk_size=4096):
                		dl += len(data)
                		actualPayload = actualPayload + bytearray(data)
                		done = int(8*dl / int(total_length))
                		sys.stdout.write("\r[%s%s]" % ('=' * done, ' '* (8-done)))
                		sys.stdout.flush()
                	print()
                else:
                	actualPayload = bytearray(response.content)

            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                # add broken urls to it's own set, then continue
                broken_urls.add(url)
                continue
            try:
            	actualPayload = actualPayload.decode('utf-8')
            except UnicodeDecodeError as e:
            	continue


            # extract base url to resolve relative links
            '''
            parts = urlsplit(url)
            base = "{0.netloc}".format(parts)
            strip_base = base.replace("www.", "")
            base_url = "{0.scheme}://{0.netloc}".format(parts)
            path = url[:url.rfind('/')+1] if '/' in parts.path else url
            '''

            # create a beutiful soup for the html document
            #soup = BeautifulSoup(response.text, "lxml")
            soup = BeautifulSoup(actualPayload, "lxml")
            title = soup.find('title')


            input_base = urlparse(domain).netloc
            base = urlparse(url).netloc
            path = urlparse(url).path
            path = path.split("/")
            path = filter(lambda x:x!='',path)
            path = list(path)
            #print(path)

            print(str(len(new_urls))+" "+url,end='\r')

            dontprint = True
            try:
                if (path[0] == 'tag') or (path[0] == 'category') or (path[0] == 'author'):
                    dontprint = True
                elif len(path) == 2:
                    if path[0].isnumeric() and path[1].isnumeric():
                        dontprint = True
                elif len(path) == 3:
                    if path[0].isnumeric() and path[1].isnumeric() and path[2].isnumeric():
                        dontprint = True
                    elif path[0].isnumeric() and path[1].isnumeric() and path[2] == 'page':
                        dontprint = True
                else:
                    dontprint = False
            except IndexError as e:
                dontprint = False

            if not dontprint:
                sys.stdout.write("\033[K") 
                if title is not None:
                	print(title.string)
                print("%s" % url)
                print()
            else:
                sys.stdout.write("\033[K")


            



            for link in soup.find_all('a'):


                anchor = link.attrs["href"] if "href" in link.attrs else ''

                
                if anchor != '':
                	try:
                		anchor = furl.furl(anchor).remove(args=True,fragment=True).url
                	except ValueError as e:
                		continue

                if anchor == '':
                    continue

                anchor_base = urlparse(anchor).netloc
                if (anchor_base != input_base):
                    #print("External : "+str(anchor))
                    foreign_urls.add(anchor)
                else:
                    #print("Internal : "+str(anchor))
                    local_urls.add(anchor)


                '''
                if not base_url in anchor:
                	foreign_urls.add(anchor)
                	continue
                '''
                

                '''
                path = urlparse(url).path
                ext = splitext(path)[1]
                #print(ext)

                #print(anchor)
                #print("netloc:"+urlparse(anchor).netloc)

                if anchor.startswith('/')  :
                    local_link = base_url + anchor
                    local_urls.add(local_link)
                elif (urlparse(anchor).netloc == ''):
                	local_link = base_url + "/" + anchor
                	local_urls.add(local_link)
                elif not base_url in anchor:
                	foreign_urls.add(anchor)
                	continue
                    #print("Case 1 : " + local_link)
                elif strip_base in anchor:
                    local_urls.add(anchor)
                    #print("Case 2 : " + anchor)
                elif not anchor.startswith('http'):
                    local_link = path + anchor
                    local_urls.add(local_link)
                    #print("Case 3 : " + local_link)
                else:
                    foreign_urls.add(anchor)
                    #print("Case 4 : " + anchor)
                '''



            for i in local_urls:
                if not i in new_urls and not i in processed_urls:
                    new_urls.append(i)


        print()
        print("External URLs : ")
        for x in foreign_urls:
        	print(x)
        print("Downloaded : "+sizeof_fmt(int(bandwithUsage)))
        sys.exit()
 
    
    except KeyboardInterrupt:
        sys.exit()




def report_file(ofile, processed_urls, local_urls, foreign_urls, broken_urls):
    with open(ofile, 'w') as f:
        print(
            "--------------------------------------------------------------------", file=f)
        print("All found URLs:", file=f)
        for i in processed_urls:
            print(i, file=f)
        print(
            "--------------------------------------------------------------------", file=f)
        print("All local URLs:", file=f)
        for j in local_urls:
            print(j, file=f)
        print(
            "--------------------------------------------------------------------", file=f)
        print("All foreign URLs:", file=f)
        for x in foreign_urls:
            print(x, file=f)
        print("--------------------------------------------------------------------", file=f)
        print("All broken URL's:", file=f)
        for z in broken_urls:
            print(z, file=f)




def main(argv):
    # define the program description
    text = 'A Python program that crawls a website and recursively checks links to map all internal and external links. Written by Ahad Sheriff.'
    # initiate the parser with a description
    parser = argparse.ArgumentParser(description=text)
    parser.add_argument('--domain', '-d', required=True,
                        help='domain name of website you want to map. i.e. "https://scrapethissite.com"')
    parser.add_argument('--ofile', '-o',
                        help='define output file to save results of stdout. i.e. "test.txt"')
    parser.add_argument('--limit', '-l',
                        help='limit search to the given domain instead of the domain derived from the URL. i.e: "github.com"')
    parser.add_argument('--mute', '-m', action="store_true",
                        help='output only the URLs of pages within the domain that are not broken')
    parser.parse_args()

    # read arguments from the command line
    args = parser.parse_args()

    domain = args.domain
    ofile = args.ofile
    limit = args.limit
    mute = args.mute
    if domain:
        print("domain:", domain)

    print()
    crawler(domain, ofile, mute)






def signal_handler(sig,frame):
	print("Exited!")
	for x in new_urls:
		#y = x.replace("%5C",'')
		#print(y.replace("\'",''))
		print(x)
	for x in foreign_urls:
		print(x)
	print("Downloaded : "+sizeof_fmt(int(bandwithUsage)))
	sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT,signal_handler)
    main(sys.argv[1:])
    signal.pause()

