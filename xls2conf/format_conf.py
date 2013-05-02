#!/usr/bin/env python
#coding=utf-8
from openpyxl import load_workbook
import os, fnmatch
import codecs
from sets import Set
import argparse
import logging
import hashlib

class src_format:
    line = 1
    inf = 2
    
class dst_format:
    ini = 1
    xml = 2

class output_config:
    def __init__(self):
        self.type = src_format.line
        #output_name=>file_name
        self.outputs = {}
        
    def from_sheet(self, sheet):
        for cells in sheet.rows:
            k = cells[0].value
            v = cells[1].value
            if k == 'type':
                if v == "line":
                    self.type = src_format.line
                elif v == "inf":
                    self.type = src_format.inf
                else:
                    logging.error("unknown source format %s"%(v))
                
            elif k.startswith('outconf_'):
                self.outputs[k.split('_', 1)[1]] = cells[1].value
            else:
                logging.error("unknown output config key %s"%(k))

class field_descriptor:
    def __init__(self, desc):
        metas = unicode(desc).split('.')
        #field name
        self.name = metas[0]
        #output names
        self.outputs = Set([k.split("_", 1)[1] for k in metas[1:] if k.startswith('o_')])
        
    def is_suppressed(self, outputs):
        if 0 == len(self.outputs):
            return False
        
        for k in outputs:
            if k in self.outputs:
                return False
        return True
        
def cell_to_string(c):
    if (c.is_date()):
        return c.value.strftime("%Y-%m-%d_%H:%M:%S")
    else:
        return unicode(c.value)
        
def xml_entry(c, d):
    return u"<%s>%s</%s>"%(d, c, d)

def line_data_from_sheet(output_name, sheet, data):
    add_comment = False
    if not isinstance(data, list):
        data = []
        add_comment = True
    rows = sheet.rows
    field_desc = [field_descriptor(f.value) for f in rows[0]]
    field_idx = [i for i in range(0, len(field_desc)) if not field_desc[i].is_suppressed([output_name])]
    if add_comment:
        #注释
        data.append([field_desc[i].name for i in field_idx])
    for r in rows[1:]:
        data.append([cell_to_string(r[i]) for i in field_idx])
        
    return data
    
def inf_data_from_sheet(output_name, sheet, data):
    if not isinstance(data, dict):
        data = {}
    rows = sheet.rows
    section = "_"
    skip_mode = False
    for row in rows:
        if len(row) < 2:
            continue
        fdesc = field_descriptor(row[0].value)
        if row[1].value == None:
            section = fdesc.name
            if fdesc.is_suppressed([output_name]):
                skip_mode = True
            else:
                skip_mode = False
                
            continue
        elif skip_mode or fdesc.is_suppressed([output_name]):
            continue
        
        v = cell_to_string(row[1])
        if data.has_key(section):
            data[section].update({fdesc.name:v})
        else:
            data.update({section: {fdesc.name:v}})
    return data
    
def line_data_to_xml(data):
    field_desc = data[0]
    content = ''
    for row in data[1:]:
        content += "\n<man>\n"
        for i in range(0, len(field_desc)):
            content += xml_entry(row[i], field_desc[i])
        content += "\n</man>\n"
    return u"<?xml version='1.0' encoding='UTF-8' standalone='yes'?><conf>%s</conf>\n"%(content)
    
def line_data_to_ini(data):
    field_desc = data[0]
    content = '#'+' '.join(field_desc)+'\n'
    for row in data[1:]:
        content += ' '.join(row) + '\n'
    return content

def inf_data_to_xml_seg(data):
    content = ''
    for k in data:
        v = data[k]
        if isinstance(v, dict):
            content += xml_entry(inf_data_to_xml_seg(v), k)
        else:
            content += xml_entry(v, k)
    return content
    
def inf_data_to_xml(data):
    return u"<?xml version='1.0' encoding='UTF-8' standalone='yes'?><conf>%s</conf>\n"%(inf_data_to_xml_seg(data))
    
def inf_data_to_ini(data):
    content = ''
    for k in data:
        v = data[k]
        if isinstance(v, dict):
            content += "[%s]\n"%(k)
            content += inf_data_to_ini(v)
        else:
            content += "%s=%s\n"%(k, v)
    return content
            
def write_data_to_file(type, data, filename):
    file_ext = os.path.splitext(filename)[1]
    
    file_content = ''
    if type == src_format.line:
        if file_ext == ".xml":
            file_content = line_data_to_xml(data)
        elif file_ext == ".ini":
            file_content = line_data_to_ini(data)
        else:
            logging.error("unknown file ext %s", file_ext)
            return False
    elif type == src_format.inf:
        if file_ext == ".xml":
            file_content = inf_data_to_xml(data)
        elif file_ext == ".ini":
            file_content = inf_data_to_ini(data)
        else:
            logging.error("unknown file ext %s", file_ext)
            return False
    else:
        logging.error("unknown source format %d"%(type))
        return False
        
    f = codecs.open(filename, "w", "utf-8")
    f.write(file_content)
    f.close()
    return True
    
def format_one_file(filename, output_path):
    if not os.path.isdir(output_path):
        logging.error("dst path must be directory!")
        return False
    try:
        wb = load_workbook(filename = filename)
    except Exception as e:
        logging.error("can not load workbook %s"%(filename))
        return False
    logging.info("now process file %s"%(filename))
    fconf = output_config()
    fconf.from_sheet(wb.get_sheet_by_name("_conf"))
    output_sheets = [wb.get_sheet_by_name(i) for i in wb.get_sheet_names() if i.startswith("_output")]

    for i in fconf.outputs:
        output_file = fconf.outputs[i]
        if src_format.line == fconf.type:
            #check output fields on each output name
            expect_flds = None
            for sheet in output_sheets:
                flds = [d.name for d in [field_descriptor(f.value) for f in sheet.rows[0]] if not d.is_suppressed([i])]
                if None == expect_flds:
                    expect_flds = flds
                elif expect_flds != flds:
                    logging.error("unmatch field description for output %s in sheet %s"%(i, sheet.title))
                    return False

        data = None
        for sheet in output_sheets:
            if src_format.line == fconf.type:
                data = line_data_from_sheet(i, sheet, data)
            elif src_format.inf == fconf.type:
                data = inf_data_from_sheet(i, sheet, data)
            else:
                logging.error("unknown source format %d", fconf.type)
                return False
        write_data_to_file(fconf.type, data, os.sep.join([output_path, output_file]))
    return True

def format_one_dir(dirpath, output_path):
    if not os.path.isdir(output_path):
        logging.error("dst path must be directory!")
        return
    excel_pat = "*.xlsx"
    for root,dirs,files in os.walk(dirpath):
        for filespath in files:
            # only files that directly under dirpath
            if (dirpath != root):
                continue
            
            if (not fnmatch.fnmatch(filespath, excel_pat)):
                continue
                
            fullname = os.path.join(root, filespath)
            format_one_file(fullname, output_path)
            
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s|%(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
    
    parser = argparse.ArgumentParser(description='convert microsoft xlsx files to unicode ini/xml.')
    parser.add_argument('--src', dest='src_path', action='store', default=".", help='specify target dir/file')
    parser.add_argument('--dst', dest='dst_path', action='store', default=".", help='specify output dir/file')
    args = parser.parse_args()
    
    rootpath = args.src_path
    if os.path.isdir(args.src_path):
        format_one_dir(args.src_path, args.dst_path)
    elif os.path.isfile(args.src_path):
        format_one_file(args.src_path, args.dst_path)
    else:
        logging.error("sorry, but i dont know wtf it is :(")