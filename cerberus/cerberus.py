#!/usr/bin/python

import sys,os,fnmatch
from os.path import join,getsize,getmtime
import re,time
import argparse
import logging

class conf_item:
    path=''
    file_pat=''
    oldest=0
    limit=0

def narrow_dir(conf, dry_run):
    dir_size, flist = get_dir_childs(conf.path)

    rm_list = []
    flist.sort(key=lambda f: f['mtime'], reverse=False)
    if (dir_size > conf.limit):
        for f in flist:
            if (not fnmatch.fnmatch(f['name'], conf.file_pat)):
                continue
            dir_size -= f['size']
            rm_list.append(f)
            f['_removed']=True
            if not dry_run:
                os.remove(f['path'])
                
            if (dir_size <= conf.limit):
                break

    #delete expired anyway
    nowtime = time.time()
    for f in flist:
        if (not fnmatch.fnmatch(f['name'], conf.file_pat) or f['_removed']):
            continue
        if (nowtime - f['mtime'] < conf.oldest):
            break
            
        dir_size -= f['size']
        rm_list.append(f)
        if not dry_run:
            os.remove(f['path'])
            
    return rm_list, dir_size

def get_dir_childs(dirname):
    size = 0L
    flist = []
    for root,dirs,files in os.walk(dirname):
        for name in files:
            fpath = join(root, name)
            fsize = getsize(fpath)
            size += fsize
            flist.append({'path':fpath, 'mtime':int(getmtime(fpath)), 'size':fsize, 'name':name, '_removed':False})
    return size, flist

if __name__ == '__main__':
    oldest_r = {'day':86400, 'hour':3600}
    limit_r = {'k':1024, 'm':1024*1024, 'g':1024*1024*1024}
    my_dir = os.path.dirname(os.path.abspath(__file__))
    procname = os.path.basename(sys.argv[0])
    logging.basicConfig(format='%(asctime)s|%(message)s', filename='%s%s%s.log'%(my_dir, os.sep, os.path.splitext(procname)[0]), level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    
    parser = argparse.ArgumentParser(description='watch dir, delete expired files if size exceeds.')
    parser.add_argument('--dryrun', dest='dry_run', metavar='1/0', type=int, help='dryrun only(1=yes,0=no)', default=1)
    parser.add_argument('-f', dest='conf', metavar='filename', type=str, help='specify config file path', default=None)
    args = parser.parse_args()

    if None == args.conf:
        args.conf = "%s%s%s.conf"%(my_dir, os.sep, os.path.splitext(procname)[0])
        
    conf_pat = re.compile(r'([^#\s]+)\s+([^\s]+)\s+(\d+)(day|hour)\s+(\d+)(k|m|g)', re.IGNORECASE)
    for line in open(args.conf):
        match = conf_pat.search(line)
        if None == match:
            continue
        
        tmp = conf_item()
        tmp.path = match.group(1)
        tmp.file_pat = match.group(2)
        tmp.oldest = int(match.group(3)) * oldest_r[match.group(4).lower()]
        tmp.limit = int(match.group(5)) * limit_r[match.group(6).lower()]
        rm_list, final_size = narrow_dir(tmp, dry_run=args.dry_run>0)
        print("%d files deleted"%(len(rm_list)))
        logging.info("delete(dryrun=%d) %d files under %s, final size is %d"%(args.dry_run, len(rm_list), tmp.path, final_size))
        for f in rm_list:
            logging.debug("%s deleted"%(f['path']))