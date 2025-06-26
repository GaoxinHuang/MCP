import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_csv('data/nvda_stock.csv')

# 计算统计信息
stats = df.describe()

# 生成报告
with open('NVDA_Stock_Report.txt', 'w') as f:
    f.write("NVDA Stock Report (2023-2024)\n")
    f.write("="*30 + "\n")
    f.write(f"Data points: {len(df)}\n")
    f.write(f"Average price: {stats['Close']['mean']:.2f}\n")
    f.write(f"Max price: {stats['Close']['max']:.2f}\n")
    f.write(f"Min price: {stats['Close']['min']:.1f}\n")
    f.write(f"Standard deviation: {stats['Close']['std']:.2f}\n")

# 生成图表
plt.figure(figsize=(12, 6))
plt.plot(df['Close'])
plt.title('NVDA Stock Price Trend')
plt.xlabel('Date')
plt.ylabel('Price')
plt.grid()
plt.savefig('NVDA_Stock_Chart.png')
plt.show()