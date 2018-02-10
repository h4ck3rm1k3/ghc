#!/usr/bin/python
from __future__ import print_function
import sys
import re
import pprint
import os
import subprocess
from subprocess import Popen, PIPE

def start (out):
        out.write("""
{-# LANGUAGE CPP #-}
{-# LANGUAGE DeriveDataTypeable #-}
module TestFakeAst where
import FakeAstCore
""")

def prim_empty_array(l):
        #'Name: ghc-prim:GHC.Types.(EmptyArray){(w) d 6x'
        m = re.search("Name: ghc-prim:GHC.(\w+)\.(\(\w+\))\{\((\w+)\)\s+(\w+)\s+(\w+)",l)
        if m :
            g = m.group(1)
            g2 = m.group(2)
            g3 = m.group(3)
            g4 = m.group(4)
            g5 = m.group(5)
            g = ("(GHCPrimName \"{}\",\"{}\",\"{}\",\"{}\" )".format(g,g2,g3,g4,g5))
            g0 = m.group(0)
            l = l.replace(g0,g)
            return l
        else:
            return False

##################################        
relist = []
for x in [
                '([\-\/\.\w]+\.hs)',
                '([\-\/\.\w]+\.hsc)',
                '([\-\/\.\w]+\.hs-incl)',
                '([\-\/\.\w]+\.x)',
                '/tmp/([\-\/\.\w]+\.hspp)',
                '([\-\/\.\w]+\.hspp)']:

    for y in [
            '(\d+):([\d]+)',
            '(\d+):([\d]+\-[\d]+)',
            '\((\d+,\d+)\)\-\((\d+,\d+)\)',
            '(\d+):(\d+)',
            '(\d+):(\d+\-\d+)',
            '\((\d+,\d+)\)\-\((\d+,\d+)\)']:
        r = "({{\s*{reg}:{lines}(?:__NEWLINE__|\s)*}})".format(reg=x,lines=y)
        relist.append(re.compile(r))

        
##################################
re1list= []
for x in [
                '(\{(ModuleName): ([\.\w]+)\})',
                '(\{(abstract):([\.\w]+)\})',
                '(\{(OccName):\s+([^}]+)\})',
                '(\{(Fixity):\s+([^}]+)\})',
                '(\{(FastString):\s+\"([^"]*)\"\})',
                '((SourceText)\s+\"([^"]*)\")',
                #        '(\{(Name):([^}]+)\})',
                #        '(\{(Name): ([^\s]+))',
                '(\{(FastString)\"([^"]+)\"\})']:
        r = re.compile(x)
        re1list.append(r)


structlist= []
for x in [
        '(\{(Bag)([^}]+)\})',
        '(\{\((w)\)([^}]+)\})',
#        '(\{(Name):([^}]+)\})',
]:
    r = re.compile(x)
    structlist.append(r)  

re2list= []
for x in [
                '(\{(Name):(\w+)\})',
]:
    #print (" -- parse",x)
    r = re.compile(x)
    re2list.append(r)

re2alist= []
for x in [
                '(\{(Name): ([\w\,\-\(\)\.\[\]\:\s]+\{[\s\w:\(\)\.\[\]]+\})\})',
]:
    #print (" -- parse",x)
    r = re.compile(x)
    re2alist.append(r)

re3list= []
for x in [
        '(\[([^\]]+)\])',
]:
    #print (" -- parse",x)
    r = re.compile(x)
    re3list.append(r)


re1alist= []
for x in ['(\{(HsInt64Prim)([^}]+)\})']:
        r = re.compile(x)
        re1alist.append(r)
    
