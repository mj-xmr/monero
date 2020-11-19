#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""

"""

import os
import argparse
import subprocess
import shutil
import ntpath
import time
import multiprocessing

from matplotlib import pyplot as plt
from tabulate import tabulate


dirOut = 'out/'
dirImgRel = 'img/'
dirDataRel = 'data/'
dirImg = dirOut + dirImgRel
dirData = dirOut + dirDataRel
TAG_PLOT = '-plot'

hyperlink_format = '<a href="{link}">{text}</a>'

class Tool:
    def __init__(self, name, alias, artifacts=[]):
        self.name = name
        self.alias = alias
        if isinstance(artifacts, str):
            self.artifacts = [artifacts]
        else:
            self.artifacts = artifacts
        
    def GetKPIs(self, res):
        return res
    
    def GetCell(self, git_hash, kpis):
        cell = ''
        for iart, artifact in enumerate(self.artifacts):
            link = GetFilenameArtifactRelative(git_hash, artifact)
            link_txt = "-{}-".format(iart+1)
            cell += hyperlink_format.format(link=link, text=link_txt) + " "
        cell += kpis
            
        return cell
        
    def _getKPIs(self, res):
        raise NotImplementedError("_getKPIs() for {}".format(self.name))
        
        
class LOC(Tool):
    def __init__(self):
        super().__init__('loc.sh', 'loc')
        
class Files(Tool):
    def __init__(self):
        super().__init__('files.sh', 'files', 
                         ['build/files.txt'
                         ,'build/files2.txt'])
    
class Failing(Tool):
    def __init__(self):
        super().__init__('failing.sh', 'failing')
        
class CBA(Tool):
    def __init__(self):
        super().__init__('clang-build-time-analyzer-run.sh', 'cbta', 
                         ['build/clang-build-analyser/cba-result.txt'
                         ,'build/clang-build-analyser/cba-trace.txt.gz'])
        

class Tidy(Tool):
    def __init__(self):
        super().__init__('clang-tidy-run.sh', 'tidy', 
                             ['build/clang-tidy-C/clang-tidy-result-C.txt.gz'
                             ,'build/clang-tidy-CXX/clang-tidy-result-CXX.txt.gz']
                        )              
class IWYU(Tool):
    def __init__(self):
        super().__init__('clang-include-what-you-use-run.sh', 'iwyu', 
                         ['build/clang-iwyu/iwyu-result.txt.gz'])
        
    
class Checkout:
    def __init__(self, git_hash, date, tool_results):
        self.git_hash = git_hash
        self.date = date
        self.tool_results = tool_results

tools = [
        LOC()       # Light
    #,   CBA()       # Heavy
    #,   IWYU()
    #,   Tidy()
    ,   Files()     # Light
    ,   Failing()   # Test failing
    #,   Valgrind()  # TODO
    ]
   

def GetDirThis():
    return os.path.dirname(os.path.realpath(__file__))

def GetParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--threads', default=1, type=int, help="Number of threads. 0 means use all cores.")
    parser.add_argument('-n', '--num-back', default=5, type=int, help="How many checkouts from head")
    parser.add_argument('-c', '--disable-cache', default=False, action='store_true', help="Disable cache")

    return parser

def GetResultsForTool(tool):
    pathTool = os.path.join(GetDirThis(), tool.name)
    result = subprocess.run([pathTool], stdout=subprocess.PIPE)
    
    if result.returncode != 0:
        raise ValueError("Return code {} for tool {}".format(result.returncode, tool.name))
    
    resStr = result.stdout.decode('utf-8')
    
    for artifact in tool.artifacts:
        if not os.path.isfile(artifact):
            raise ValueError("No artifact {} for tool {}".format(artifact, tool.name))
    
    # Assumption: The KPIs are the last emited set of space divided numbers
    kpis = resStr.strip().split('\n')[-1]
    
    return kpis

def CreateDirIfNotExists(filePath):
    dir_dst = os.path.dirname(os.path.realpath(filePath))
    os.makedirs(dir_dst, exist_ok=True)

def GetResultsForToolCached(args, git_hash, tool):
    print(tool.name)
    frep = GetFilenameTool(git_hash, tool)
    
    try:
        use_cache = not args.disable_cache
        if use_cache and os.path.isfile(frep):
            print("Using cached", tool.name)
            with open(frep) as fin:
                res = fin.readlines()[0]
                
            for artifact in tool.artifacts:
                dst = GetFilenameArtifact(git_hash, artifact)
                if not os.path.isfile(dst):
                    res = '-3'
                    print("Target artifact", dst, "not available! Error code", res)
                    
        else:  
            res = GetResultsForTool(tool)
            
            for artifact in tool.artifacts:
                if os.path.isfile(artifact):
                    dst = GetFilenameArtifact(git_hash, artifact)
                    CreateDirIfNotExists(dst)
                    #print("dst", dst)
                    shutil.move(artifact, dst)
                    #shutil.copy(artifact, dst)
                else:
                    res = '-2'
                    print("Source artifact", artifact, "not available! Error code", res)
                    
    except:
        res = '-1'
        print("Error executing tool", tool.name, "Error code", res)
        # TODO: Better error handling here
    finally:
        CreateDirIfNotExists(frep)
        with open(frep, 'w') as fin:
            fin.writelines([res])
        
        return res 

def LoopIter(args, git_hash, tool):
    res = GetResultsForToolCached(args, git_hash, tool)
    kpis = tool.GetKPIs(res)
    return kpis

def GetResultsForCheckout(args, git_hash):
    tool_results = []
    
    if args.threads == 1:
        # No parallelism requested (important for debugging!)
        for tool in tools:
            kpis = LoopIter(args, git_hash, tool)
            tool_results.append(kpis)
            
    else:
        if args.threads <= 0:
            # Use all detected cores
            num_threads = multiprocessing.cpu_count()
        else:
            # Use the selected number of cores
            num_threads = args.threads
        
        data_in = []
        for tool in tools:
            data_in.append((args, git_hash, tool))
        print("Starting", num_threads, "threads.")
        with multiprocessing.Pool(processes=num_threads) as pool:
            tool_results = pool.starmap(LoopIter, data_in)
            
    return tool_results

def GetFilenameTool(git_hash, tool):
    return '{}/{}/{}-{}.txt'.format(dirData, git_hash, git_hash, tool.name)

def GetFilenameArtifact(git_hash, artifact):
    return '{}/{}'.format(dirOut, GetFilenameArtifactRelative(git_hash, artifact))

def GetFilenameArtifactRelative(git_hash, artifact):
    art_name = ntpath.basename(artifact)
    return '{}{}/{}-{}'.format(dirDataRel, git_hash, git_hash, art_name)

def GetFilenameToolPNG(tool_name):
    return '{}.png'.format(tool_name)

def all_equal2(iterator):
    return len(set(iterator)) <= 1

def PlotKPI(name, vals):
    fig = plt.figure()
    data = list(reversed(vals))
    print("Plotting", data)
    plt.plot(data)
    plt.title(name)
    plt.grid()
    plt.savefig('{}/{}'.format(dirImg, GetFilenameToolPNG(name)))
    plt.close(fig)

def GetToolHashKey(git_hash, tool_key):
    return '{}-{}'.format(git_hash, tool_key)

def GetReports(table, header):
    rep_html = tabulate(table, headers=header, tablefmt='html')
    rep_text = tabulate(table, headers=header, tablefmt='fancy_grid')
    
    return rep_html, rep_text

def ReplaceTitleLink(rep_html):
    for tool in tools:
        name = tool.alias
        link = dirImgRel + GetFilenameToolPNG(name)
        rep_html = rep_html.replace(name + TAG_PLOT, hyperlink_format.format(link=link, text=name))
    return rep_html

def ReplaceStyle(rep_html):
    style = "style='border: 1px solid;'"
    for tag in ("<table", "<td", "<tr"):
        rep_html = rep_html.replace(tag, "{} {}".format(tag, style))
    return rep_html

def ReplaceToolsCells(checkouts, rep_html):
    for chk in checkouts:        
        for itool, kpis in enumerate(chk.tool_results):
            tool_key = tools[itool].alias
            tool = tools[itool]
            cell = tool.GetCell(chk.git_hash, kpis)            
            key = GetToolHashKey(chk.git_hash, tool_key)
            rep_html = rep_html.replace(key, cell)
            
    return rep_html

def CreateHeader():
    header = []
    header.append("Commit")
    header.append("Date")
    for tool in tools:
        name = tool.alias
        header.append(name + TAG_PLOT)
    return header

def CreateTable(checkouts):
    table = []
    
    for chk in checkouts:
        row = []
        row.append(chk.git_hash)
        row.append(chk.date)
        
        for tool in tools:
            tool_key = tool.alias
            row.append(GetToolHashKey(chk.git_hash, tool_key))
            
        table.append(row)
    return table

def GetKPIs(checkouts):
    tool_kpi = {}
        
    for chk in checkouts:       
        for itool, result in enumerate(chk.tool_results):
            kpis = []
            tool_key = tools[itool].alias
            for res in result.split():
                try:
                    kpi = int(res)
                except:
                    print("Couldn't read KPI for ", tool_key)
                    kpi = 0;
                kpis.append(kpi)
            
            if tool_key not in tool_kpi:
                tool_kpi[tool_key] = []
            tool_kpi[tool_key].append(kpis)
    return tool_kpi

def MakeReport(checkouts):   
    table = CreateTable(checkouts)
    tool_kpi = GetKPIs(checkouts)
        
    for tool_key in tool_kpi:
        kpi = tool_kpi[tool_key]
        PlotKPI(tool_key, kpi)

    header = CreateHeader()
    rep_html, rep_text = GetReports(table, header)
    rep_html = ReplaceTitleLink(rep_html)
    rep_html = ReplaceStyle(rep_html)
    rep_html = ReplaceToolsCells(checkouts, rep_html)

    file_name_rep = dirOut + "/index.html"
    with open(file_name_rep, 'w') as out:
        out.writelines(rep_html)
        print("Wrote report to:\n" + os.path.abspath(file_name_rep))
    #print(rep)
    print(rep_text)
    
def FormatMinutes(seconds):
    return "{}".format(round(seconds / 60, 2))

def Main():
    for dir_ini in (dirOut, dirImg, dirData):
        os.makedirs(dir_ini, exist_ok=True)
    
    parser = GetParser()
    args = parser.parse_args()
    
    checkouts = []

    start = time.time()
    
    iterTimeAvg = 0
    timeLeft = 0
    spaces = "-" * 50
    for head in range(args.num_back):
        print("\n" + spaces)
        print("HEAD~{}".format(head), "{}/{}".format(head+1, args.num_back), 
              "Time: Average =", FormatMinutes(iterTimeAvg), "ETA =", FormatMinutes(timeLeft))
        subprocess.run(['git', 'checkout', 'master'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'checkout', 'HEAD'],   stdout=subprocess.DEVNULL)
        subprocess.run(['git', 'checkout', 'HEAD~{}'.format(head)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        result_hash = subprocess.run(['git', 'log',  '--pretty=format:%h', '-n', '1'], stdout=subprocess.PIPE)
        result_date = subprocess.run(['git', 'show', '--format=%cs', '-s'], stdout=subprocess.PIPE)
        
        result_hash_str = result_hash.stdout.decode('utf-8')
        result_date_str = result_date.stdout.decode('utf-8')
        reports = GetResultsForCheckout(args, result_hash_str)
        checkouts.append(Checkout(result_hash_str, result_date_str, reports))
        
        time_passed = time.time() - start
        iterTimeAvg = time_passed / (head+1)
        timeLeft = iterTimeAvg * (args.num_back - head - 1)
        
        print(spaces + "\n")
        
    MakeReport(checkouts)
    
    end = time.time()
    diff = end - start
    print("Time passed:", FormatMinutes(diff), "minutes.")
        
if __name__ == "__main__":
    Main()
