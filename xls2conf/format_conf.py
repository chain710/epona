from openpyxl import load_workbook
import os, fnmatch
import codecs

class format_conf:
    type = "line"
    xml_prefix = None
    ini_prefix = None
    output_forbid = ""
    
    def is_allowed(self, ftype):
        if (None == self.output_forbid):
            return True
        for i in self.output_forbid.split(','):
            if i == ftype:
                return False
        return True
    
def load_format_conf(sheet):
    ret = format_conf()
    for cells in sheet.rows:
        if cells[0].value == 'type':
            ret.type = cells[1].value
        elif cells[0].value == 'xml_prefix':
            ret.xml_prefix = cells[1].value
        elif cells[0].value == 'ini_prefix':
            ret.ini_prefix = cells[1].value
        elif cells[0].value == 'output_forbid':
            ret.output_forbid = cells[1].value
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

def is_xml_node(name):
    if (name.find('.o_xml') >= 0):
        return True
    elif (name.find('.o_') < 0):
        return True
    else:
        return False

def is_ini_node(name):
    if (name.find('.o_ini') >= 0):
        return True
    elif (name.find('.o_') < 0):
        return True
    else:
        return False
        
def cell_value(c):
    if (c.is_date()):
        return c.value.strftime("%Y-%m-%d_%H:%M:%S")
    else:
        return unicode(c.value)
        
def xml_entry(c, d):
    return u"<%s>%s</%s>"%(d, c, d)
        
def to_xml_row_str(desc, row):
    return "<%s>\n%s\n</%s>"%(
        'man', 
        '\n'.join([xml_entry(cell_value(row[i]), node_desc(desc[i].value)) for i in range(0,len(row)) if is_xml_node(desc[i].value)]), 
        'man')

def to_ini_row_str(desc, row):
    return '  '.join([cell_value(row[i]) for i in range(0,len(row)) if is_ini_node(desc[i].value)])

def output_xml(filename, data):
    f = codecs.open(filename, "w", "utf-8")
    f.write(u"<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n")
    f.write(data)
    f.close()
    
def output_ini(filename, data):
    f = codecs.open(filename, "w", "utf-8")
    f.write(data)
    f.close()

def xml_filename(fconf, filename, title):
    if (None == fconf or None == fconf.xml_prefix):
        return "%s.%s.xml"%(filename_prefix(filename), title)
    else:
        return "%s.%s.xml"%(fconf.xml_prefix, title)
        
def ini_filename(fconf, filename, title):
    if (None == fconf or None == fconf.ini_prefix):
        return "%s.%s.ini"%(filename_prefix(filename), title)
    else:
        return "%s.%s.ini"%(fconf.ini_prefix, title)

def ini_description(desc):
    return '#'+'  '.join([node_desc(i.value) for i in desc if is_ini_node(i.value)])

def format_one_sheet(filename, fconf, sheet):
    print "now process sheet %s"%(sheet.title)
    # row 0 must be comment
    sheet_desc = sheet.rows[0]
    #output xml & ini files
    if (fconf != None and fconf.is_allowed('xml')):
        xmlout = "<conf>\n%s\n</conf>"%('\n'.join([to_xml_row_str(sheet_desc, i) for i in sheet.rows[1:]]))
        output_xml(xml_filename(fconf, filename, sheet.title), xmlout)
    if (fconf != None and fconf.is_allowed('ini')):
        print ini_filename(fconf, filename, sheet.title)
        iniout = "%s\n%s"%(ini_description(sheet_desc), '\n'.join([to_ini_row_str(sheet_desc, i) for i in sheet.rows[1:]]))
        output_ini(ini_filename(fconf, filename, sheet.title), iniout)

def format_one_conf(filename):
    wb = load_workbook(filename = filename)
    fconf = None
    for i in wb.get_sheet_names():
        if i == "_conf":
            fconf = load_format_conf(wb.get_sheet_by_name(i))
            
    for i in wb.get_sheet_names():
        if i.find("_") != 0:
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