def process_src(l):

    for x in re1list:
        while re.search(x,l):
          for o in re.findall(x,l):
            v= o[2]
            v= v.replace('{',"OPENBRACE")
            v= v.replace('}',"CLOSEBRACE")
            new = " (Simple_{name} \"{value}\")".format(name=o[1].lower(),value=v)
            l = l.replace(o[0],new)
            
    for x in re1alist:
        while re.search(x,l):
          for o in re.findall(x,l):
            v= o[2]
            new = " (Simple_{name} {value})".format(name=o[1].lower(),value=v)
            l = l.replace(o[0],new)

    for x in relist:        
        for o in re.findall(x,l):
            new = " (checkSrc(source(\"{}\",\"{}\",\"{}\"))) ".format(o[1],o[2],o[3])
            #l = l.replace(o[0],new)
            l = l.replace(o[0],"") # strip out sources for now

            
    l = l.replace('{ <no location info> }','(NoLocationInfo)')
    ## pattern includes then name of the object to create and the one value
    for x in re2alist:
        while re.search(x,l):
          for o in re.findall(x,l):
            new = " (Name2_{name} \"{value}\")".format(name=o[1].lower(),value=o[2])
            l = l.replace(o[0],new)


    for x in structlist:
        while re.search(x,l):
          for o in re.findall(x,l):
            new = " (Struct_{name} {value})".format(name=o[1].lower(),value=o[2])
            l = l.replace(o[0],new)

    for x in re2list:
        while re.search(x,l):
          for o in re.findall(x,l):
            new = " (Name_{name} \"{value}\")".format(name=o[1].lower(),value=o[2])
            l = l.replace(o[0],new)
            

    #for x in re3list:
    #    for o in re.findall(x,l):
            #new = " (SomeArray [{value}])".format(value=o[1])
    #        l = l.replace(o[0],new)

    return l

def pre(l):


    l2 = prim_empty_array(l)
    if l2 is not False:
        return l2

    ####
    m = re.search("\{Name: ghc-prim:GHC.(\w+)\.(..)\{\((\w+)\)\s+(\w+)\s+(\w+)\}\}",l)
    if m :
        g = m.group(1)
        g2 = m.group(2)
        g3 = m.group(3)
        g4 = m.group(4)
        g5 = m.group(5)
        g = ("(GHCPrimName(\"{}\",\"{}\",\"{}\",\"{}\"))".format(g,g2,g3,g4,g5))
        g0 = m.group(0)
        l = l.replace(g0,g)
        return l 
    
def cleanup(l):
    l = l.replace("(Nothing)","(ANothing)")
    l = l.replace("(Just","(AJust")
    #l = l.replace("[]","(EmptyArray)")

#    l = l.replace("]","]))")
#    if '{' in l :
#        print "Check", l
#    l = l.replace("(","\n    (")
    return l

def process (fn):
    if '.#' in fn:
            return 
    f = open (fn)
    newname = fn + ".asths"
    if os.path.exists(newname):
            return
    f2 = open(newname,"w")
    start(f2)
    #print ("-- Processing ", fn)
    fname= fn.replace("/","_").replace(".","_").replace("-","_")
    
    text = ""
    for l in f.readlines():
        l= l.strip()
        l = l.replace("HsInt{64}Prim","HsInt64Prim")
        l = l.replace("\\\\","TWOBACKSLASH")
        l = l.replace("\\\\\\n","NEWLINE1")
        l = l.replace("\\\\n","NEWLINE2")
        l = l.replace("\\\"","DOUBLEQUOTE")
        l = l.replace("'{'","SINGLE_QUOTEDOPEN_BRACE")
        l = l.replace("'}'","SINGLE_QUOTEDCLOSE_BRACE")
        if l == '==================== Parser AST ====================':
            continue        
        if l.endswith('UTC'):
            continue    
        text = text + str(l) + "__NEWLINE__"
    text = process_src(text)
    text = cleanup(text)
    text = text.replace("__NEWLINE__","\n    ")
    #text = text.replace("__DOUBLEQUOTE__","\"",)
    f2.write ("f{fname} x = {text}".format(fname=fname, text=text))
    f2.close()
    #print ("NEW",newname)
    cmd = ['/home/mdupont/.stack/snapshots/x86_64-linux-nopie/lts-9.5/8.0.2/bin/hindent', newname]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    lines = text.split("\n")
    print ("NEW->",newname, x)
    
    if p.returncode != 0:
            os.rename(newname,newname + "err")
            print ("ERR->",newname+ "err", x)
            m = re.match(r'hindent: ([\w\.\/\-]+).asths: (\d+): (\d+): (.+)',stderr)
            line = int(m.group(2))
            print ("line", line)
            print (stderr)
            for l in range(line-10,line + 3):
                    print("Lines",l,lines[l])

            exit (x)
import sys

def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)
        
for fn in sys.argv[1:]:
    eprint ("#"+ fn)
    process (fn)
