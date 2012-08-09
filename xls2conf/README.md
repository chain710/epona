依赖：
python 2.7.2
openpyxl

当前支持的输出文件类型：
1.ini
2.xml

xlsx编辑：
1.第一行必须是注释
    注释格式为 注释名称.o_输出类型 或者 注释名称
    比如 item_name.o_xml 表示该字段(item_name)将会输出到xml格式的配置中
    如果仅仅是item_name，则表示该字段将输出到所有格式的配置中
    
2.表名称
    表名称影响输出的配置文件名
    默认输出的配置文件名格式为：xlsx前缀.表名称.文件类型
    比如item.xlsx的dev表默认输出的xml文件名为item.dev.xml
    如果表名称以_开头，则不会输出（比如_conf）
    
3.输出配置
    该脚本把名称为_conf的表作为输出配置，表内容如下（可以参考template.xlsx）
    type	配置类型，暂时只支持line一种
    xml_prefix	输出xml的配置文件前缀，如果配置项非空(比如test)，则输出的xml文件名为：test.表名称.xml
    ini_prefix	输出ini的配置文件前缀，如果配置项非空(比如test)，则输出的ini文件名为：test.表名称.ini
    output_forbid	禁止输出的配置类型，用,隔开。如果不想输出任何一种配置，填ini,xml，如果不想输出xml，填xml

其他：
    表名称使用场景
    1.开发环境区别，比如dev表示测试环境，run表示运营环境等
    2.运行平台区别，比如tx表示腾讯平台，renren表示人人平台等等