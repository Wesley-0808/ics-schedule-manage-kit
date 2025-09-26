from fastapi import FastAPI, HTTPException, Response, Query
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
from datetime import datetime, date
import os

from models import (
    Calendar, Event, EventType, Location, CalendarCategory,
    CreateCalendarRequest, CreateEventRequest, CreateCategoryRequest, UpdateEventRequest,
    EventResponse, CalendarResponse
)
from ics_service import ICSService, ConcurrencyError

# 创建FastAPI应用
app = FastAPI(
    title="ICS Schedule Management System",
    description="一个功能完整的ICS日程管理系统，兼容Apple日历、Google Calendar、Outlook等",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化ICS服务
ics_service = ICSService()

# ==================== 日历管理 ====================

@app.post("/calendars", summary="创建日历", response_model=dict)
async def create_calendar(request: CreateCalendarRequest):
    """创建新的日历"""
    calendar_id = str(uuid.uuid4())
    current_timestamp = int(datetime.now().timestamp())
    
    calendar = Calendar(
        id=calendar_id,
        name=request.name,
        description=request.description,
        color=request.color,
        timezone=request.timezone,
        version=1,
        created_timestamp=current_timestamp,
        modified_timestamp=current_timestamp
    )
    
    file_path = ics_service.create_calendar(calendar)
    
    return {
        "id": calendar_id,
        "name": calendar.name,
        "description": calendar.description,
        "color": calendar.color,
        "timezone": calendar.timezone,
        "version": calendar.version,
        "created_timestamp": calendar.created_timestamp,
        "modified_timestamp": calendar.modified_timestamp,
        "file_path": file_path,
        "subscribe_url": f"/calendars/{calendar_id}/subscribe",
        "download_url": f"/calendars/{calendar_id}/download"
    }

@app.get("/calendars", summary="获取所有日历")
async def list_calendars():
    """获取所有日历列表"""
    calendars = ics_service.list_calendars()
    
    # 为每个日历添加订阅和下载链接
    for calendar in calendars:
        calendar["subscribe_url"] = f"/calendars/{calendar['id']}/subscribe"
        calendar["download_url"] = f"/calendars/{calendar['id']}/download"
    
    return {"calendars": calendars}

@app.get("/calendars/{calendar_id}", summary="获取日历详情", response_model=CalendarResponse)
async def get_calendar(calendar_id: str):
    """获取指定日历的详细信息"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    return calendar

@app.delete("/calendars/{calendar_id}", summary="删除日历")
async def delete_calendar(calendar_id: str):
    """删除指定的日历"""
    success = ics_service.delete_calendar(calendar_id)
    if not success:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    return {"message": "日历删除成功"}

# ==================== 日历订阅和下载 ====================

@app.get("/calendars/{calendar_id}/subscribe", summary="日历订阅")
async def subscribe_calendar(calendar_id: str):
    """获取日历订阅链接（返回ICS内容）"""
    ics_content = ics_service.get_ics_content(calendar_id)
    if not ics_content:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    return PlainTextResponse(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename={calendar_id}.ics",
            "Cache-Control": "no-cache"
        }
    )

@app.get("/calendars/{calendar_id}/download", summary="下载日历文件")
async def download_calendar(calendar_id: str):
    """下载日历ICS文件"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    file_path = ics_service.metadata["calendars"][calendar_id]["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="日历文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=f"{calendar.name}.ics",
        media_type="text/calendar"
    )

# ==================== 事件管理 ====================

