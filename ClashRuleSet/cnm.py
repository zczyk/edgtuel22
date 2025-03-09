import os

def add_prefix_suffix_to_file(filepath):
    """
    给指定文件的每一行添加前缀 "  - '" 和后缀 "'"。

    Args:
        filepath (str): 文件的路径。
    """
    try:
        # 读取文件内容
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 修改每一行
        modified_lines = ["  - '" + line.rstrip() + "'\n" for line in lines]

        # 将修改后的内容写回文件
        with open(filepath, 'w', encoding='utf-8') as file:
            file.writelines(modified_lines)

        print(f"文件 {filepath} 已成功修改。")

    except FileNotFoundError:
        print(f"错误：文件 {filepath} 未找到。")
    except Exception as e:
        print(f"发生错误：{e}")

# 获取文件路径
file_path = input("请输入文件路径：")

# 调用函数进行处理
add_prefix_suffix_to_file(file_path)