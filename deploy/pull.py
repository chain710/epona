#!/usr/bin/python

import sys
import os
import json
import logging
from fabric.api import get, env
import shutil
from datetime import datetime
import random

def load_pull_conf(file):
    try:
        with open(file, "r") as f:
            raw = f.read()
            return json.loads(raw)
    except IOError as e:
        logging.error("file io error %s"%(e))
        return None
        
def pull_one_host(local_path, pull_dict):
    host = str(pull_dict['host'])
    logging.debug("now pulling files from %s"%(host))
    env.hosts = [host]
    env.host_string = host
    env.password = str(pull_dict.get('password', ''))
    ldir = pull_dict.get('local_dir', local_path)
    for f in pull_dict.get("files", []):
        result = get(f, ldir)
        if (len(result.failed) > 0):
            for i in result.failed:
                logging.error("pull %s failed"%(f))

def pull_one_dir(conf_path, cleanup = False):
    local_path = os.path.dirname(conf_path)
    if cleanup:
        logging.info("now clean up %s ..."%(local_path))
        
        tmp_conf_path = "/tmp/tmp_deploy_conf_%s_%d"%(datetime.now().strftime("%Y%m%d%H%M%S"), random.randint(0,1000))
        #move _conf to /tmp
        shutil.move(conf_path, tmp_conf_path)
        #rm whole dir
        shutil.rmtree(local_path, ignore_errors = True)
        #make new one
        os.makedirs(local_path)
        #move _conf back
        shutil.move(tmp_conf_path, conf_path)
        
    conf = load_pull_conf(conf_path)
    if conf == None:
        logging.error("find no conf file %s\n"%(conf_path))
        return -1
        
    for i in conf:
        pull_one_host(local_path, i)
            
if __name__ == "__main__":
    if (len(sys.argv) <= 1):
        sys.stderr.write("Usage: %s pullname\n"%(sys.argv[0]))
        sys.exit(0)
    pull_name = sys.argv[1]
    rootpath = os.path.dirname(os.path.abspath(__file__))
    confpath = os.path.join(rootpath, pull_name, '_conf')
    pull_one_dir(confpath, True)