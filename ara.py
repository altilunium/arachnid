"""
    A Python program that crawls a website and recursively checks links to map all internal and external links
"""

from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urllib.parse import urlsplit
from urllib.parse import urlparse
from urllib.parse import urljoin
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
import pickle
from requests_html import HTMLSession

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
bandwithUsage = 0


def crawler(domain, ofile, mute, cont):
    global new_urls,bandwithUsage,foreign_urls,processed_urls,local_urls,url
    try:
        domain_schema = urlparse(domain).scheme
        if cont:
            print("Continuing last session")
            with open("last_crawl","rb") as f:
                new_urls = pickle.load(f)
                print("Queue : " + str(len(new_urls)))
                foreign_urls = pickle.load(f)
                processed_urls = pickle.load(f)
                print("Processed : " +str(len(processed_urls)))
                local_urls = pickle.load(f)
                print("Local URLs : " +str(len(local_urls)))
                url = pickle.load(f)
                print("Last URL : "+ str(url))
                new_urls.append(url)
        else:
            new_urls = deque([domain])
            processed_urls = set()
            local_urls = set()
            foreign_urls = set()
            broken_urls = set()


        while len(new_urls):

            url = new_urls.popleft()
            processed_urls.add(url)
            url_scheme = urlparse(url).scheme
            if url_scheme == '':
                url = domain_schema +"://" + url


            try:
                response = requests.head(url)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):
                broken_urls.add(url)
                continue


            if 'content-type' in response.headers:
                content_type = response.headers['content-type']
                #print("Content Type : "+ content_type)
                if not 'text/html' in content_type:
                    print("Not html. Skipping")
                    print("Content Type : "+ content_type)
                    continue

       
            actualPayload = bytearray()
            try:
                response = requests.get(url)
                actualPayload = response.text
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema):                
                broken_urls.add(url)
                continue

            soup = BeautifulSoup(actualPayload, "lxml")
            title = soup.find('title')
            

            input_base = urlparse(domain).netloc
            base = urlparse(url).netloc
            path = urlparse(url).path
            path = path.split("/")
            path = filter(lambda x:x!='',path)
            path = list(path)


            print(str(len(new_urls))+" "+url,end='\r')

            dontprint = False
            
            try:
                if (path[0] == 'tag') or (path[0] == 'category') or (path[0] == 'author') or (path[0] == 'search') or(path[0] == 'page'):
                    dontprint = True
                elif (len(path) == 1) and path[0].isnumeric():
                    dontprint = True
                elif len(path) == 2:
                    if path[0].isnumeric() and path[1].isnumeric():
                        dontprint = True
                    else:
                        dontprint = False
                elif len(path) == 3:
                    if path[0].isnumeric() and path[1].isnumeric() and path[2].isnumeric():
                        dontprint = True
                    elif path[0].isnumeric() and path[1].isnumeric() and path[2] == 'page':
                        dontprint = True
                    else:
                    	dontprint = False
                elif len(path) == 5:
                    if path[0].isnumeric() and path[1].isnumeric() and path[2].isnumeric() and not path[3].isnumeric() and path[4] != '':
                        dontprint = True
                    else:
                        dontprint = False
                else:
                    dontprint = False
            except IndexError as e:
                dontprint = False
            

            if not dontprint:
                sys.stdout.write("\033[K")          
                if title is not None:
                    print()
                    print(title.string)
                    print(url)
                    
            else:
                sys.stdout.write("\033[K")
                #print("Discarded : "+url)



            



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
                    if anchor_base == '':
                        if anchor.startswith("/"):
                            fullurl = domain_schema+"://"+input_base+anchor
                            #print("LU1 : "+fullurl)
                            local_urls.add(fullurl)
                        elif anchor.startswith("./") or anchor.startswith("../"):
                            fullurl = urljoin(url,anchor)
                            #print("LU2 : "+fullurl)
                            local_urls.add(fullurl)
                        elif anchor.startswith("mailto:"):
                            continue
                        else:
                            fullurl = domain_schema+"://"+input_base+"/"+anchor
                            #print("LU3 : "+fullurl)
                            local_urls.add(fullurl)
                    elif anchor.startswith("//"):
                            fullurl = url_scheme +":"+ anchor
                            anchor_base = urlparse(fullurl).netloc
                            if (anchor_base != input_base):
                                foreign_urls.add(anchor)
                            else:
                                #print("LU4 : "+fullurl)
                                local_urls.add(anchor)
                            
                    else:
                        foreign_urls.add(anchor)
                else:
                    
                    local_urls.add(anchor)


            for i in local_urls:
                if not i in new_urls and not i in processed_urls:
                    #print("Add : "+i)
                    if "https://" in i:
                        nya = i.replace("https://","http://")
                        if nya not in new_urls:
                            new_urls.append(i)
                        else:
                            continue
                    elif "http://" in i:
                        nya = i.replace("http://","https://")
                        if nya not in new_urls:
                            new_urls.append(i)
                    else:
                        new_urls.append(i)


        print()
        
        print("External URLs : ")

        fu_list = []
        for x in foreign_urls:
        	#print(x)
            fu_list.append(x)
        fu_list.sort()
        for x in fu_list:
            print(x)
        #print("Downloaded : "+sizeof_fmt(int(bandwithUsage)))
        
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
    parser.add_argument('--cont','-c',action="store_true")
    parser.parse_args()

    # read arguments from the command line
    args = parser.parse_args()

    domain = args.domain
    ofile = args.ofile
    limit = args.limit
    mute = args.mute
    cont = args.cont
    if domain:
        print("domain:", domain)

    print()
    crawler(domain, ofile, mute, cont)






def signal_handler(sig,frame):
    #global new_urls,bandwithUsage,foreign_urls,processed_urls,local_urls,url
    print("Exited!")
    '''
    for x in new_urls:
		#y = x.replace("%5C",'')
		#print(y.replace("\'",''))
		print(x)
	for x in foreign_urls:
		print(x)
    '''
	#print("Downloaded : "+sizeof_fmt(int(bandwithUsage)))
    with open("last_crawl","wb") as f:
        pickle.dump(new_urls,f)
        pickle.dump(foreign_urls,f)
        pickle.dump(processed_urls,f)
        pickle.dump(local_urls,f)
        pickle.dump(url,f)

    print("External URLs : ")
    for x in foreign_urls:
        print(x)
    print("Captured URL : ")
    for x in new_urls:
        print(x)

    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT,signal_handler)
    main(sys.argv[1:])
    signal.pause()

