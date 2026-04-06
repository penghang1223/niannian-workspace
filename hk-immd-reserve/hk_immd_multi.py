#!/usr/bin/env python3
"""
香港入境事务处身份证预约工具 - 多人并发版
运行环境：macOS
依赖：pip3 install browser-use

使用方法：
    python3 hk_immd_multi.py
"""

import asyncio
from browser_use import Agent


# ========== 修改这里：添加申请人信息 ==========
APPLICANTS = [
    {
        "name": "張三",
        "id": "A1234567",
        "phone": "91234567",
        "email": "zhang@example.com",
        "office": "灣仔"
    },
    {
        "name": "李四",
        "id": "B2345678",
        "phone": "92345678",
        "email": "li@example.com",
        "office": "觀塘"
    },
    {
        "name": "王五",
        "id": "C3456789",
        "phone": "93456789",
        "email": "wang@example.com",
        "office": "長沙灣"
    },
    # ... 添加更多人
]
# ========== 修改这里 ==========


async def book_single(applicant, index):
    """单个预约任务"""

    task = f"""
    为以下申请人预约香港身份证：
    - 姓名：{applicant['name']}
    - 身份证：{applicant['id']}
    - 电话：{applicant['phone']}
    - 电邮：{applicant['email']}
    - 办事处：{applicant['office']}

    步骤：
    1. 打开 https://system.es2.immd.gov.hk/smartics2-client/ropbooking/zh-HK/eservices/makeAppointment/term
    2. 选择服务：申领身份证
    3. 选择办事处：{applicant['office']}
    4. 选择最早的可用日期和时间
    5. 填写信息并提交
    6. 返回预约确认编号
    7. 截图保存为 'appointment_{applicant['name']}.png'
    """

    agent = Agent(task=task, model="gpt-4o")
    result = await agent.run()

    status = "✅成功" if result.success else "❌失败"
    print(f"[{index}] {applicant['name']} - {status}")

    if result.success:
        print(f"    预约编号：{result.confirmation_number}")
        print(f"    办事处：{applicant['office']}")
        print(f"    截图：appointment_{applicant['name']}.png")

    return result


async def main():
    """并发执行所有预约"""

    print(f"开始为 {len(APPLICANTS)} 人预约香港身份证...")
    print(f"{'='*50}\n")

    # 创建任务
    tasks = [
        book_single(applicant, i)
        for i, applicant in enumerate(APPLICANTS, 1)
    ]

    # 限制并发数（建议最多 5 个同时，避免被封锁）
    semaphore = asyncio.Semaphore(5)

    async def limited(task):
        async with semaphore:
            return await task

    results = await asyncio.gather(*[limited(t) for t in tasks])

    # 统计结果
    success = sum(1 for r in results if r.success)

    print(f"\n{'='*50}")
    print(f"完成：{success}/{len(APPLICANTS)} 成功")

    if success > 0:
        print(f"\n成功的预约：")
        for i, r in enumerate(results):
            if r.success:
                applicant = APPLICANTS[i]
                print(f"  - {applicant['name']}: {r.confirmation_number} ({applicant['office']})")

    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(main())
