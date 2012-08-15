from openpyxl import load_workbook
import os, fnmatch
import codecs

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
            ret.out_confs['_'.join(cells[0].value.split('_')[1:])] = cells[1].value
    return ret

def node_desc(name):
    pos = name.find('.')
    if pos > 0:
        return name[:pos]
    else:
        return name
        
def filename_prefix(name):
    pos = name.rfind('/')
    if pos < 0:
        return node_desc(name)
    else:
        return node_desc(name[pos+1:])
        
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
        
def to_xml_row_str(desc, row, fcode):
    return "<%s>\n%s\n</%s>"%(
        'man', 
        '\n'.join([xml_entry(cell_value(row[i]), node_desc(desc[i].value)) for i in range(0,len(row)) if is_conf_node(desc[i].value, fcode)]), 
        'man')

def to_ini_row_str(desc, row, fcode):
    return '  '.join([cell_value(row[i]) for i in range(0,len(row)) if is_conf_node(desc[i].value, fcode)])

def output_xml(filename, data):
    f = codecs.open(filename, "w", "utf-8")
    f.write(u"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n")
    f.write(data)
    f.close()
    
def output_ini(filename, data):
    f = codecs.open(filename, "w", "utf-8")
    f.write(data)
    f.close()

def ini_description(desc, fcode):
    return '#'+'  '.join([node_desc(i.value) for i in desc if is_conf_node(i.value, fcode)])

def format_one_sheet(filename, fconf, sheet):
    # row 0 must be comment
    sheet_desc = sheet.rows[0]
    
    #output conf files
    if (fconf == None):
        return
        
    for fcode in fconf.out_confs:
        confname = fconf.out_confs[fcode]
        file_ext = os.path.splitext(confname)[1]
        if file_ext == ".xml":
            xmlout = "<conf>\n%s\n</conf>"%('\n'.join([to_xml_row_str(sheet_desc, i, fcode) for i in sheet.rows[1:]]))
            output_xml(confname, xmlout)
            print "output xml %s"%(confname)
        elif file_ext == ".ini":
            iniout = "%s\n%s"%(ini_description(sheet_desc, fcode), '\n'.join([to_ini_row_str(sheet_desc, i, fcode) for i in sheet.rows[1:]]))
            output_ini(confname, iniout)
            print "output ini %s"%(confname)

def format_one_conf(filename):
    wb = load_workbook(filename = filename)
    fconf = None
    print "now process xlsx file %s"%(filename)
    for i in wb.get_sheet_names():
        if i == "_conf":
            fconf = load_format_conf(wb.get_sheet_by_name(i))

    for i in wb.get_sheet_names():
        if i == "_output":
            format_one_sheet(filename, fconf, wb.get_sheet_by_name(i))

if __name__ == '__main__':
    rootpath = "./"
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