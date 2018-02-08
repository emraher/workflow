#!/usr/bin/env python
# coding=utf-8
# pdfmeat - 
# Copyright (C) David Aumueller
# 2013-01-11: copy/paste into single file from last version

import urllib
import urllib2
import re
import os
import logging
import argparse
import translitcodec
import anyjson
import hashlib
import subdist
import glob
import cookielib
import subprocess
import datetime

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=os.path.join(os.path.expanduser('~'), '/tmp/.pdfmeatfile.log'))
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=os.path.join(os.path.expanduser('~'), '/tmp/.pdfmeatfile.log'))

DEMO = False
FAILTOBROWSER = True

GS_URL = 'http://scholar.google.com/scholar?%s' #num=100&
GA_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s'
GA_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s&key=ABQIAAAAW-Sxm-UvV18CEcuvC-8R6hQDvCfPwbxk_Ht9GuQPZOcoDbrteRRcJgN0OK0E8FyqFAKiNYBEeIkGxw'

GS_TRIES=3
GA_TRIES=2

REGS = dict()
REGS['none'] = "did not match any articles|Sorry, no information is available for"
REGS['one'] = 'Showing web page information for'
REGS['some'] = ">([0-9,]+) result"
REGS['sorry'] = "We're sorry|please type the characters"

class WebScrapingError(Exception):
    pass

