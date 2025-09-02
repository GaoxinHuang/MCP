#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新西兰公寓投资买家计算器 - 2025年版
专为买家设计：根据目标收益率计算合理购买价格
仅生成Excel文件（包含自动计算公式）
"""

import xlsxwriter
from datetime import datetime


def create_buyer_data_for_excel():
    """为Excel创建原始数据（包含手动输入的管理费和维修预备金）"""
    
    properties = [
        {
            'address': 'Unit 12/45 Queen Street, Auckland CBD',
            'weekly_rent': 650,
            'body_corp': 4500,
            'rates': 2800,
            'insurance': 1200,
            'property_management': 1800,  # 手动输入
            'maintenance_reserve': 900,   # 手动输入
            'build_year': 2015,
            'rv': 520000,
            'asking_layout': '$475000 / 1卧1卫+书房',
            'rental_status': '长期租约至2026年3月',
            'link': 'https://example.com/property1',
            'notes': '市中心位置优越，近天空塔'
        },
        {
            'address': 'Apt 8/123 Lambton Quay, Wellington',
            'weekly_rent': 550,
            'body_corp': 3800,
            'rates': 2200,
            'insurance': 1100,
            'property_management': 1600,  # 手动输入
            'maintenance_reserve': 800,   # 手动输入
            'build_year': 2012,
            'rv': 420000,
            'asking_layout': '$395000 / 2卧1卫',
            'rental_status': '月租约，租客稳定',
            'link': 'https://example.com/property2',
            'notes': '政府区域，公交便利'
        },
        {
            'address': 'Unit 15/78 Cashel Street, Christchurch',
            'weekly_rent': 420,
            'body_corp': 2800,
            'rates': 1800,
            'insurance': 950,
            'property_management': 1200,  # 手动输入
            'maintenance_reserve': 600,   # 手动输入
            'build_year': 2018,
            'rv': 340000,
            'asking_layout': '$310000 / 1卧1卫',
            'rental_status': '空置待租',
            'link': 'https://example.com/property3',
            'notes': '重建区新建筑，现代化设施'
        },
        {
            'address': 'Apt 6/234 Tay Street, Hamilton',
            'weekly_rent': 380,
            'body_corp': 2400,
            'rates': 1600,
            'insurance': 850,
            'property_management': 1100,  # 手动输入
            'maintenance_reserve': 550,   # 手动输入
            'build_year': 2010,
            'rv': 300000,
            'asking_layout': '$275000 / 2卧1卫',
            'rental_status': '已出租，租期6个月',
            'link': 'https://example.com/property4',
            'notes': '近大学，学生租赁需求稳定'
        },
        {
            'address': 'Unit 22/156 Riccarton Road, Christchurch',
            'weekly_rent': 440,
            'body_corp': 3200,
            'rates': 1900,
            'insurance': 1000,
            'property_management': 1300,  # 手动输入
            'maintenance_reserve': 650,   # 手动输入
            'build_year': 2016,
            'rv': 360000,
            'asking_layout': '$335000 / 1卧1卫+停车位',
            'rental_status': '长期租约至2025年12月',
            'link': 'https://example.com/property5',
            'notes': '近商场和大学，包含停车位'
        }
    ]
    
    # 转换为Excel所需的格式
    excel_data = []
    for prop in properties:
        excel_data.append({
            'Property Address': prop['address'],
            'Weekly Rent (NZD)': prop['weekly_rent'],
            'Body Corp Fee (Annual)': prop['body_corp'],
            'Council Rates (Annual)': prop['rates'],
            'Insurance (Annual)': prop['insurance'],
            'Property Management (Annual)': prop['property_management'],
            'Maintenance Reserve (Annual)': prop['maintenance_reserve'],
            'Build Year': prop['build_year'],
            'RV (Government Valuation)': prop['rv'],
            'Asking Price/Layout': prop['asking_layout'],
            'Rental Status': prop['rental_status'],
            'Property Link': prop['link'],
            'Notes': prop['notes']
        })
    
    return excel_data


def create_buyer_excel(data, filename):
    """创建买家版Excel文件 - 使用公式而非预计算值"""
    workbook = xlsxwriter.Workbook(filename)
    
    # 添加格式
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    money_format = workbook.add_format({'num_format': '$#,##0'})
    highlight_format = workbook.add_format({
        'num_format': '$#,##0',
        'bg_color': '#FFE6CC',
        'bold': True
    })
    
    # 创建主计算表
    worksheet = workbook.add_worksheet('买家投资计算器')
    
    # 表头
    headers = [
        '物业地址', '每周租金 (NZD)', '年租金收入 (NZD)',
        'Body Corp年费', '市政费率年费', '房东保险年费', '物业管理费年费',
        '维修预备金年费', '总年度支出', '净年收入',
        '合理购买价@6%', '合理购买价@6.5%', '合理购买价@7%', '合理购买价@8%',
        '建造年份', '政府估值 (RV)', '咨询价格/格局', '出租情况', '物业链接', '备注'
    ]
    
    # 写入表头
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
    
    # 写入数据和公式
    for row, item in enumerate(data, 1):
        # 基础数据列
        worksheet.write(row, 0, item['Property Address'])
        worksheet.write(row, 1, item['Weekly Rent (NZD)'], money_format)
        
        # 年租金收入公式 = 每周租金 × 48
        # 年租金 = 周租金 × 46周（考虑6周空置期）
        worksheet.write_formula(row, 2, f'=B{row+1}*46', money_format)
        
        # 固定费用
        worksheet.write(row, 3, item['Body Corp Fee (Annual)'], money_format)
        worksheet.write(row, 4, item['Council Rates (Annual)'], money_format)
        worksheet.write(row, 5, item['Insurance (Annual)'], money_format)
        
        # 手动输入的费用（用户可以修改）
        worksheet.write(row, 6, item['Property Management (Annual)'], money_format)
        worksheet.write(row, 7, item['Maintenance Reserve (Annual)'], money_format)
        
        # 总年度支出公式 = SUM(D:H列)
        worksheet.write_formula(row, 8, f'=SUM(D{row+1}:H{row+1})', money_format)
        
        # 净年收入公式 = 年租金 - 总支出
        worksheet.write_formula(row, 9, f'=C{row+1}-I{row+1}', money_format)
        
        # 关键：合理购买价格公式 = 净年收入 / 目标收益率
        worksheet.write_formula(row, 10, f'=J{row+1}/0.06', highlight_format)    # 6%
        worksheet.write_formula(row, 11, f'=J{row+1}/0.065', highlight_format)   # 6.5%
        worksheet.write_formula(row, 12, f'=J{row+1}/0.07', highlight_format)    # 7%
        worksheet.write_formula(row, 13, f'=J{row+1}/0.08', highlight_format)    # 8%
        
        # 信息列（不参与计算）
        worksheet.write(row, 14, item['Build Year'])
        worksheet.write(row, 15, item['RV (Government Valuation)'], money_format)
        worksheet.write(row, 16, item['Asking Price/Layout'])
        worksheet.write(row, 17, item['Rental Status'])
        worksheet.write(row, 18, item['Property Link'])
        worksheet.write(row, 19, item['Notes'])
    
    # 调整列宽
    worksheet.set_column('A:A', 40)  # 地址列
    worksheet.set_column('B:J', 15)  # 租金和费用列
    worksheet.set_column('K:N', 18)  # 目标购买价格列（突出显示）
    worksheet.set_column('O:O', 10)  # 建造年份
    worksheet.set_column('P:P', 15)  # 政府估值
    worksheet.set_column('Q:Q', 25)  # 咨询价格/格局
    worksheet.set_column('R:R', 20)  # 出租情况
    worksheet.set_column('S:S', 30)  # 物业链接
    worksheet.set_column('T:T', 30)  # 备注
    
    # 添加说明工作表
    info_sheet = workbook.add_worksheet('使用说明')
    
    info_text = [
        '买家投资回报率计算器 - 2025年版（公寓/Unit/Townhouse专用）',
        '',
        '🎯 买家专用功能：',
        '• 根据您的目标净收益率自动计算合理购买价格',
        '• 专注公寓、Unit、Townhouse投资分析',
        '• 无需猜测，直接知道应该出价多少',
        '• 避免过高出价，确保投资回报达标',
        '',
        '💰 目标收益率说明：',
        '• 6%：保守型投资者，追求稳定回报',
        '• 6.5%：平衡型投资者，适中风险收益比',
        '• 7%：积极型投资者，追求较高回报',
        '• 8%：激进型投资者，高风险高回报',
        '',
        '📊 如何使用：',
        '1. 修改物业管理费和维修预备金（手动输入）',
        '2. 选择您的目标净收益率（建议6.5-7%）',
        '3. 查看对应的"合理购买价"列',
        '4. 将此价格作为您的最高出价参考',
        '5. 考虑RV估值、建造年份等因素微调',
        '',
        '✏️ 可修改参数：',
        '• 每周租金：根据市场情况调整',
        '• 物业管理费：可以手动输入实际金额',
        '• 维修预备金：根据建筑年份和状况调整',
        '• 其他费用：Body Corp、市政费、保险等',
        '',
        '⚠️ 重要提醒：',
        '• 计算基于46周出租（已考虑6周空置期）',
        '• 物业管理费和维修预备金需要手动输入',
        '• 价格为税前净收益率，需考虑个人所得税',
        '• 建议在计算价格基础上再留10-15%安全边际',
        '',
        '🏠 投资决策流程：',
        '1. 确定目标收益率',
        '2. 输入准确的管理费用',
        '3. 查看合理购买价',
        '4. 对比咨询价格和RV',
        '5. 评估建造年份和出租状况',
        '6. 制定出价策略',
        '',
        '💡 实用技巧：',
        '• 物业管理费：一般为年租金的5-8%',
        '• 维修预备金：新建筑2-3%，老建筑3-5%',
        '• 如果RV > 合理购买价，需要很大折让才值得投资',
        '• 空置物业可以更接近目标价格出价',
        '• 长期租约物业风险较低，可接受稍高价格',
        '• 老建筑需预留额外维修成本',
        '',
        f'文件创建时间：{datetime.now().strftime("%Y年%m月%d日")}',
        '专为新西兰买家设计，助您做出明智投资决策'
    ]
    
    for row, text in enumerate(info_text):
        info_sheet.write(row, 0, text)
    
    info_sheet.set_column('A:A', 60)
    
    workbook.close()


if __name__ == "__main__":
    # 生成Excel文件（使用公式）
    print("正在生成Excel文件（包含自动计算公式）...")
    excel_data = create_buyer_data_for_excel()
    create_buyer_excel(excel_data, 'Buyer_Investment_Calculator.xlsx')
    
    print("\n🎯 买家专用投资计算器已创建！")
    print("\n📁 生成文件:")
    print("• Buyer_Investment_Calculator.xlsx (Excel公式版本)")
    
    print("\n✨ 重要说明:")
    print("• 使用公式自动计算，可以修改参数")
    print("• 您可以在Excel中修改周租金、费用等，公式会自动重算合理购买价")
    
    print("\n📊 Excel公式说明:")
    print("• 年租金 = 周租金 × 46")
    print("• 物业管理费 = 手动输入金额（可修改）")
    print("• 维修预备金 = 手动输入金额（可修改）")
    print("• 合理购买价@X% = 净年收入 ÷ X%")
    
    print("\n� 投资建议:")
    print("• 打开Excel文件查看每个物业的合理购买价格")
    print("• 根据您的风险偏好选择目标收益率（建议6.5-7%）")
    print("• 将计算结果作为出价参考，结合市场情况做决策")
    print("• 建议在计算价格基础上再留10-15%安全边际")
