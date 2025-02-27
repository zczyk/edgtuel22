import pandas as pd
import sys

def csv_to_txt(csv_filename, output_filename, area_name):
    df = pd.read_csv(csv_filename, encoding='utf-8')
    ips = df.iloc[:, 0]
    download_speeds = df.iloc[:, 5]

    with open(output_filename, 'w', encoding='utf-8') as f:
        for i, (ip, speed) in enumerate(zip(ips, download_speeds)):
            f.write(f"{ip}#{area_name}优选IP {i+1}  ↓ {speed}MB/s\n")

csv_to_txt("HKG.csv", "HKG.txt", "中国香港")
csv_to_txt("KHH.csv", "KHH.txt", "中国台湾高雄")
csv_to_txt("NRT.csv", "NRT.txt", "日本东京")
csv_to_txt("LAX.csv", "LAX.txt", "美国洛杉矶")
csv_to_txt("SEA.csv", "SEA.txt", "美国西雅图")
csv_to_txt("SJC.csv", "SJC.txt", "美国圣何塞")