class PdfMeatFile:

    def __init__(self, filename = None, doi=None, title=None):
        self.filename = filename
        self.doi = doi
        self.title = title
        
        self.queryLog = []
        self.queryNo = 0
        self.gs_hits = None
        self.bibtex = None

        self.pdftext = None
        self.gs_entry = dict()

        self.pdfhead = None
        self.abstract = None
        self.mailhosts = None

        self.oldfilename = self.filename #os.path.basename(self.filename)
        self.newfilename = self.oldfilename

        self.md5sum = None

    def __repr__(self):
        if self.bibtex is not None and len(self.bibtex) > 0:
            return self.bibtex
        str = "PDFMeat entry for %s\n" % self.filename
        try:
            str += "%s (%s) %s\n" % (self.gs_entry['authors'], self.gs_entry['year'], self.gs_entry['title'])
        except (KeyError):
            try:
                str += "%s: %s\n" % (self.gs_entry['authors'], self.gs_entry['title'])
            except (KeyError):
                pass
        return str

    def pdfToText(self, options = None):
       
        commando_pdf2txt = ["pdftotext", '-q', '-f', '1', '-l', '10']
        if options is not None:
            commando_pdf2txt.extend(options)
        commando_pdf2txt.append(self.filename)            
        commando_pdf2txt.append('-')
        proc = subprocess.Popen(commando_pdf2txt, stdout=subprocess.PIPE)
        c_txt = proc.communicate()[0]

        if c_txt is None:
            logging.error("pdftotext: empty")

        if self.pdftext is None: # in case of multiple pdftotext calls eg in guess title with layout/first page only
            self.pdftext = c_txt

        return c_txt #[0:9999]
    
    def getWebdata(self, url):
        useragent = 'Mozilla/5.0 (X11; Linux x86_64; rv:6.0) Gecko/20100101 Firefox/6.0'
        referer = 'http://scholar.google.com'
    
        cj = self.firefox_cookie()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('User-agent', useragent), ('Referer', referer)]
        html = opener.open(url).read() # use current firefox cookies to access url
        
        html = html.decode('utf8')
        #html = html.encode('translit/long')        
        
        #if re.search(r"We're sorry", html) or re.search("please type the characters", html):
        if re.search(REGS['sorry'], html):
            logging.critical("scholar captcha")
            logging.debug(html)
            import webbrowser
            webbrowser.get().open_new_tab(url)
            os.remove('/tmp/.pdfmeat_cookies.sqlite')
            os.remove('/tmp/.pdfmeat_cookies.txt')
        
        if FAILTOBROWSER is True and re.search(REGS['none'], html):
            import webbrowser
            webbrowser.get().open_new_tab(url)
        
        if DEMO is True:
            import webbrowser
            webbrowser.get().open_new_tab(url)
    
        return html
    
    # adapted from http://code.google.com/p/webscraping/source/browse/common.py
    def firefox_cookie(self, filename=None, tmp_sqlite_file='/tmp/.pdfmeat_cookies.sqlite', tmp_cookie_file='/tmp/.pdfmeat_cookies.txt'):
        """Create a cookie jar from this FireFox 3 sqlite cookie database
    
        >>> cj = firefox_cookie()
        >>> opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        >>> url = 'http://code.google.com/p/webscraping'
        >>> html = opener.open(url).read()
        """
    
        if not os.path.exists(tmp_cookie_file):
            
            if filename is None:
                try:
                    filename = glob.glob(os.path.expanduser('~/Library/Application Support/Firefox/Profiles/*.default/cookies.sqlite'))[0]
                    
                except IndexError:
                    raise WebScrapingError('Cannot find firefox cookie database')
    
            # copy firefox cookie file locally to avoid locking problems
            import shutil
            shutil.copyfile(filename, tmp_sqlite_file)
            import sqlite3             
            con = sqlite3.connect(tmp_sqlite_file)
            cur = con.cursor()
            cur.execute('select host, path, isSecure, expiry, name, value from moz_cookies')
    
            # create standard cookies file that can be interpreted by cookie jar 
            fp = open(tmp_cookie_file, 'w')
            fp.write('# Netscape HTTP Cookie File\n')
            fp.write('# http://www.netscape.com/newsref/std/cookie_spec.html\n')
            fp.write('# This is a generated file!  Do not edit.\n')
            ftstr = ['FALSE', 'TRUE']
            for item in cur.fetchall():
                row = '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (item[0], ftstr[item[0].startswith('.')], item[1], ftstr[item[2]], item[3], item[4], item[5])
                fp.write(row)
            fp.close()
    
        cookie_jar = cookielib.MozillaCookieJar()
        cookie_jar.load(tmp_cookie_file)
        return cookie_jar

    def unescape(self, text):
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    import htmlentitydefs                    
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is
        return re.sub("&#?\w+;", fixup, text)

    def normalizeTitle(self, t):
        t = self.unescape(t)
        # xcmd = "echo '%s' | iconv -t US-ASCII//translit" % (txt)
        try:
            t = t.decode('utf8')
            t = t.encode('translit/long')
        except:
            pass

        t = t.lower()
        t = re.sub('[^a-z0-9]', '', t)
        return t


    def matchScholarEntries(self, p_head, entries):
        pn = self.normalizeTitle(p_head)
        eNo = 0
        for e in entries:
            eNo+=1
            t = e['title']
            tn = self.normalizeTitle(t)
            # test whether title contained in pdftext
            logging.debug("normalized title to match: %s" % tn)
            self.queryLog.append("normalized title to match: %s" % tn)
            logging.debug("p_head: %s" % pn)
            self.queryLog.append("p_head: %s" % pn)
            
            if tn in pn:
                logging.debug("query %s: matching hit was %d of %d" % (self.queryNo, eNo, len(entries)))
                return e
            else:
                logging.debug("no substring found, going fuzzy")
                #dist = self.fuzzy_substring(tn, pn)
                dist = subdist.substring(unicode(tn), unicode(pn))
                logging.debug("fuzzy: %d off" % dist)
                if float(dist)/len(tn) < 0.1: # up to 10 percent off ok?
                    logging.debug("fuzzy: accepting %f off" % ( float(dist)/len(tn) )) 
                    return e
    
    def getScholarQuery(self, p, windex=0):
        if self.doi:
            return self.doi
        if self.title:
            return 'intitle:"'+self.title+'"'
            
        stopwords = ['I','a','about','an','are','as','at','be','by','com','for','from','how','in','is','it','of','on','or','that','the','this','to','was','what','when','where','who','will','with','the','www']
        q = ''
        p_az = p.lower()
        # latex diacritics often as in: Inst. f" r Inf.
        p_az = re.sub('[^a-z0-9"]', " ", p_az)
        p_az = re.sub(' [^ ]+" [^ ]+ ', " ", p_az)
        p_az = re.sub('" ', " ", p_az)
        p_az = re.sub("[a-z]+[0-9] ", " ", p_az) #autname1 autname2 get rid of (or keep as autname autname ?)
        #p_az = re.sub(" +", " ", p_az)
        words = re.split(" +", p_az)
        words2 = []
        for w in words:
            if len(w) > 1 and re.search("[a-z]", w) and (w not in stopwords) and re.search("[aeiou].*[aeiou]", w) and (w not in words2):
                words2.append(w)
        for w in words2[windex:windex + 99]:
            q = q + w + ' '
            q = q[0:255]
            q = re.sub("[^ ]+$", "", q) # strip last unfinished word
        self.queryNo += 1
        self.queryLog.append("query %s: %s" % (str(self.queryNo), q))
        logging.debug("query %s: %s" % (str(self.queryNo), q))
        return q


    def parse_scholar_hit_count(self, s):
        if re.search(REGS['none'], s):
            return 0
        p = REGS['some']
        m = re.search(p, s)
        if m is not None and m.group(1) is not None:
            return re.sub(",", "", m.group(1))
        if re.search(REGS['one'], s):
            return 1

    
    def md5file(self, block_size=2**20):
        fh = open(self.filename)
        md5 = hashlib.md5()
        while True:
            data = fh.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    
    def setFragments(self):
        if self.pdftext is None:
            return
        p = self.pdftext
        p_head = p[0:999] # title in first x chars?
        m = re.search(r"(.*?)((abstract)|(introduction))\n", p_head, re.I|re.S)
        if m is not None and m.group(1) is not None:
            p_head = m.group(1)

        self.pdfhead = p_head
        abstract = None
        m = re.search(r'(?:(?i)Abstract)[:\. \n]+([A-Z].{99,3333})(\n[0-9 \.]*(?:(?i)Introduction))', p, re.S)
        if m is not None:
            abstract = m.group(1).strip(' 12.') # strip space, 1. intro  -- as above regex with {99,3333} is greedy
            self.abstract = abstract
            if abstract is not None and len(abstract) > 1337: #### was: 60*6: #roughly 60 chars by 6 lines is too long for an abstract
                self.abstract = re.sub(r'[^\.]+$',' [abriged]', self.abstract[:1234])
            import textwrap
            self.abstract = '\n'.join(textwrap.wrap(' '.join(self.abstract.split(r'[\r\n]+'))))

        doi = None
        # DOI 10.1007/s00778-005-0158-4
        m = re.search(r'DOI (\d\d\.\d\d\d\d/\w[^ \n]+)', p, re.I | re.S)
        if m is not None:
            doi = m.group(1)
            self.doi = doi
            
    def processFile(self):
        logging.info("processfile %s" % self.filename)
        
        if self.pdftext is None and self.filename is not None:
            #p = self.pdfToText(self.filename, " -enc ASCII7") #self.pdftext
            logging.debug("processfile: pdftotext")            
            p = self.pdfToText(['-enc','UTF-8'])
            logging.debug("processfile: pdftotext.")            
        else:
            p = self.pdftext
            logging.debug("processfile: loading text.")            

        try:
            p = unicode(p.decode('utf8').encode('translit/long'))
            logging.debug('processfile encoding 1')
            #logging.debug(p[:444])
        except:
            try:
                #p = unidecode.unidecode(p)
                p = (p.decode('utf8'))
                logging.debug('processfile encoding 2')
            except:
                logging.debug('processfile encoding 3')
                pass
        self.pdftext = p

        if p is None and (self.doi is not None or self.title is not None):
            if self.title is not None:
                p = self.title
            if self.doi is not None:
                p = self.doi

        if self.filename is not None:
            self.md5sum = self.md5file()
            
        #p_utf = self.pdfToText(f, "-enc UTF-8")
      
        self.setFragments() # self.pdfhead, self.abstract
        logging.debug("processfile: setting fragments.")
        
        gs_tryNo = 0 #110
        ga_tryNo = 0 #110
        querywordsoffset = 64
        e = None
        while (e is None and (gs_tryNo < GS_TRIES or ga_tryNo < GA_TRIES)):
            if gs_tryNo < GS_TRIES:
                q = self.getScholarQuery(p, gs_tryNo * querywordsoffset)
                gs_tryNo += 1
                if len(q) < 3:
                    logging.debug("skipping too short query: %s" % q)
                    self.queryLog.append("skipping too short query: %s" % q)
                    continue
            elif ga_tryNo < GA_TRIES:
                ga_q = self.getScholarQuery(p, ga_tryNo * querywordsoffset)
                ga_tryNo += 1
                ga_query = urllib.urlencode({'q' : ga_q}) #.encode('utf8')
                url = GA_URL % ( ga_query )
                resultset = urllib2.urlopen(url).read()
                if resultset is not None:
                    resjs = anyjson.deserialize(resultset) #load()
                    logging.debug(resultset)
                    
                    if resjs is not None:
                        if type(resjs) is dict and len(resjs['responseData']['results'])>0:
                            result = resjs['responseData']['results']
                            q = urllib.unquote(result[0]['url'])
                            logging.info("web search result: %s" % q)
                            self.queryLog.append("web search result: %s" % q)
                        else:
                            logging.info("web search: no result")
                            self.queryLog.append("web search: no result")
                            continue
            
            query = urllib.urlencode({'q' : q}) #.encode('utf8')
            gsu = GS_URL % (query)
            gsc = self.getWebdata(gsu)
            gs_hits = self.parse_scholar_hit_count(gsc)

            logging.debug("result %d+%d hits: %s" % (gs_tryNo, ga_tryNo, str(gs_hits)))
            self.queryLog.append("result %d+%d hits: %s" % (gs_tryNo, ga_tryNo, str(gs_hits)))
            self.gs_hits = gs_hits
            #TODO: if gs_hits > threshold: be more specific. else: be less specific -- aka adaptive querying

            if self.gs_hits > 0:
                entries = self.parseScholar(gsc)
                self.queryLog.append("retrieved %d of %s entries" % (len(entries), self.gs_hits))

                if self.filename is None:
                    e = entries[0]
                else:
                    e = self.matchScholarEntries(self.pdfhead, entries)
                    if e is None:
                        logging.debug("result %s: no match in %d entries (of %s)" % (self.queryNo, len(entries), self.gs_hits))
                        self.queryLog.append("no match in %d entries (of %s)" % (len(entries), self.gs_hits))
        
        if e is None:
            logging.info("%s: tried %d+%d queries, no (matching) result. giving up" % (self.filename, GS_TRIES, GA_TRIES) )
        else:
            try:
                self.gs_entry = e
                logging.info("match: %s: %s" % (e['authors'], e['title']))
            except:
                logging.warn("%s: basic info (authors, title, year) incomplete" % self.filename)
                print "pdfmeat: have you set in Firefox on page scholar.google.COM settings to show BibTeX (or scholar html changed, parser broken, inform david)"
            try:
                if e['importlink'] is not None:
                    importlink = re.sub('&amp;', '&', e['importlink'])
                    _b = self.getWebdata(importlink)
                    _b = _b.replace(r'{\\"', r'{\"')
                    self.bibtex = _b
                    if self.filename is not None:
                        self._append_bibtex('file={file://' + os.path.realpath(self.newfilename) + ':pdf}')
                        self._append_bibtex('md5sum={' + self.md5sum + '}')
                    try:
                        self._append_bibtex('url={' + e['url'] + '}')
                    except (KeyError, TypeError): # e['url'] can be None?
                        pass # cannot be
                    try:        
                        self._append_bibtex('htmllink={' + e['htmllink'] + '}')
                    except (KeyError, TypeError):
                        pass
                    try:
                        self._append_bibtex('citations={' + e['citations'] + '}')
                        self._append_bibtex('citedbyid={' + e['citedbyid'] + '}')                
                    except (KeyError, TypeError):
                        pass
                    try:
                        self._append_bibtex('doi={' + self.doi + '}')
                    except (KeyError, TypeError):
                        pass
        
                    if self.abstract is not None:
                        self._append_bibtex("abstract={" + self.abstract + "}")
                    
                    if self.mailhosts is not None:
                        self._append_bibtex("mailhosts={" + "; ".join(self.mailhosts) + "}")
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    if self.filename is not None:
                        self._append_bibtex("pdfmeat={timestamp: %s; queries: %d; inode: %d}" % (timestamp, self.queryNo, os.stat(self.newfilename).st_ino))
                    else:
                        self._append_bibtex("pdfmeat={timestamp: %s; queries: %d}" % (timestamp, self.queryNo))

            except (KeyError):
                logging.warning("cannot retrieve bibtex")
        return self.bibtex
        
    def _append_bibtex(self, keyvalue):
        keyvalue = r",\n  " + keyvalue  
        self.bibtex = re.sub(r"}\n", r"}" + keyvalue + r"\n", self.bibtex, 1)
        return self.bibtex

    def parseScholar(self, content):
      pa = re.compile('(<h3 class="gs_rt">(.*?)</div></div>)', re.DOTALL)
      myItems = []
      for m in re.finditer(pa, content):
        a = m.group(1)
        a = re.sub('</?b>', '', a)
        a = re.sub('<font .*?>\[[^\]]+\]</font>', '', a)
        a = re.sub('&nbsp;|<br>', '', a)
        a = re.sub('&hellip;', '...', a)
        a = re.sub('&amp;', '&', a) # 2010-02-22
        pt = re.compile('<h3.*?>.*?(?:<span .*?</span> )?((<a href="([^"]+)"[^>]*>)?([^<]+)(</a>)?)</h3>')
        myItem = {}
        m1 = re.search(pt, a)
        if m1 != None:    
          myItem['url'] = m1.group(3)
          myItem['title'] = m1.group(4) #.strip()

          pc = re.compile('>Cited by ([0-9]+)<')
          m2 = re.search(pc, a)
          if m2 != None:
            myItem['citations'] = m2.group(1)
          pcl = re.compile(' href="/scholar\?([^"]*cites=([0-9]+))')
          m_pcl = re.search(pcl, a)
          if m_pcl != None:
            myItem['citedbyid'] = m_pcl.group(2)
          authorvenueyear = ''
          pa = re.compile('<div class="gs_a">(.*?)</div>')
          m3 = re.search(pa, a)
          if m3 != None:
            authorvenueyear = m3.group(1)
            pavy = re.compile('^(.*?)( - ((?:(.*?), ((?:19|20)[0-9][0-9])|(((?:19|20)[0-9][0-9])|(.*?)))))? - (.*)$')
            m4 = re.search(pavy, authorvenueyear)
            if m4 != None:
              myItem['authors'] = re.sub('<[^<]+?>', '', m4.group(1))
              if m4.group(4) != None:
                myItem['venue'] = m4.group(4)
              if m4.group(5) != None and re.match('(19|20)[0-9][0-9]', m4.group(5)):
                myItem['year'] = m4.group(5)
              if m4.group(6) != None and re.match('(19|20)[0-9][0-9]', m4.group(6)):
                myItem['year'] = m4.group(6)            
              if m4.group(7) != None and re.match('(19|20)[0-9][0-9]', m4.group(7)):
                myItem['year'] = m4.group(7)
              if m4.group(8) != None:
                myItem['venue'] = m4.group(8)
              if m4.group(9) != None:
                myItem['publisher'] = m4.group(9)
          pca = re.compile('q=cache:([^+"]+)[^"]*">View as HTML</a>')
          m_pca = re.search(pca, a)
          if m_pca != None:
            myItem['htmllink'] = 'http://scholar.google.com/scholar?q=cache:' + m_pca.group(1)
          pim = re.compile('href="/scholar\.([^"]+)".*?>Import into .*?</a>')
          m_pim = re.search(pim, a)
          if m_pim != None:
            myItem['importlink'] = 'http://scholar.google.com/scholar.' + m_pim.group(1)
          # querylink = "http://scholar.google.com/scholar?q=" + urllib.quote("intitle:\"" + title + "\"")
          myItems.append(myItem)    
      return myItems

    def _rename_file(self, filename, name_new = None):
        target_dir = os.path.dirname(os.path.realpath(filename))
        newfilename = target_dir + '/' + name_new + '.pdf'
        if os.path.realpath(filename) != newfilename:
            if not os.path.isfile(newfilename):
                try:
                    os.rename(filename, newfilename)
                    logging.info("renaming: %s to %s" % (filename, newfilename))
                except:
                    logging.error("%s: renaming to %s failed" % (filename, newfilename))
            else:
                logging.error("%s: not renaming to %s, file already exists" % (filename, newfilename))
        else:
            logging.info("%s: already accordingly named" % filename)
        return newfilename

    def _extract_bibkey(self, bibstr):
        bibkey = None
        p_bibkey = re.compile("@[a-z]+{(.*?),") # @article{bibkey,
        bibstr = bibstr.encode('translit/long') # umlauts
        m_bibkey = re.search(p_bibkey, bibstr)
        if m_bibkey is not None:
            bibkey = m_bibkey.group(1)
        return bibkey

