#!/usr/bin/env python
#coding=utf-8

import os, sys
from datetime import datetime
import fabric
from fabric.api import local, run, env, put, sudo, lcd, cd
from fabric.contrib.project import upload_project
from fabric.context_managers import settings
from ConfigParser import SafeConfigParser
import logging
import random

def run_remote(cmdline, use_sudo):
    if use_sudo:
        sudo(cmdline)
    else:
        run(cmdline)

def deploy_dir(local_dir, conf, pack_name):
    sprefix=conf['sudo_prefix']
    if sprefix is None:
        sprefix = env.sudo_prefix
    with settings(sudo_prefix=sprefix), fabric.context_managers.show("debug"):
        if None != conf['pre_process']:
            run_remote(conf['pre_process'], conf['sudo'])
            
        result = put(local_path=pack_name, 
                    remote_path="/tmp", 
                    use_sudo=False, 
                    mirror_local_mode=False)
        if (len(result.failed) > 0):
            for i in result.failed:
                logging.error( "transfer failed: %s"%(i) )

        run_remote("mkdir -p %s"%(conf['remote_dir']), conf['sudo'])
        run_remote("tar -xzf /tmp/%s -C %s"%(pack_name, conf['remote_dir']), conf['sudo'])
        #delete tmp file
        run("rm /tmp/%s"%(pack_name))
    
        if None != conf['post_process']:
            run_remote(conf['post_process'], conf['sudo'])
    
def config_get(conf, section, option, default):
    if conf.has_section(section) and conf.has_option(section, option):
        if type(default) == bool:
            return "yes" == conf.get(section, option) or "true" == conf.get(section, option)
        else:
            return conf.get(section, option)
    else:
        return default
        
def load_deploy_conf(conf_file):
    remote_dir = ""
    post_process = None
    pre_process = None
    conf_reader = SafeConfigParser()
    try:
        conf_reader.read(conf_file)
    except Exception, e:
        sys.stderr.write("read(%s) failed, err:%s\n"%(conf_file, str(e)))
        return
    # check def conf
    def_pwd = config_get(conf_reader, "_def", "password", "")
    remote_dir = config_get(conf_reader, "_def", "remote_dir", "")
    post_process = config_get(conf_reader, "_def", "post_process", None)
    pre_process = config_get(conf_reader, "_def", "pre_process", None)
    
    for host in conf_reader.sections():
        if host.startswith('_'):
            continue
            
        yield {
            'host': config_get(conf_reader, host, "host", host),
            'password': config_get(conf_reader, host, "password", def_pwd), 
            'remote_dir': config_get(conf_reader, host, "remote_dir", remote_dir), 
            'post_process': config_get(conf_reader, host, "post_process", post_process), 
            'pre_process': config_get(conf_reader, host, "pre_process", pre_process), 
            'sudo': config_get(conf_reader, host, "sudo", False), 
            'sudo_prefix': config_get(conf_reader, host, "sudo_prefix", None), 
        }
        
def clean_deploy(deploy_name, deploy_root = None):
    if None == deploy_name:
        return
        
    if None != deploy_root:
        rootpath = deploy_root
    else:
        rootpath = os.path.dirname(os.path.abspath(__file__))

    for root,dirs,files in os.walk(rootpath):
        for dir in dirs:
            # process file under root only
            if (dir != deploy_name):
                continue
            
            if (rootpath != root or dir.startswith('_')):
                continue
            
            logging.info( "now cleanup %s ..."%(dir) )
            with lcd(dir):
                tmp_conf_path = "/tmp/tmp_deploy_conf_%s_%d"%(datetime.now().strftime("%Y%m%d%H%M%S"), random.randint(0,1000))
                local("mv ./_conf %s"%(tmp_conf_path))
                local("rm * -rf")
                local("mv %s ./_conf"%(tmp_conf_path))
    
def deploy(deploy_name = None, deploy_root = None):
    if None != deploy_root:
        rootpath = deploy_root
    else:
        rootpath = os.path.dirname(os.path.abspath(__file__))
    deploynum = 0
    for root,dirs,files in os.walk(rootpath):
        for dir in dirs:
            # process file under root only
            if (deploy_name != None and dir != deploy_name):
                continue
            
            if (rootpath != root or dir.startswith('_')):
                continue
            
            #prepare local pack
            logging.info( "now deploy directory %s ..."%(dir) )
            pack_name = "_deploy.tar.gz"
            with lcd(dir):
                local("tar -czf ../%s --exclude=_conf *"%(pack_name))
            
            for deploy_conf in load_deploy_conf(os.sep.join([dir, "_conf"])):
                env.hosts = []
                env.hosts.append(deploy_conf['host'])
                env.password = deploy_conf['password']
                #host_string Defines the current user/host/port which Fabric will connect to when executing run, put and so forth.
                env.host_string = deploy_conf['host']
                deploy_dir(dir, deploy_conf, pack_name)
                
            local("rm ./%s"%(pack_name));
            deploynum = deploynum + 1
    
    return deploynum
            
if __name__ == '__main__':
    my_dir = os.path.dirname(os.path.abspath(__file__))
    procname = os.path.basename(sys.argv[0])
    logging.basicConfig(format='%(asctime)s|%(message)s', filename=os.path.join(my_dir, os.path.splitext(procname)[0]+".log"), level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    
    deploy_name = None
    if (len(sys.argv) > 1):
        deploy_name = sys.argv[1]
    deploy(deploy_name)