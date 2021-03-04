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


dirOut = 'build/report-health/'
dirImgRel = 'img/'
dirDataRel = 'data/'
dirImg = dirOut + dirImgRel
dirData = dirOut + dirDataRel
TAG_PLOT = '-plot'

hyperlink_format = '<a href="{link}">{text}</a>'

def GetDirThis():
    return os.path.dirname(os.path.realpath(__file__))


class Tool:
    def __init__(self, name, alias, base_path, artifacts=[], kpis='', kpis_descr=[], params=[]):
        self.name = name
        self.path = os.path.join("utils", "health", name)
        self.base_path = base_path
        self.alias = alias
        self.params = params
        self.kpis_descr = self.ConvertStringToArrayOfStrings(kpis_descr)
        artifacts = self.ConvertStringToArrayOfStrings(artifacts)
        self.kpis = kpis
        if len(kpis):
            self.kpis = os.path.join(base_path, kpis)

        self.artifacts = []
        for art in artifacts:
            self.artifacts.append(os.path.join(base_path, art))

    def ConvertStringToArrayOfStrings(self, stringOrArray):
        if isinstance(stringOrArray, str):
            return [stringOrArray]
        return stringOrArray

    def GetKPIs(self, res):
        return res
    
    def IsRunnable(self):
        return True
    
    def NeedsBuild(self):
        return False

    def GetCell(self, git_hash, kpis):
        kpisOK = True
        try:
            kpi = kpis.strip().split(' ')[0]
            print("KPI = ", kpi)
            kpiVal = float(kpi)
            if kpiVal <= 0:
                kpisOK = False
        except:
            kpisOK = False
        
        cell = ''
        sep = ' '
        for iart, artifact in enumerate(self.artifacts):
            link_txt = "-{}-".format(iart+1)
            if kpisOK:
                link = GetFilenameArtifactRelative(git_hash, artifact)
                cell += hyperlink_format.format(link=link, text=link_txt) + sep
            else:
                cell += link_txt + sep
            
        cell += kpis

        return cell

    def _getKPIs(self, res):
        raise NotImplementedError("_getKPIs() for {}".format(self.name))


class LOC(Tool):
    def __init__(self):
        super().__init__('loc.sh', 'loc', '.', kpis='kpis.txt', kpis_descr=['Everything', 'Headers only'])

class Files(Tool):
    def __init__(self):
        super().__init__('files.sh', 'files', 'build',
                         ['files.txt'
                         ,'files2.txt'])

class Failing(Tool):
    def __init__(self):
        super().__init__('failing.sh', 'failing', '.', kpis="kpis.txt")

class CBA(Tool):
    def __init__(self):
        super().__init__('clang-build-time-analyzer-run.sh', 'cbta', 'build/clang-build-analyser',
                         ['cba-result.txt'
                         ,'cba-trace.txt.txz'],
                         kpis='kpis.txt', kpis_descr=['T parsing', 'T codegen'])
        
    def IsRunnable(self):
        return False


class TidyC(Tool):
    def __init__(self):
        super().__init__('clang-tidy-run-cc.sh', 'tidyC', "build/clang-tidy-C",
                             ['clang-tidy-result-C.txt.txz']
                             , kpis='kpis.txt', kpis_descr='Lines of warnings'
                        )

class TidyCXX(Tool):
    def __init__(self):
        super().__init__('clang-tidy-run-cpp.sh', 'tidyCXX', "build/clang-tidy-CXX",
                             ['clang-tidy-result-CXX.txt.txz']
                             , kpis='kpis.txt', kpis_descr='Lines of warnings'
                        )
class IWYU(Tool):
    def __init__(self):
        super().__init__('clang-include-what-you-use-run.sh', 'iwyu', "build/clang-iwyu",
                         ['iwyu-result.txt.txz'],
                         kpis='kpis.txt', kpis_descr=['lines of warnings'])
        
class Doxygen(Tool):
    def __init__(self):
        super().__init__('doxygen.sh', 'doxygen', "build/doxygen",
                         ['doxygen.tar.xz'],
                         kpis='kpis.txt', kpis_descr=''
                         )
        
class Valgrind(Tool):
    def __init__(self):
        super().__init__('valgrind-tests.sh', 'valgrind', "build/valgrind-output",
                         ['valgrind-output.txz'],
                         kpis='kpis.txt', kpis_descr=['time taken'], params=[os.path.join(GetDirThis(), 'valgrind-executable-list.txt')])
        
    def NeedsBuild(self):
        return True


class Checkout:
    def __init__(self, git_hash, date, tool_results):
        self.git_hash = git_hash
        self.date = date
        self.tool_results = tool_results

