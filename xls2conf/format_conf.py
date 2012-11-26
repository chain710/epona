from openpyxl import load_workbook
import os, fnmatch
import codecs
from sets import Set

class format_conf:
    def __init__(self):
        self.type = "line"
        self.out_confs = {}
    
def load_format_conf(sheet):
    ret = format_conf()
    for cells in sheet.rows:
        if cells[0].value == 'type':
            ret.type = cells[1].value
        elif cells[0].value.startswith('outconf_') and cells[1].value != None:
            ret.out_confs[cells[0].value.split('_', 1)[1]] = cells[1].value
    return ret

def node_desc(name):
    return unicode(name).split('.', 1)[0]
    
    
def is_conf_node(name, fcode):
    opts = name.split('.')
    has_out_spec = False
    for i in opts:
        if 'o_%s'%(fcode) == i:
            return True
        if i.startswith('o_'):
            has_out_spec = True
            
    return not has_out_spec
        
def cell_value(c):
    if (c.is_date()):
        return c.value.strftime("%Y-%m-%d_%H:%M:%S")
    else:
        return unicode(c.value)
        
def xml_entry(c, d):
    return u"<%s>%s</%s>"%(d, c, d)
        
def to_xml_row_str(desc, row, fcode, col_masks):
    return "<%s>\n%s\n</%s>"%(
        'man', 
        '\n'.join([xml_entry(cell_value(row[i]), node_desc(desc[i].value)) 
            for i in range(0,len(row)) if node_desc(desc[i].value) in col_masks and is_conf_node(desc[i].value, fcode)]), 
        'man')

def to_ini_row_str(desc, row, fcode, col_masks):
    return '  '.join([cell_value(row[i]) for i in range(0,len(row)) if node_desc(desc[i].value) in col_masks and is_conf_node(desc[i].value, fcode)])
    
def save_conf_file(filename, data):
    f = codecs.open(filename, "w", "utf-8")
    f.write(data)
    f.close()

def ini_description(desc, fcode):
    return '#'+'  '.join([node_desc(i.value) for i in desc if is_conf_node(i.value, fcode)])

def inf_to_ini(rows, fcode):
    inf_str = ''
    for row in rows:
        if len(row) < 2:
            continue
        k = cell_value(row[0])
        v = cell_value(row[1])
        
        if row[1].value == None:
            inf_str += "[%s]\n"%(k)
        elif is_conf_node(k, fcode):
            inf_str += "%s=%s\n"%(node_desc(k), v)
    return inf_str
    
def inf_to_xml(rows, fcode):
    inf_str = ''
    last_sec = None
    for row in rows:
        if len(row) < 2:
            continue
        k = cell_value(row[0])
        v = cell_value(row[1])
        
        if row[1].value == None:
            if None == last_sec:
                inf_str += "<%s>\n"%(k)
            elif is_conf_node(k, fcode):
                inf_str += "</%s>\n<%s>\n"%(last_sec, k)
            last_sec = k
        elif is_conf_node(k, fcode):
            inf_str += "<%s>%s</%s>\n"%(node_desc(k), v, node_desc(k))
    if last_sec != None:
        inf_str += "</%s>\n"%(last_sec)
    return inf_str
    
def generate_conf_text(file_ext, conf_type, fcode, rows, col_masks):
    if file_ext == ".xml":
        if conf_type == "inf":
            xmlout = inf_to_xml(rows, fcode)
        else:
            xmlout = "%s\n"%('\n'.join([to_xml_row_str(rows[0], i, fcode, col_masks) for i in rows[1:]]))
        return xmlout
    elif file_ext == ".ini":
        if conf_type == "inf":
            iniout = inf_to_ini(rows, fcode)
        else:
            iniout = "%s\n"%('\n'.join([to_ini_row_str(rows[0], i, fcode, col_masks) for i in rows[1:]]))
        #output_ini(confname, iniout)
        return iniout
    else:
        print "unknown file ext %s"%(file_ext)
        return ""

def format_one_conf(filename):
    wb = load_workbook(filename = filename)
    fconf = None
    print "now process xlsx file %s"%(filename)
    fconf = load_format_conf(wb.get_sheet_by_name("_conf"))
    col_masks = None
    def_sheet = None
    if fconf.type == "line":
        # get default sheet
        def_sheet = wb.get_sheet_by_name("_output")
        col_masks = Set([node_desc(i.value) for i in def_sheet.rows[0]])
    
    outconf_content = {}
    for i in wb.get_sheet_names():
        sheet = wb.get_sheet_by_name(i)
        if i.startswith("_output"):
            for fcode in fconf.out_confs:
                confname = fconf.out_confs[fcode]
                file_ext = os.path.splitext(confname)[1]
                if not outconf_content.has_key(confname):
                    outconf_content[confname] = ""
                outconf_content[confname] += generate_conf_text(file_ext, fconf.type, fcode, sheet.rows, col_masks)

    for fcode in fconf.out_confs:
        confname = fconf.out_confs[fcode]
        file_ext = os.path.splitext(confname)[1]
        if file_ext == ".xml":
            outconf_content[confname] = u"<?xml version='1.0' encoding='UTF-8' standalone='yes'?><conf>\n%s\n</conf>\n"%(outconf_content[confname])
        elif file_ext == ".ini" and fconf.type == "line":
            outconf_content[confname] = u"%s\n%s"%(ini_description(def_sheet.rows[0], fcode), outconf_content[confname])
        save_conf_file(confname, outconf_content[confname])

if __name__ == '__main__':
    rootpath = "."
    excel_pat = "*.xlsx"
    for root,dirs,files in os.walk(rootpath):
        for filespath in files:
            # process file under root only
            if (rootpath != root):
                continue
            
            if (not fnmatch.fnmatch(filespath, excel_pat)):
                continue
                
            fullname = os.path.join(root, filespath)
            format_one_conf(fullname)