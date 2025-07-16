import os
import re
import mimetypes
import webbrowser
import base64
import csv
import json
from collections import Counter
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

mcp = FastMCP('MCP',log_level="ERROR")
# 安全目录配置
SAFE_BASE_DIR = r"D:\WorkSpace\mcp-server\Resource"

# 初始化安全目录
if not os.path.exists(SAFE_BASE_DIR):
    os.makedirs(SAFE_BASE_DIR)

def validate_path(path: str) -> str:
    """验证路径是否在安全目录内"""
    full_path = os.path.abspath(path)
    if not full_path.startswith(os.path.abspath(SAFE_BASE_DIR)):
        raise PermissionError("访问路径超出安全范围")
    return full_path

@mcp.tool()
def read_file(file_path: str, file_name: str) -> str:
    """
    读取文本文件内容
    
    功能:
        1. 只读取文本文件内容
        2. 支持多种文本格式
        3. 自动检测文件编码
    
    参数:
        file_path: 文件所在目录绝对路径
        file_name: 目标文件名
    
    返回:
        文件内容字符串或错误信息
    """
    try:
        full_dir = validate_path(file_path)
        full_path = validate_path(os.path.join(full_dir, file_name))
        
        if not os.path.isfile(full_path):
            return f"错误: 文件不存在 - {file_name}"
        
        # 判断文件类型
        mime_type, _ = mimetypes.guess_type(full_path)
        text_types = [
            'text/', 
            'application/json', 
            'application/xml', 
            'application/javascript',
            'application/x-python',
            'application/x-sh',
            'application/x-csv',
            'application/x-httpd-php',
            'application/xhtml+xml'
        ]
        
        # 检查是否是文本文件
        is_text_file = (
            mime_type and 
            any(mime_type.startswith(t) for t in text_types)
        )
        
        # 如果没有MIME类型信息，检查文件扩展名
        if not is_text_file:
            text_extensions = [
                '.txt', '.log', '.csv', '.json', '.xml', '.yaml', 
                '.ini', '.conf', '.py', '.js', '.html', '.css', '.md'
            ]
            _, ext = os.path.splitext(full_path)
            is_text_file = ext.lower() in text_extensions
        
        if not is_text_file:
            return f"错误: 不支持的文件类型 - {mime_type or '未知'}"
        
        # 尝试自动检测编码
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return f"读取错误: {str(e)}"
        
        return "错误: 无法解码文件内容"
    
    except PermissionError as pe:
        return f"安全错误: {str(pe)}"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.tool()
def write_file(file_path: str, content: str, mode: str = 'w') -> str:
    """
    安全写入文件 - 支持多种写入模式
    
    功能:
        1. 创建新文件或追加/覆盖现有文件
        2. 自动创建缺失目录
        3. 支持文本和Base64内容写入
    
    参数:
        file_path: 目标文件路径
        content: 要写入的内容
        mode: 写入模式 (w=覆盖, a=追加, wb=二进制写入)
    
    返回:
        操作结果消息
    """
    full_path = validate_path(file_path)
    dir_path = os.path.dirname(full_path)
    
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    try:
        if mode == 'wb':
            # 二进制写入
            with open(full_path, 'wb') as f:
                f.write(base64.b64decode(content))
        else:
            # 文本写入
            with open(full_path, mode, encoding='utf-8') as f:
                f.write(content)
        return f"成功写入文件: {os.path.basename(full_path)}"
    except Exception as e:
        return f"写入错误: {str(e)}"