TOOLS_PROD = [
        Valgrind()  # Super heavy
    ,   TidyCXX()   # Super heavy
    ,   TidyC()
    ,   LOC()       # Light
    ,   CBA()       # Heavy
    ,   IWYU()
    ,   Doxygen()   # Heavy on HDD
    ,   Failing()   # Test handling of failing report
    ]

TOOLS_TESTING = [
        LOC()       # Light
    #,   Valgrind()  # Heavy
    , Doxygen()
    ,   Files()     # Light
    ,   Failing()   # Test handling of failing report
    #,   TidyC()
    #,   TidyCXX()
    ]

TOOLS = []
TOOLS_DIC = {}

def GetParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num-back', default=5, type=int, help="How many checkouts from head")
    parser.add_argument('-j', '--num-threads', default=1, type=int, help="How many threads")
    parser.add_argument('-r', '--report-only', default=False, action='store_true', help="Only generate report from the available data")
    parser.add_argument('-c', '--disable-cache', default=False, action='store_true', help="Disable cache")
    parser.add_argument('-l', '--leave-faulty', default=False, action='store_true', help="Leave the faulty reports and don't retry generating them")
    parser.add_argument('-s', '--tools-testing', default=False, action='store_true', help="Use only the testing tools")

    return parser

def Build():
    pathTool = os.path.join(GetDirThis(), 'build.sh')
    subprocess.run([pathTool], stdout=subprocess.PIPE)

def GetResultsForTool(tool):
    pathTool = os.path.join(GetDirThis(), tool.name)
    #pathTool = tool.path
    if tool.IsRunnable():
        if tool.NeedsBuild():
            Build()
        result = subprocess.run([pathTool] + tool.params, stdout=subprocess.PIPE)
        if result.returncode != 0:
            raise ValueError("Return code {} for tool {}".format(result.returncode, tool.name))
 
        for artifact in tool.artifacts:
            if not os.path.isfile(artifact):
                raise ValueError("No artifact {} for tool {}".format(artifact, tool.name))

    if tool.kpis:
        print(tool.name, "Opening:", tool.kpis)
        with open(tool.kpis) as fkpis:
            kpis = fkpis.readline()
    else:
        kpis = '0'
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
            
            if not tool.IsRunnable():
                # TODO
                if tool.kpis:
                    if os.path.isfile(tool.kpis):
                        shutil.move(tool.kpis, frep)
                for artifact in tool.artifacts:
                    MoveArtifacts(git_hash, artifact)
                    
                    
            with open(frep) as fin:
                res = fin.readlines()[0]

            for artifact in tool.artifacts:
                dst = GetFilenameArtifact(git_hash, artifact)

                is_artifact = os.path.isfile(dst)
                if not is_artifact:
                    res = '-3'
                    print("Target artifact", dst, "not available! Error code", res)
                    if not args.leave_faulty and not args.report_only:
                        print("Retrying", tool.name)
                        res = ProcessTool(args, tool, git_hash)

        else:
            res = ProcessTool(args, tool, git_hash)

    except Exception as e:
        res = '-1'
        print(e)
        print("Error executing tool", tool.name, "Error code", res)

        # TODO: Better error handling here
    finally:
        CreateDirIfNotExists(frep)
        with open(frep, 'w') as fin:
            fin.writelines([res])

        return res
    
def MoveArtifacts(git_hash, artifact):
    if os.path.isfile(artifact):
        dst = GetFilenameArtifact(git_hash, artifact)
        CreateDirIfNotExists(dst)
        #print("dst", dst)
        shutil.move(artifact, dst)
        #shutil.copy(artifact, dst)

def ProcessTool(args, tool, git_hash):
    if args.report_only:
        return "0"
        
    res = GetResultsForTool(tool)

    for artifact in tool.artifacts:
        if os.path.isfile(artifact):
            MoveArtifacts(git_hash, artifact)
        else:
            res = '-2'
            print("Source artifact", artifact, "not available! Error code", res)
        
    return res
    
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
    return res

def LoopIter(args, git_hash, tool):
    res = GetResultsForToolCached(args, git_hash, tool)
    kpis = tool.GetKPIs(res)
    return kpis

def GetResultsForCheckout(args, git_hash, date_str):
    tool_results = []

    if args.num_threads <= 1:
        for tool in TOOLS:
            kpis = LoopIter(args, git_hash, tool)
            tool_results.append(kpis)
    else:
        data = []
        for tool in TOOLS:
            data.append((args, git_hash, tool))
        with multiprocessing.Pool(args.num_threads) as pool:
            tool_results = pool.starmap(LoopIter, data)

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