def main():
    
    parser = argparse.ArgumentParser(description='PDF Metadata acquisition tool.', argument_default=argparse.SUPPRESS)
    parser.add_argument('--PDF', default=None, help='pdf file in question')
    parser.add_argument('--rename', action='store_true', default=False, help='rename files after successfully retrieving metadata')
    parser.add_argument('--inject',  action='store_true', default=False, help='inject metadata into PDF (requires according Perl script)')
    parser.add_argument('--title', default=None, help="Title of document")
    parser.add_argument('--doi', default=None, help="DOI of document")
    filename, title, doi = None,None,None

    args = parser.parse_args()
    if args.PDF:
        filename = args.PDF
        if not os.path.isfile(filename):
            parser.error('file not found: ' + filename)
            parser.exit()

    pf = PdfMeatFile(filename=filename, title=args.title, doi=args.doi)
    pf.processFile()
    
    if pf.bibtex is not None and args.inject is True:
        proc = subprocess.Popen('./bibtex2pdfmeta.pl -', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE )
        out,err = proc.communicate((pf.bibtex).encode('translit/long'))
        
    if pf.bibtex is not None and args.rename is True:
        bibkey = pf._extract_bibkey(pf.bibtex)
        newfn = pf._rename_file(filename, bibkey)
        pf.bibtex.replace(filename, newfn)
    
    print pf.bibtex
    parser.exit()

if __name__ == "__main__": 
    main()
