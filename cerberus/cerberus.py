#!/usr/bin/python

import sys,os,fnmatch
from os.path import join,getsize,getmtime
import re,time
import argparse
import logging
import gzip

class conf_item:
    path=''
    file_pat=''
    oldest=0
    limit=0
    method='rm'
    
def proc_single_file(method, path):
    if 'gzip' == method:
        gzip_path = '%s.gz'%(path)
        f_in = open(path, 'rb')
        f_out = gzip.open(gzip_path, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(path)
    elif 'rm' == method:
        os.remove(path)
    else:
        logging.error("unknown method %s for file %s"%(method, path))

def narrow_dir(conf, dry_run):
    dir_size, flist = get_dir_childs(conf.path, conf.file_pat)

    rm_list = []
    flist.sort(key=lambda f: f['mtime'], reverse=False)
    if (dir_size > conf.limit):
        for f in flist:
            dir_size -= f['size']
            rm_list.append(f)
            logging.debug("size too large(dir=%d, file=%d), %s %s"%(dir_size, f['size'], conf.method, f['path']))
            f['_proc']=True
            if not dry_run:
                proc_single_file(conf.method, f['path'])
                
            if (dir_size <= conf.limit):
                break

    #proc expired anyway
    nowtime = time.time()
    for f in flist:
        if (not fnmatch.fnmatch(f['name'], conf.file_pat) or f['_proc']):
            continue
        if (nowtime - f['mtime'] < conf.oldest):
            break
            
        logging.debug("file too old, %s %s"%(conf.method, f['path']))
        dir_size -= f['size']
        rm_list.append(f)
        if not dry_run:
            proc_single_file(conf.method, f['path'])
            
    return rm_list, dir_size

def is_dangerous_dir(dirname):
    dirname = dirname.rstrip("/")
    return "" == dirname or "/usr" == dirname or "/usr/local" == dirname or "/var" == dirname
    
def get_dir_childs(dirname, file_pat):
    size = 0L
    flist = []
    # we dont want rm / -rf, do we?
    if is_dangerous_dir(dirname):
        logging.error("dir %s too dangerous, maybe you want to delete it manually?"%(dirname))
        return 0, []
        
    for root,dirs,files in os.walk(dirname):
        for name in files:
            fpath = join(root, name)
            if (not fnmatch.fnmatch(name, file_pat)):
                continue
            fsize = getsize(fpath)
            size += fsize
            flist.append({'path':fpath, 'mtime':int(getmtime(fpath)), 'size':fsize, 'name':name, '_proc':False})
    return size, flist

if __name__ == '__main__':
    oldest_r = {'day':86400, 'hour':3600}
    limit_r = {'k':1024, 'm':1024*1024, 'g':1024*1024*1024}
    my_dir = os.path.dirname(os.path.abspath(__file__))
    procname = os.path.basename(sys.argv[0])
    logging.basicConfig(format='%(asctime)s|%(message)s', filename='%s%s%s.log'%(my_dir, os.sep, os.path.splitext(procname)[0]), level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    
    parser = argparse.ArgumentParser(description='watch dir, proc(rm/gzip) expired files if size exceeds.')
    parser.add_argument('--dryrun', dest='dry_run', metavar='1/0', type=int, help='dryrun only(1=yes,0=no)', default=1)
    parser.add_argument('-f', dest='conf', metavar='filename', type=str, help='specify config file path', default=None)
    args = parser.parse_args()

    if None == args.conf:
        args.conf = "%s%s%s.conf"%(my_dir, os.sep, os.path.splitext(procname)[0])
        
    conf_pat = re.compile(r'([^#\s]+)\s+([^\s]+)\s+(\d+)(day|hour)\s+(\d+)(k|m|g)\s+(gzip|rm)', re.IGNORECASE)
    for line in open(args.conf):
        match = conf_pat.search(line)
        if None == match:
            continue
        
        tmp = conf_item()
        tmp.path = match.group(1)
        tmp.file_pat = match.group(2)
        tmp.oldest = int(match.group(3)) * oldest_r[match.group(4).lower()]
        tmp.limit = int(match.group(5)) * limit_r[match.group(6).lower()]
        tmp.method = match.group(7).lower()
        
        rm_list, final_size = narrow_dir(tmp, dry_run=args.dry_run>0)
        logging.info("%s %d files"%(tmp.method, len(rm_list)))
        logging.info("%s (dryrun=%d) %d files under %s, final size is %d"%(tmp.method, args.dry_run, len(rm_list), tmp.path, final_size))