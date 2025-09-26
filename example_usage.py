#!/usr/bin/env python3
"""
ICS日程管理系统使用示例
演示如何使用API创建日历、添加事件等功能
"""

import requests
import json
from datetime import datetime, date, timedelta

# API基础URL
BASE_URL = "http://localhost:8000"

def create_sample_calendar():
    """创建示例日历"""
    print("=== 创建示例日历 ===")
    
    calendar_data = {
        "name": "我的工作日历",
        "description": "包含工作相关的所有日程安排",
        "color": "#FF6B6B",
        "timezone": "Asia/Shanghai"
    }
    
    response = requests.post(f"{BASE_URL}/calendars", json=calendar_data)
    if response.status_code == 200:
        calendar = response.json()
        print(f"✅ 日历创建成功: {calendar['name']}")
        print(f"   ID: {calendar['id']}")
        print(f"   订阅链接: {BASE_URL}{calendar['subscribe_url']}")
        print(f"   下载链接: {BASE_URL}{calendar['download_url']}")
        return calendar['id']
    else:
        print(f"❌ 日历创建失败: {response.text}")
        return None

def create_categories(calendar_id):
    """创建分类"""
    print("\n=== 创建日程分类 ===")
    
    categories = [
        {"name": "工作会议", "color": "#4ECDC4", "description": "各种工作会议"},
        {"name": "个人事务", "color": "#45B7D1", "description": "个人相关事务"},
        {"name": "学习培训", "color": "#96CEB4", "description": "学习和培训活动"},
        {"name": "休闲娱乐", "color": "#FFEAA7", "description": "休闲娱乐活动"}
    ]
    
    category_ids = {}
    
    for cat_data in categories:
        response = requests.post(f"{BASE_URL}/calendars/{calendar_id}/categories", json=cat_data)
        if response.status_code == 200:
            category = response.json()
            category_ids[cat_data['name']] = category['id']
            print(f"✅ 分类创建成功: {cat_data['name']}")
        else:
            print(f"❌ 分类创建失败: {cat_data['name']}")
    
    return category_ids

def create_sample_events(calendar_id, category_ids):
    """创建示例事件"""
    print("\n=== 创建示例事件 ===")
    
    # 获取今天和未来几天的日期
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    
    events = [
        {
            "title": "团队周会",
            "description": "每周团队例会，讨论项目进展和问题",
            "event_type": "timed",
            "start_datetime": datetime.combine(tomorrow, datetime.min.time().replace(hour=10, minute=0)).isoformat(),
            "end_datetime": datetime.combine(tomorrow, datetime.min.time().replace(hour=11, minute=30)).isoformat(),
            "category_id": category_ids.get("工作会议"),
            "location": {
                "name": "会议室A",
                "address": "公司大楼3楼",
                "latitude": 39.9042,
                "longitude": 116.4074
            },
            "alarm_minutes": 15
        },
        {
            "title": "项目截止日",
            "description": "重要项目的最终截止日期",
            "event_type": "all_day",
            "start_date": next_week.isoformat(),
            "category_id": category_ids.get("工作会议"),
            "alarm_minutes": 1440  # 提前一天提醒
        },
        {
            "title": "健身训练",
            "description": "每周定期健身训练",
            "event_type": "duration",
            "start_datetime": datetime.combine(today + timedelta(days=2), datetime.min.time().replace(hour=19, minute=0)).isoformat(),
            "duration_minutes": 90,
            "category_id": category_ids.get("休闲娱乐"),
            "location": {
                "name": "健身房",
                "address": "市中心健身中心"
            },
            "rrule": "FREQ=WEEKLY;BYDAY=TU,TH",  # 每周二、四重复
            "alarm_minutes": 30
        },
        {
            "title": "在线培训课程",
            "description": "技术技能提升培训",
            "event_type": "timed",
            "start_datetime": datetime.combine(today + timedelta(days=3), datetime.min.time().replace(hour=14, minute=0)).isoformat(),
            "end_datetime": datetime.combine(today + timedelta(days=3), datetime.min.time().replace(hour=16, minute=0)).isoformat(),
            "category_id": category_ids.get("学习培训"),
            "alarm_minutes": 10
        },
        {
            "title": "医院体检",
            "description": "年度健康体检",
            "event_type": "duration",
            "start_datetime": datetime.combine(today + timedelta(days=5), datetime.min.time().replace(hour=8, minute=30)).isoformat(),
            "duration_minutes": 120,
            "category_id": category_ids.get("个人事务"),
            "location": {
                "name": "市人民医院",
                "address": "健康路123号"
            },
            "alarm_minutes": 60
        }
    ]
    
    created_events = []
    
    for event_data in events:
        response = requests.post(f"{BASE_URL}/calendars/{calendar_id}/events", json=event_data)
        if response.status_code == 200:
            event = response.json()
            created_events.append(event)
            print(f"✅ 事件创建成功: {event_data['title']}")
        else:
            print(f"❌ 事件创建失败: {event_data['title']} - {response.text}")
    
    return created_events

