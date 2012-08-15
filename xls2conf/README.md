依赖：
python 2.7.2
openpyxl

当前支持的输出文件类型：
1. ini
2. xml

xlsx编辑：
1.第一行必须是注释
    注释格式为 注释名称.o_输出别名 或者 注释名称
    比如 item_name.o_a 表示该字段(item_name)将会输出到outconf_a指定的配置中
    如果仅仅是item_name，则表示该字段将输出到所有格式的配置中
    
2.表名称
    _output 输出表
    _conf 配置表
    
3.输出配置
    该脚本把名称为_conf的表作为输出配置，表内容如下（可以参考template.xlsx）
    type	配置类型，暂时只支持line一种
    outconf_%s 输出文件，%s部分为输出别名，用于1中的注释行