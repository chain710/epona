#!/usr/bin/env python
#coding=utf-8

import os, sys
from datetime import datetime
from fabric.api import local, run, env, put, sudo, lcd, cd
from ConfigParser import SafeConfigParser


def deploy_dir(local_dir, conf):
    if None != conf['pre_process']:
        run(conf['pre_process'])
        
    for root,dirs,files in os.walk(local_dir):
        for file in files:
            if file.startswith('_'):
                continue
            deploy_file = os.sep.join([root, file])
            result = put(local_path=deploy_file, 
                remote_path=conf['remote_dir'], 
                use_sudo=False, 
                mirror_local_mode=False)
            if (len(result.failed) > 0):
                for i in result.failed:
                    print "transfer failed: %s"%(i)
                    
    if None != conf['post_process']:
        run(conf['post_process'])

def config_get(conf, section, option, default):
    if conf.has_option(section, option):
        return conf.get(section, option)
    else:
        return default
        
def load_deploy_conf(conf_file):
    remote_dir = "~"
    post_process = None
    pre_process = None
    conf_reader = SafeConfigParser({'password':None, 'user':None, 'remote_dir':None, 'post_process':None})
    try:
        conf_reader.read(conf_file)
    except Exception, e:
        sys.stderr.write("read(%s) failed, err:%s\n"%(conf_file, str(e)))
        return None
    # check def conf
    if conf_reader.has_section('_def'):
        def_pwd = config_get(conf_reader, "_def", "password", "")
        def_usr = config_get(conf_reader, "_def", "user", "root")
        remote_dir = config_get(conf_reader, "_def", "remote_dir", "/tmp")
        post_process = config_get(conf_reader, "_def", "post_process", None)
        pre_process = config_get(conf_reader, "_def", "pre_process", None)
        env.password = def_pwd
        env.user = def_usr
    else:
        env.password = None
        env.user = None
    
    env.hosts = []
    env.passwords.clear()
    
    for host in conf_reader.sections():
        if host.startswith('_'):
            continue
        
        host_pwd = conf_reader.get(host, "password")
        env.hosts.append(host)
        if None != host_pwd:
            env.passwords[host] = host_pwd

    return {'remote_dir':remote_dir, 'post_process':post_process, 'pre_process': pre_process}
    
def deploy():
    rootpath = "."
    for root,dirs,files in os.walk(rootpath):
        for dir in dirs:
            # process file under root only
            if (rootpath != root or dir.startswith('_')):
                continue
            
            deploy_path = dir
            conf = load_deploy_conf(os.sep.join([deploy_path, "_conf"]))
            if None == conf:
                sys.stderr.write("load conf err under %s"%(deploy_path))
                continue
            
            for host_str in env.hosts:
                env.host_string = host_str
                deploy_dir(deploy_path, conf)
            
if __name__ == '__main__':
    deploy()