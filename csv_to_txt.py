import pandas as pd
import sys

def csv_to_txt(csv_filename, output_filename, area_name):
    try:
        # 尝试读取 CSV 文件
        df = pd.read_csv(csv_filename, encoding='utf-8')
        ips = df.iloc[:, 0]
        download_speeds = df.iloc[:, 5]

        # 将数据写入 TXT 文件
        with open(output_filename, 'w', encoding='utf-8') as f:
            for i, (ip, speed) in enumerate(zip(ips, download_speeds)):
                f.write(f"{ip}#{area_name} {i+1} ↓ {speed}MB/s\n")
        print(f"成功处理文件: {csv_filename} -> {output_filename}")
    except FileNotFoundError:
        # 如果文件不存在，跳过并提示
        print(f"文件未找到: {csv_filename}，跳过处理。")
    except Exception as e:
        # 捕获其他可能的异常
        print(f"处理文件 {csv_filename} 时发生错误: {e}")

# 调用函数处理文件
csv_to_txt("HKG.csv", "HKG.txt", "中国香港")
csv_to_txt("KHH.csv", "KHH.txt", "中国台湾")
csv_to_txt("NRT.csv", "NRT.txt", "日本东京")
csv_to_txt("LAX.csv", "LAX.txt", "美国洛杉矶")
csv_to_txt("SEA.csv", "SEA.txt", "美国西雅图")
csv_to_txt("SJC.csv", "SJC.txt", "美国圣何塞")