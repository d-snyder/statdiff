#!python

import sys, re, os, pipes
from optparse import OptionParser
from datetime import datetime

#Suppress md5 deprecation warning.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        import paramiko
    except Exception, e:
        paramiko = None

class StatDiff():
    _STAT_FORMAT = '%A %U %G %s %X %Y %Z %n'
    _STAT_REGEX = '(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s(.+)'
    _STAT_CMD = "find %s -mindepth 1 -maxdepth 1 -exec stat --format=\'%s\' {} \\;"
    _p = re.compile(_STAT_REGEX)
    _USAGE = 'usage: %prog [options] [host:]path1 [host:]path2'

    subject_left = None
    subject_right = None
    def __init__(self,argv):
        parser = OptionParser(self._USAGE)
        parser.add_option('-v','--verbose',action="store_true", dest="verbose", default=False, help="Turns on additional output")
        parser.add_option('-l','--long',action="store_true", dest="long", default=False, help="Turns on long output mode.")
        parser.add_option('-1','--short',action="store_true", dest="short", default=False, help="Turns on short output mode.")
        parser.add_option('-a','--all',action="store_true", dest="all", default=False, help="Includes normally hidden files")
        parser.add_option('--rights',action="store_true", dest="rights", default=False, help="Compare access rights of files.")
        parser.add_option('--owner',action="store_true", dest="owner", default=False, help="Compare owner name of files")
        parser.add_option('--group',action="store_true", dest="group", default=False, help="Compare group name of files")
        parser.add_option('--atime',action="store_true", dest="atime", default=False, help="Compare access time of files")
        parser.add_option('--mtime',action="store_true", dest="mtime", default=False, help="Compare modify time of files")
        parser.add_option('--size',action="store_true", dest="size", default=False, help="Compare size of files")
        (options,args) = parser.parse_args(argv)
        self.options = options
        if(len(args) < 3):
            raise Exception('You must provide at least two subjects to compare')
        self.subject_left = args[1]
        self.subject_right = args[2]

        self.ckeys = set()
        if(options.rights): self.ckeys.add('rights')
        if(options.owner): self.ckeys.add('owner')
        if(options.group): self.ckeys.add('group')
        if(options.atime): self.ckeys.add('atime')
        if(options.mtime): self.ckeys.add('mtime')
        if(options.size): self.ckeys.add('size')
        if len(self.ckeys) == 0: self.ckeys = None

    def _parse_statlines(self,statlines):
        stats = dict()
        for line in statlines:
            stat = self._parse_statline(line)
            if self.options.all or not stat['filename'].startswith('.'):
                stats[stat['filename']] = stat
        return stats

    def _parse_statline(self,statline):
        m = self._p.search(statline)
        stat = dict()
        if m:
            stat['rights'] = m.group(1)
            stat['owner'] = m.group(2)
            stat['group'] = m.group(3)
            stat['size'] = m.group(4)
            stat['atime'] = m.group(5)
            stat['mtime'] = m.group(6)
            fnpath = m.group(7).split('/')
            stat['filename'] = fnpath.pop()
        return stat

    def _exec_stat(self,path):
        pathelem = path.split(':')
        cmd = self._STAT_CMD % (pathelem.pop(),self._STAT_FORMAT)
        if self.options.verbose:
            print "Executing command: " + cmd
        if(pathelem):
            return self._exec_remote(pathelem.pop(),cmd)
        else:
            return self._exec_local(cmd)

    def _exec_local(self,cmd):
        stream = os.popen(cmd)
        out = stream.readlines()
        exit = stream.close()
        if(not exit):
            return out
        else:
            raise Exception(os.WEXITSTATUS(exit))

    def _exec_remote(self,host,cmd):
        if(paramiko):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(host)
            stdin, stdout, stderr = client.exec_command(cmd)
            return stdout.readlines()
        else:
            raise Exception('paramiko library was not loaded and is required for remote diff support')

    def _gen_diff(self,lsubject,rsubject,compare_keys = None):
        lkeys = set(lsubject)
        rkeys = set(rsubject)

        lextras = lkeys.difference(rkeys)
        rextras = rkeys.difference(lkeys)

        different = dict()
        for key in lkeys.intersection(rkeys):
            if compare_keys:
                ckeys = compare_keys
            else:
                ckeys = set(lsubject[key])
            for ckey in ckeys:
                if(lsubject[key][ckey] != rsubject[key][ckey]):
                    if key not in different:
                        different[key] = dict()
                    different[key][ckey] = [lsubject[key][ckey],rsubject[key][ckey]]

        return (different,lextras,rextras)

    def do_diff(self):
        try:
            lsubjects = self._parse_statlines(self._exec_stat(self.subject_left))
            rsubjects = self._parse_statlines(self._exec_stat(self.subject_right))
            (difference,lextras,rextras) = self._gen_diff(lsubjects,rsubjects,self.ckeys)
            return self.format_diff(lsubjects,rsubjects,difference,lextras,rextras)
        except Exception,e:
            print str(e)
            return

    def format_diff(self,lsubjects,rsubjects,difference,lextras,rextras):
        if(len(difference)==0 and len(lextras)==0 and len(rextras)==0):
            return
        output = []
        output.append('--- %s' % (self.subject_left))
        output.append('+++ %s' % (self.subject_right))

        keylist = list(set(difference).union(lextras).union(rextras))
        keylist.sort()

        maxlen = max(map(len,keylist))

        if not self.options.short:
            if maxlen > 40: maxlen = 40

        for key in keylist:
            dkey = key
            if len(key) > maxlen:
                dkey = (key[0:maxlen-1] +  '*')
            dkey = dkey.ljust(maxlen)
            if key in lextras:
                output.append('- %s %s' %
                        (dkey,self.format_subject(lsubjects[key])))
            if key in rextras:
                output.append('+ %s %s' %
                        (dkey,self.format_subject(rsubjects[key])))
            if key in difference:
                output.append('- %s %s' %
                        (dkey,self.format_subject(lsubjects[key])))
                output.append('+ %s %s' %
                        (dkey,self.format_subject(rsubjects[key])))
        return '\n'.join(output)

    def format_subject(self,subject):
        rights = subject['rights']
        group = subject['group']
        owner = subject['owner']
        size = subject['size']
        atime = subject['atime']
        mtime = subject['mtime']
        filename = subject['filename']

        datime = datetime.fromtimestamp(int(atime))
        dmtime = datetime.fromtimestamp(int(mtime))

        if self.options.long:
            return '%10s   - %8s %8s %10s %8s (Access: %8s)' % (rights,owner,group,size,dmtime,datime)
        elif not self.options.short:
            return '%8s %8s' % (size,dmtime)
        else:
            return ''

def statdiff_main():
    sd = StatDiff(sys.argv)
    output = sd.do_diff()
    if output:
        print output
    elif sd.options.verbose:
        print "No Differences Found."

if __name__ == '__main__':
    statdiff_main()