@app.post("/calendars/{calendar_id}/events", summary="创建事件", response_model=EventResponse)
async def create_event(calendar_id: str, request: CreateEventRequest):
    """在指定日历中创建新事件
    
    地址格式支持：
    - 简单字符串: "北京市朝阳区"
    - 结构化格式: "{geo:39.9042,116.4074;name:天安门广场}"
    - 仅坐标: "{geo:39.9042,116.4074}"
    - 仅名称: "{name:会议室A}"
    """
    # 验证事件类型和时间字段的一致性
    if request.event_type == EventType.ALL_DAY:
        if not request.start_timestamp:
            raise HTTPException(status_code=400, detail="全天事件必须提供开始时间戳")
    elif request.event_type == EventType.TIMED:
        if not request.start_timestamp or not request.end_timestamp:
            raise HTTPException(status_code=400, detail="时段事件必须提供开始和结束时间戳")
    elif request.event_type == EventType.DURATION:
        if not request.start_timestamp or not request.duration_minutes:
            raise HTTPException(status_code=400, detail="区间事件必须提供开始时间戳和持续时长")
    
    try:
        event_response = ics_service.add_event(calendar_id, request)
        if not event_response:
            raise HTTPException(status_code=404, detail="日历不存在")
        
        return event_response
    
    except ConcurrencyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"事件创建失败: {str(e)}")

@app.get("/calendars/{calendar_id}/events", summary="获取日历事件")
async def get_calendar_events(
    calendar_id: str,
    start_timestamp: Optional[int] = Query(None, description="开始时间戳过滤"),
    end_timestamp: Optional[int] = Query(None, description="结束时间戳过滤"),
    category_id: Optional[str] = Query(None, description="分类过滤")
):
    """获取指定日历的所有事件"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    events = calendar.events
    
    # 应用过滤条件
    if start_timestamp or end_timestamp or category_id:
        filtered_events = []
        for event in events:
            # 分类过滤
            if category_id and event.category_id != category_id:
                continue
            
            # 时间戳过滤
            if start_timestamp or end_timestamp:
                event_start = event.start_timestamp
                event_end = event.end_timestamp
                
                # 如果没有结束时间戳，使用持续时间计算
                if not event_end and event.duration_minutes and event_start:
                    event_end = event_start + (event.duration_minutes * 60)
                
                if start_timestamp and event_end and event_end < start_timestamp:
                    continue
                if end_timestamp and event_start and event_start > end_timestamp:
                    continue
            
            filtered_events.append(event)
        
        events = filtered_events
    
    return {"events": events}

@app.get("/calendars/{calendar_id}/events/{event_uid}", summary="获取事件详情", response_model=EventResponse)
async def get_event(calendar_id: str, event_uid: str):
    """获取指定事件的详细信息"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    for event in calendar.events:
        if event.uid == event_uid:
            return event
    
    raise HTTPException(status_code=404, detail="事件不存在")

@app.put("/calendars/{calendar_id}/events/{event_uid}", summary="更新事件", response_model=EventResponse)
async def update_event(calendar_id: str, event_uid: str, request: UpdateEventRequest):
    """更新指定的事件
    
    支持乐观锁并发控制：
    - 传入version字段进行版本检查
    - 版本不匹配时返回409冲突错误
    
    地址格式支持：
    - 简单字符串: "北京市朝阳区"
    - 结构化格式: "{geo:39.9042,116.4074;name:天安门广场}"
    """
    try:
        event_response = ics_service.update_event(calendar_id, event_uid, request)
        if not event_response:
            raise HTTPException(status_code=404, detail="事件不存在")
        
        return event_response
    
    except ConcurrencyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"事件更新失败: {str(e)}")

@app.delete("/calendars/{calendar_id}/events/{event_uid}", summary="删除事件")
async def delete_event(calendar_id: str, event_uid: str):
    """删除指定的事件"""
    success = ics_service.delete_event(calendar_id, event_uid)
    if not success:
        raise HTTPException(status_code=404, detail="事件不存在")
    
    return {"message": "事件删除成功"}

# ==================== 分类管理 ====================

@app.post("/calendars/{calendar_id}/categories", summary="创建分类")
async def create_category(calendar_id: str, request: CreateCategoryRequest):
    """为指定日历创建新的分类"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    category_id = str(uuid.uuid4())
    category = CalendarCategory(
        id=category_id,
        name=request.name,
        color=request.color,
        description=request.description
    )
    
    success = ics_service.add_category(calendar_id, category)
    if not success:
        raise HTTPException(status_code=500, detail="分类创建失败")
    
    return {
        "id": category_id,
        "message": "分类创建成功",
        "category": category
    }

@app.get("/calendars/{calendar_id}/categories", summary="获取分类列表")
async def get_categories(calendar_id: str):
    """获取指定日历的所有分类"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    return {"categories": calendar.categories}