def PlotKPI(alias, vals):
    fig = plt.figure()
    #data = list(reversed(vals))
    data = list(vals)
    print("Plotting", alias, data)
    # Equalize the dimensions
    maxDim = 0
    for ele in data:
        if len(ele) > maxDim:
            maxDim = len(ele)
    for ele in data:
        if len(ele) < maxDim:
            ele.append(0)
    plt.plot(data)
    plt.title(alias)
    plt.xlabel('HEAD~x')
    tool = TOOLS_DIC[alias]
    if len(tool.kpis_descr):
        plt.legend(tool.kpis_descr)
    
    plt.grid()
    plt.savefig('{}/{}'.format(dirImg, GetFilenameToolPNG(alias)))
    plt.close(fig)

def GetToolHashKey(git_hash, tool_key):
    return '{}-{}'.format(git_hash, tool_key)

def GetReports(table, header):
    rep_html = tabulate(table, headers=header, tablefmt='html')
    rep_text = tabulate(table, headers=header, tablefmt='fancy_grid')

    return rep_html, rep_text

def ReplaceTitleLink(rep_html):
    for tool in TOOLS:
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
            tool_key = TOOLS[itool].alias
            tool = TOOLS[itool]
            cell = tool.GetCell(chk.git_hash, kpis)
            key = GetToolHashKey(chk.git_hash, tool_key)
            rep_html = rep_html.replace(key, cell)

    return rep_html

def AddHeader(rep_html):
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    header = """<!DOCTYPE html>
    <html>
    <head>
      <title>Monero statistics</title>
    </head>
    <body>
    <h1>Monero statistics from {}</h1>
    <p>The headers are links to plots of a given tool's KPIs (Key Performance Index).
     The table cell links point to a given tool's artifact(s).
     The numbers are the KPIs. Negative numbers are error codes. The tools are: Valgrind, Doxygen, Clang-Tidy, LinesOfCode, ClangBuildAnalyser, Include-What-You-Use, and a test script. Beware of the unpacked size of some of the artifacts. Clang-Tidy-CXX weights over 500 MB! 
     Unpack the .txz files with: 'tar -xvf artifact.txt.txz'.
     </p>
    """.format(timestamp)
    footer = "</body>"
    return header + rep_html + footer   

def CreateHeader():
    header = []
    header.append("Commit")
    header.append("Date")
    for tool in TOOLS:
        name = tool.alias
        header.append(name + TAG_PLOT)
    return header

def CreateTable(checkouts):
    table = []

    for chk in checkouts:
        row = []
        row.append(chk.git_hash)
        row.append(chk.date)

        for tool in TOOLS:
            tool_key = tool.alias
            row.append(GetToolHashKey(chk.git_hash, tool_key))

        table.append(row)
    return table

def GetKPIs(checkouts):
    tool_kpi = {}

    for chk in checkouts:
        for itool, result in enumerate(chk.tool_results):
            kpis = []
            tool_key = TOOLS[itool].alias
            for res in result.split():
                try:
                    #print(tool_key, res)
                    kpi = float(res)
                except:
                    try:
                        kpi = int(res)
                    except:
                        print("Couldn't read KPI for ", tool_key)
                        kpi = 0;
                kpis.append(kpi)

            if tool_key not in tool_kpi:
                tool_kpi[tool_key] = []
            if all(i >= 0 for i in kpis ):
                tool_kpi[tool_key].append(kpis)
    return tool_kpi

def MakeReport(checkouts):
    print("Generating report for {} checkouts".format(len(checkouts)))
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
    rep_html = AddHeader(rep_html)

    #print(rep)
    print(rep_text)

    file_name_rep = dirOut + "/index.html"
    with open(file_name_rep, 'w') as out:
        out.writelines(rep_html)
        print("Wrote report to:\n" + os.path.abspath(file_name_rep))

def FormatMinutes(seconds):
    return "{}".format(round(seconds / 60, 2))

def Main():
    global TOOLS
    global TOOLS_DIC

    for dir_ini in (dirOut, dirImg, dirData):
        os.makedirs(dir_ini, exist_ok=True)

    parser = GetParser()
    args = parser.parse_args()

    if args.tools_testing:
        TOOLS = TOOLS_TESTING
    else:
        TOOLS = TOOLS_PROD

    if args.tools_testing:
        TOOLS = TOOLS_TESTING
    else:
        TOOLS = TOOLS_PROD
        
    for tool in TOOLS:
        TOOLS_DIC[tool.alias] = tool

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
        print("Git ID", result_hash_str, result_date_str)
        reports = GetResultsForCheckout(args, result_hash_str, result_date_str)
        if (any(int(i.strip().replace(" ", "")) > 0 for i in reports)):
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