@mcp.tool()
def analyze_text(file_path: str) -> dict:
    """
    文本文件分析 - 生成内容统计信息
    
    功能:
        1. 统计字符数、单词数、行数
        2. 识别常用词汇
        3. 检测文件编码
    
    参数:
        file_path: 文本文件路径
    
    返回:
        包含分析结果的字典
    """
    full_path = validate_path(file_path)
    
    if not os.path.isfile(full_path):
        return {"error": "文件不存在"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 基础统计
            char_count = len(content)
            word_count = len(re.findall(r'\w+', content))
            line_count = len(content.splitlines())
            
            # 词汇分析
            words = re.findall(r'\b\w{4,}\b', content.lower())
            word_freq = Counter(words).most_common(10)
            
            return {
                "file": os.path.basename(full_path),
                "characters": char_count,
                "words": word_count,
                "lines": line_count,
                "top_words": word_freq,
                "encoding": "UTF-8"
            }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def analyze_data(file_path: str, file_name: str, output_dir: str) -> str:
    """
    执行数据的全面分析并将图表保存到指定目录
    
    参数:
        file_path (str): 数据文件路径
        file_name (str): 数据文件名
        output_dir (str): 图表保存目录
        
    返回:
        str: 分析结果摘要，包含图表保存路径
    
    功能:
        1. 读取并清洗数据
        2. 显示数据统计摘要
        3. 可视化数据的分布并保存图表
        4. 分析数据之间的关系并保存图表
    """
    try:
        
        # 构建完整文件路径
        absolute_path = os.path.join(file_path, file_name)
        if not os.path.isfile(absolute_path):
            raise FileNotFoundError(f"文件不存在: {absolute_path}")
        
        # 读取数据
        data = pd.read_csv(absolute_path)
        data = data.dropna()
        
        # 准备结果信息
        result_info = f"数据分析完成: {file_name}\n"
        result_info += f"数据行数: {len(data)}\n"
        result_info += f"数据列数: {len(data.columns)}\n"
        
        # 数据统计摘要
        stats = data.describe().to_string()
        result_info += "\n统计摘要:\n" + stats + "\n"
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 图表1: 房价分布图
        plt.figure(figsize=(10, 6))
        sns.histplot(data['price'], kde=True)
        plt.title('房价分布图')
        dist_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_price_distribution.png")
        plt.savefig(dist_path, bbox_inches='tight', dpi=150)
        plt.close()
        result_info += f"\n房价分布图已保存至: {dist_path}"
        
        # 图表2: 房间数与房价关系图
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='rooms', y='price', data=data)
        plt.title('房间数与房价关系图')
        scatter_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_rooms_vs_price.png")
        plt.savefig(scatter_path, bbox_inches='tight', dpi=150)
        plt.close()
        result_info += f"\n房间数与房价关系图已保存至: {scatter_path}"
        
        # 图表3: 不同地区的房价箱线图
        plt.figure(figsize=(12, 8))
        sns.boxplot(x='location', y='price', data=data)
        plt.title('不同地区的房价箱线图')
        plt.xticks(rotation=45)
        boxplot_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_location_boxplot.png")
        plt.savefig(boxplot_path, bbox_inches='tight', dpi=150)
        plt.close()
        result_info += f"\n不同地区的房价箱线图已保存至: {boxplot_path}"
        
        # 可选: 保存统计摘要到文件
        stats_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_statistics.txt")
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(stats)
        result_info += f"\n统计摘要已保存至: {stats_path}"
        
        return result_info
        
    except Exception as e:
        # 捕获并返回详细错误信息
        error_msg = f"分析失败: {str(e)}\n"
        error_msg += f"文件路径: {file_path}\n"
        error_msg += f"文件名: {file_name}"
        return error_msg