def demonstrate_api_usage(calendar_id):
    """演示API的各种用法"""
    print("\n=== API使用演示 ===")
    
    # 获取日历信息
    print("\n1. 获取日历信息:")
    response = requests.get(f"{BASE_URL}/calendars/{calendar_id}")
    if response.status_code == 200:
        calendar = response.json()
        print(f"   日历名称: {calendar['name']}")
        print(f"   事件数量: {len(calendar['events'])}")
        print(f"   分类数量: {len(calendar['categories'])}")
    
    # 获取统计信息
    print("\n2. 获取统计信息:")
    response = requests.get(f"{BASE_URL}/calendars/{calendar_id}/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"   总事件数: {stats['total_events']}")
        print(f"   事件类型分布: {stats['event_type_stats']}")
        print(f"   分类分布: {stats['category_stats']}")
    
    # 按日期范围查询事件
    print("\n3. 按日期范围查询事件:")
    today = date.today()
    next_week = today + timedelta(days=7)
    
    response = requests.get(
        f"{BASE_URL}/calendars/{calendar_id}/events",
        params={
            "start_date": today.isoformat(),
            "end_date": next_week.isoformat()
        }
    )
    if response.status_code == 200:
        events = response.json()['events']
        print(f"   未来一周的事件数量: {len(events)}")
        for event in events:
            print(f"   - {event['title']} ({event['event_type']})")
    
    # 获取所有日历列表
    print("\n4. 获取所有日历:")
    response = requests.get(f"{BASE_URL}/calendars")
    if response.status_code == 200:
        calendars = response.json()['calendars']
        print(f"   系统中共有 {len(calendars)} 个日历")
        for cal in calendars:
            print(f"   - {cal['name']} (ID: {cal['id']})")

def main():
    """主函数"""
    print("🗓️  ICS日程管理系统使用示例")
    print("=" * 50)
    
    try:
        # 检查服务是否运行
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动服务: python main.py")
            return
        
        print("✅ 服务运行正常")
        
        # 创建示例日历
        calendar_id = create_sample_calendar()
        if not calendar_id:
            return
        
        # 创建分类
        category_ids = create_categories(calendar_id)
        
        # 创建示例事件
        created_events = create_sample_events(calendar_id, category_ids)
        
        # 演示API使用
        demonstrate_api_usage(calendar_id)
        
        print("\n" + "=" * 50)
        print("🎉 示例运行完成！")
        print(f"\n📱 您可以通过以下方式使用日历:")
        print(f"   • 订阅链接: {BASE_URL}/calendars/{calendar_id}/subscribe")
        print(f"   • 下载文件: {BASE_URL}/calendars/{calendar_id}/download")
        print(f"   • API文档: {BASE_URL}/docs")
        
        print(f"\n📋 如何在日历应用中使用:")
        print(f"   • Apple 日历: 添加订阅 → 输入订阅链接")
        print(f"   • Google Calendar: 添加其他日历 → 通过URL添加")
        print(f"   • Outlook: 添加日历 → 从Internet添加")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务正在运行")
        print("   启动命令: python main.py")
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == "__main__":
    main()