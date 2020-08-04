# excel_convert
excel_convert是一个代码生成工具，用于将Excel数据表中的结构信息转换成对应的C++和C#代码，同时将表中的数据序列化到一个文件中。
支持以下特性：
- 多文件、多数据表
- 多种序列化类型
- 多种数据类型
- 支持struct等复杂类型
- 支持C++和C#使用不同的配置
- 支持自动定义基类

### 支持的序列化类型
- 二进制
- 类似thrift的支持向后兼容的二进制格式
- XML

### 支持的数据类型
- bool
- int32
- float
- string
- array
- list
- set
- map
- enum
- struct
