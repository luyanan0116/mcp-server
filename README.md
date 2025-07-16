# mcp-server
python代码+cherry studio客户端实现mcp服务

# 功能概览

## 📄 1. 文件读取 (read_file)

自动检测文件编码

支持多种文本格式（TXT, CSV, JSON等）

返回文件内容字符串

```
python
def read_file(file_path: str, file_name: str) -> str:
```

## 💾 2. 文件写入 (write_file)

支持多种写入模式：覆盖('w')、追加('a')、二进制('wb')

自动创建缺失目录

支持文本和Base64内容写入

```
python
def write_file(file_path: str, content: str, mode: str = 'w') -> str:
```

## 📊 3. 文本分析 (analyze_text)

统计字符数、单词数和行数

识别常用词汇

自动检测文件编码

返回包含分析结果的字典

```
python
def analyze_text(file_path: str) -> dict:
```

## 📈 4. 数据分析 (analyze_data)

执行数据的全面分析

生成可视化图表并保存

返回包含图表路径的分析摘要

```
python
def analyze_data(file_path: str, file_name: str, output_dir: str) -> str:
```

## 🌐 5. HTML转换 (convert_to_html)

将文件内容转换为HTML格式

支持文本、CSV和JSON格式

提供多种样式主题：default, dark, minimal

保留原始格式和结构

```
python
def convert_to_html(file_path: str, style: str = "default") -> str:
```

## 🌍 6. 浏览器打开 (open_html_in_browser)

使用系统默认浏览器打开HTML文件

返回操作结果

## 安装与依赖

### 系统要求

- Python 3.12+

### 依赖

MCP官方推荐使用uv管理python包，所以优先下载uv

```
pip install uv
```

然后配置环境变量，在powerShell中使用如下命令

```
(base) PS C:\Users\admin> uv --version
uv 0.7.13 (62ed17b23 2025-06-12)
```

就代表uv安装成功

### uv 进行项目管理

建项目的时候也要用 uv 来进行初始化。

```
#初始化项目
uv init myproject
```

```
#进入项目文件
cd my_project

# 创建虚拟环境
uv venv

#激活uv虚拟环境
.venv\Scripts\activate

#添加mcp相关依赖
uv add mcp[cli]
```

项目就创建完成了

### 用uv安装项目中的依赖

在uv中安装数据分析相关的包

```
uv pip install pandas,seaborn,matplotlib
```

### Cline Mcp配置

```
{

 "mcpServers": {

  "mcp-demo": {

   "command": "uv",

   "args": [

    "--directory",

    "xxx\\xxx\\your mcp-server path",

    "run",

    "main.py"

   ]

  }

 }

}
```

