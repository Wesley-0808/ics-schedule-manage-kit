from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import threading

class EventType(str, Enum):
    ALL_DAY = "all_day"
    TIMED = "timed"
    DURATION = "duration"

class CalendarCategory(BaseModel):
    id: str
    name: str
    color: str = Field(default="#3174ad", description="Hex color code")
    description: Optional[str] = None

class Location(BaseModel):
    name: str = Field(description="位置名称")
    address: Optional[str] = Field(default=None, description="详细地址")
    latitude: Optional[float] = Field(default=None, description="纬度")
    longitude: Optional[float] = Field(default=None, description="经度")
    
    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('纬度必须在-90到90之间')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('经度必须在-180到180之间')
        return v

# RRULE构建器相关模型
class RRuleFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"

class RRuleWeekday(str, Enum):
    MO = "MO"
    TU = "TU"
    WE = "WE"
    TH = "TH"
    FR = "FR"
    SA = "SA"
    SU = "SU"

class RRuleBuilder(BaseModel):
    freq: RRuleFrequency
    interval: Optional[int] = Field(default=1, description="间隔")
    count: Optional[int] = Field(default=None, description="重复次数")
    until_timestamp: Optional[int] = Field(default=None, description="结束时间戳")
    by_weekday: Optional[List[RRuleWeekday]] = Field(default=None, description="星期几")
    by_monthday: Optional[List[int]] = Field(default=None, description="每月第几天")
    by_month: Optional[List[int]] = Field(default=None, description="月份")
    
    @validator('by_monthday')
    def validate_monthday(cls, v):
        if v:
            for day in v:
                if not (-31 <= day <= 31 and day != 0):
                    raise ValueError('by_monthday必须在-31到31之间且不为0')
        return v
    
    @validator('by_month')
    def validate_month(cls, v):
        if v:
            for month in v:
                if not (1 <= month <= 12):
                    raise ValueError('by_month必须在1到12之间')
        return v

# 并发控制锁管理器
class LockManager:
    _locks: Dict[str, threading.RLock] = {}
    _lock = threading.Lock()
    
    @classmethod
    def get_lock(cls, resource_id: str) -> threading.RLock:
        with cls._lock:
            if resource_id not in cls._locks:
                cls._locks[resource_id] = threading.RLock()
            return cls._locks[resource_id]
    
    @classmethod
    def cleanup_lock(cls, resource_id: str):
        with cls._lock:
            if resource_id in cls._locks:
                del cls._locks[resource_id]

class Event(BaseModel):
    uid: Optional[str] = Field(default=None, description="事件UID，由服务端生成")
    title: str
    description: Optional[str] = None
    location: Optional[Location] = None
    category_id: Optional[str] = None
    event_type: EventType
    
    # 时间相关字段 - 统一使用时间戳
    start_timestamp: Optional[int] = Field(default=None, description="开始时间戳(秒)")
    end_timestamp: Optional[int] = Field(default=None, description="结束时间戳(秒)")
    duration_minutes: Optional[int] = Field(default=None, description="持续时长(分钟)")
    
    # 重复规则 - 使用结构化数据
    rrule_builder: Optional[RRuleBuilder] = Field(default=None, description="重复规则构建器")
    
    # 提醒设置
    alarm_minutes: Optional[int] = None
    
    # 版本控制字段
    version: int = Field(default=1, description="版本号，用于并发控制")
    created_timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    modified_timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    
    @validator('start_timestamp', 'end_timestamp')
    def validate_timestamps(cls, v):
        if v is not None and v <= 0:
            raise ValueError('时间戳必须大于0')
        return v
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('持续时长必须大于0')
        return v

class Calendar(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    color: str = Field(default="#3174ad")
    timezone: str = Field(default="Asia/Shanghai")
    categories: List[CalendarCategory] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    version: int = Field(default=1, description="版本号，用于并发控制")
    created_timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    modified_timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

# API请求模型
class CreateCalendarRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = Field(default="#3174ad")
    timezone: str = Field(default="Asia/Shanghai")

class CreateEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None  # 支持字符串格式 {geo:string;name:string}
    category_id: Optional[str] = None
    event_type: EventType
    
    # 统一使用时间戳
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_minutes: Optional[int] = None
    
    # 使用结构化重复规则
    rrule_builder: Optional[RRuleBuilder] = None
    alarm_minutes: Optional[int] = None

class CreateCategoryRequest(BaseModel):
    name: str
    color: str = Field(default="#3174ad")
    description: Optional[str] = None

class UpdateEventRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None  # 支持字符串格式 {geo:string;name:string}
    category_id: Optional[str] = None
    event_type: Optional[EventType] = None
    
    # 统一使用时间戳
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_minutes: Optional[int] = None
    
    # 使用结构化重复规则
    rrule_builder: Optional[RRuleBuilder] = None
    alarm_minutes: Optional[int] = None
    
    # 版本控制
    version: Optional[int] = Field(default=None, description="当前版本号，用于乐观锁")

# 响应模型
class EventResponse(BaseModel):
    """事件响应模型，包含完整的事件信息"""
    uid: str
    title: str
    description: Optional[str] = None
    location: Optional[Location] = None
    category_id: Optional[str] = None
    event_type: EventType
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_minutes: Optional[int] = None
    rrule_builder: Optional[RRuleBuilder] = None
    rrule_string: Optional[str] = Field(default=None, description="生成的RRULE字符串")
    alarm_minutes: Optional[int] = None
    version: int
    created_timestamp: int
    modified_timestamp: int

class CalendarResponse(BaseModel):
    """日历响应模型"""
    id: str
    name: str
    description: Optional[str] = None
    color: str
    timezone: str
    categories: List[CalendarCategory]
    events: List[EventResponse]
    version: int
    created_timestamp: int
    modified_timestamp: int