# ==================== 统计信息 ====================

@app.get("/calendars/{calendar_id}/stats", summary="获取日历统计")
async def get_calendar_stats(calendar_id: str):
    """获取日历的统计信息"""
    calendar = ics_service.get_calendar(calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="日历不存在")
    
    total_events = len(calendar.events)
    
    # 按事件类型统计
    event_type_stats = {
        "all_day": 0,
        "timed": 0,
        "duration": 0
    }
    
    # 按分类统计
    category_stats = {}
    
    for event in calendar.events:
        event_type_stats[event.event_type.value] += 1
        
        if event.category_id:
            category_name = "未知分类"
            for cat in calendar.categories:
                if cat.id == event.category_id:
                    category_name = cat.name
                    break
            category_stats[category_name] = category_stats.get(category_name, 0) + 1
        else:
            category_stats["无分类"] = category_stats.get("无分类", 0) + 1
    
    return {
        "total_events": total_events,
        "total_categories": len(calendar.categories),
        "event_type_stats": event_type_stats,
        "category_stats": category_stats,
        "version": calendar.version,
        "created_timestamp": calendar.created_timestamp,
        "modified_timestamp": calendar.modified_timestamp
    }

# ==================== 时间戳工具 ====================

@app.get("/utils/timestamp", summary="获取当前时间戳")
async def get_current_timestamp():
    """获取当前时间戳"""
    return {
        "timestamp": int(datetime.now().timestamp()),
        "iso_format": datetime.now().isoformat(),
        "description": "当前时间戳（秒）"
    }

@app.get("/utils/timestamp/{timestamp}", summary="时间戳转换")
async def convert_timestamp(timestamp: int):
    """将时间戳转换为可读格式"""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return {
            "timestamp": timestamp,
            "iso_format": dt.isoformat(),
            "readable": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S")
        }
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"无效的时间戳: {str(e)}")

# ==================== RRULE工具 ====================

@app.post("/utils/rrule/preview", summary="预览RRULE规则")
async def preview_rrule(rrule_builder: dict):
    """预览RRULE规则生成的重复事件
    
    支持的字段：
    - freq: DAILY/WEEKLY/MONTHLY/YEARLY (必需)
    - interval: 间隔数 (默认1)
    - count: 重复次数
    - until_timestamp: 结束时间戳
    - by_weekday: 星期几 ["MO","TU","WE","TH","FR","SA","SU"]
    - by_monthday: 每月第几天 [1-31, -31--1]
    - by_month: 月份 [1-12]
    """
    try:
        from models import RRuleBuilder
        builder = RRuleBuilder(**rrule_builder)
        rrule_string = ics_service._build_rrule_string(builder)
        
        # 提供使用示例
        examples = {
            "每天": {"freq": "DAILY"},
            "每周一三五": {"freq": "WEEKLY", "by_weekday": ["MO", "WE", "FR"]},
            "每月15日": {"freq": "MONTHLY", "by_monthday": [15]},
            "每两周": {"freq": "WEEKLY", "interval": 2},
            "重复10次": {"freq": "DAILY", "count": 10}
        }
        
        return {
            "rrule_builder": builder,
            "rrule_string": rrule_string,
            "description": "生成的RRULE字符串",
            "examples": examples
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"RRULE构建失败: {str(e)}")

# ==================== 健康检查 ====================

@app.get("/health", summary="健康检查")
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "timestamp": int(datetime.now().timestamp()),
        "calendars_count": len(ics_service.metadata["calendars"]),
        "version": "2.0.0",
        "features": {
            "concurrency_control": True,
            "server_side_uid": True,
            "timestamp_format": True,
            "structured_location": True,
            "rrule_builder": True
        }
    }

# ==================== 错误处理 ====================

@app.exception_handler(ConcurrencyError)
async def concurrency_error_handler(request, exc):
    """处理并发冲突异常"""
    return HTTPException(status_code=409, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)