@mcp.tool()
def convert_to_html(file_path: str, style: str = "default") -> str:
    """
    文件内容转HTML展示 - 支持多种格式
    
    功能:
        1. 文本文件：保留格式和换行
        2. CSV文件：转换为表格
        3. JSON文件：格式化展示
        4. 支持自定义样式主题
    
    参数:
        file_path: 源文件路径
        style: 样式主题 (default, dark, minimal)
    
    返回:
        HTML字符串
    """
    full_path = validate_path(file_path)
    
    if not os.path.isfile(full_path):
        return "<p>错误: 文件不存在</p>"
    
    try:
        # 获取文件内容
        content = read_file(os.path.dirname(full_path), os.path.basename(full_path))
        if content.startswith("错误:"):
            return f"<p>{content}</p>"
        
        # 根据文件类型处理
        ext = os.path.splitext(full_path)[1].lower()
        
        # CSS样式定义
        styles = {
            "default": """
                body { font-family: Arial, sans-serif; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; }
                th { background-color: #f2f2f2; }
                pre { background-color: #f5f5f5; padding: 15px; }
            """,
            "dark": """
                body { font-family: Arial, sans-serif; background-color: #333; color: #fff; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #555; padding: 8px; }
                th { background-color: #444; }
                pre { background-color: #222; padding: 15px; }
            """,
            "minimal": """
                body { font-family: Arial, sans-serif; }
                table { border: none; width: 100%; }
                th, td { padding: 4px; }
                th { text-align: left; }
                pre { padding: 5px; }
            """
        }
        
        css = styles.get(style, styles["default"])
        
        # 处理不同类型文件
        if ext == '.txt':
            # 纯文本处理
            formatted = content.replace('\n', '<br>').replace(' ', '&nbsp;')
            html_content = f"<pre>{formatted}</pre>"
        
        elif ext == '.csv':
            # CSV转表格
            csv_data = list(csv.reader(content.splitlines()))
            table_rows = []
            
            # 处理表头
            headers = csv_data[0]
            table_rows.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
            
            # 处理数据行
            for row in csv_data[1:]:
                table_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
            
            html_content = f"<table>{''.join(table_rows)}</table>"
        
        elif ext == '.json':
            # JSON格式化
            try:
                json_data = json.loads(content)
                formatted_json = json.dumps(json_data, indent=2)
                formatted_json = formatted_json.replace('\n', '<br>').replace(' ', '&nbsp;')
                html_content = f"<pre>{formatted_json}</pre>"
            except json.JSONDecodeError:
                html_content = "<pre>无效的JSON格式</pre>"
        
        else:
            # 默认处理
            html_content = f"<pre>{content}</pre>"
        
        # 构建完整HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{os.path.basename(full_path)}</title>
            <style>{css}</style>
        </head>
        <body>
            <h2>{os.path.basename(full_path)}</h2>
            {html_content}
        </body>
        </html>
        """
    
    except Exception as e:
        return f"<p>转换错误: {str(e)}</p>"

@mcp.tool()
def open_html_in_browser(file_path: str) ->str:
    """
    用系统默认浏览器打开HTML文件
    
    参数:
        file_path: HTML文件的完整路径
    返回:
        html打开结果
    """
    # 确保文件存在
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 确保是HTML文件
    if not file_path.lower().endswith(('.html', '.htm')):
        raise ValueError("文件必须是HTML格式")
    
    # 转换为绝对路径
    absolute_path = os.path.abspath(file_path)
    
    # 使用默认浏览器打开
    webbrowser.open('file://' + absolute_path)
    return f"已在浏览器中打开: {os.path.basename(file_path)}"

@mcp.tool()
def file_diff(file1: str, file2: str) -> List[Tuple[int, str, str]]:
    """
    文件差异比较 - 行级对比
    
    功能:
        1. 比较两个文本文件的差异
        2. 显示不同行内容
        3. 行号标注
    
    参数:
        file1: 第一个文件路径
        file2: 第二个文件路径
    
    返回:
        差异行列表 (行号, 文件1内容, 文件2内容)
    """
    file1_full = validate_path(file1)
    file2_full = validate_path(file2)
    
    if not os.path.isfile(file1_full):
        return [(-1, "错误: 文件1不存在", "")]
    if not os.path.isfile(file2_full):
        return [(-1, "", "错误: 文件2不存在")]
    
    try:
        with open(file1_full, 'r') as f1, open(file2_full, 'r') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
        
        diff = []
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i].strip() if i < len(lines1) else ""
            line2 = lines2[i].strip() if i < len(lines2) else ""
            
            if line1 != line2:
                diff.append((i+1, line1, line2))
        
        return diff
    except Exception as e:
        return [(-1, str(e), "")]

if __name__ == "__main__":
    mcp.run(transport="stdio")