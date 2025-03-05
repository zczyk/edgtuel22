import pandas as pd
import os

def csv_to_txt(csv_filename,output_dir,area_name):
    df = pd.read_csv(csv_filename, encoding='utf-8')
    ips = df.iloc[:, 0]
    download_speeds = df.iloc[:, 5]
    output_filename = csv_filename.replace(".csv", ".txt")
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (ip, speed) in enumerate(zip(ips, download_speeds)):
            f.write(f"{ip}#{area_name} {i+1} ↓ {speed}MB/s\n")

# 简化函数调用
csv_to_txt("HKG.csv","SpeedTest","中国香港")
csv_to_txt("NRT.csv","SpeedTest","日本东京")
csv_to_txt("LAX.csv","SpeedTest","美国洛杉矶")
csv_to_txt("SEA.csv","SpeedTest","美国西雅图")
csv_to_txt("SJC.csv","SpeedTest","美国圣何塞")