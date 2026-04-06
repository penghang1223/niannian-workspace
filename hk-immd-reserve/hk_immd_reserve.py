#!/usr/bin/env python3
"""
香港入境事务处身份证预约工具
运行环境：macOS
依赖：pip3 install browser-use

使用方法：
    python3 hk_immd_reserve.py
"""

import asyncio
from browser_use import Agent


async def book_hk_immd_appointment(
    name: str,
    id_number: str,
    phone: str,
    email: str,
    office: str = "灣仔",
    date: str = None,
    time: str = None,
    headed: bool = True,
):
    """
    预约香港身份证办理

    Args:
        name: 申请人姓名（繁体中文）
        id_number: 身份证号码（如 A1234567）
        phone: 电话号码（如 91234567）
        email: 电邮地址
        office: 办事处名称（灣仔/觀塘/長沙灣/荃灣/沙田/大埔/屯門/元朗）
        date: 预约日期（可选，不填选最早）
        time: 预约时间（可选，不填选最早）
        headed: 是否显示浏览器窗口（调试用）
    """

    task = f"""
    完成香港入境事务处身份证预约，步骤如下：

    1. 打开网址：https://system.es2.immd.gov.hk/smartics2-client/ropbooking/zh-HK/eservices/makeAppointment/term

    2. 选择服务类型：申领身份证

    3. 选择办事处：{office}

    4. 选择日期：{date if date else "最早的可用日期"}

    5. 选择时间：{time if time else "最早的可用时间"}

    6. 填写申请人信息：
       - 姓名：{name}
       - 身份证号码：{id_number}
       - 电话号码：{phone}
       - 电邮地址：{email}

    7. 确认信息并提交

    8. 保存预约确认编号

    9. 截图保存确认页面为 'appointment_{name}.png'

    注意：
    - 使用繁体中文填写
    - 身份证号码格式正确（字母 +7 位数字）
    - 电话号码 8 位数字
    - 完成后返回预约确认编号
    """

    agent = Agent(
        task=task,
        model="gpt-4o",
    )

    result = await agent.run()
    return result


async def main():
    """主函数 - 修改这里的预约信息"""

    # ========== 修改这里 ==========
    result = await book_hk_immd_appointment(
        name="張三",  # 繁体中文姓名
        id_number="A1234567",  # 身份证号
        phone="91234567",  # 电话
        email="test@example.com",  # 电邮
        office="灣仔",  # 办事处：灣仔/觀塘/長沙灣/荃灣/沙田/大埔/屯門/元朗
        date=None,  # 指定日期 "2026-04-15" 或 None 选最早
        time=None,  # 指定时间 "10:00" 或 None 选最早
        headed=True,  # True 显示浏览器窗口，False 后台运行
    )
    # ========== 修改这里 ==========

    print(f"\n{'='*50}")
    print(f"预约结果：{'✅ 成功' if result.success else '❌ 失败'}")

    if result.success:
        print(f"预约编号：{result.confirmation_number}")
        print(f"截图已保存：appointment_張三.png")
    else:
        print(f"失败原因：{result.error}")

    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(main())
