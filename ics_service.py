import os
import uuid
import json
import fcntl
import threading
import time
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from icalendar import Calendar as ICalendar, Event as ICalEvent, vText, vDDDTypes, Alarm
import pytz
from models import (
    Calendar, Event, EventType, Location, CalendarCategory, 
    RRuleBuilder, CreateEventRequest, UpdateEventRequest,
    EventResponse, CalendarResponse, LockManager
)

class ConcurrencyError(Exception):
    """并发冲突异常"""
    pass

class ICSService:
    """ICS日历服务类，负责ICS文件的生成、读取和管理"""
    
    def __init__(self, calendars_dir: str = "calendars"):
        self.calendars_dir = calendars_dir
        self.metadata_file = os.path.join(calendars_dir, "metadata.json")
        self.metadata_lock = threading.RLock()  # 元数据锁
        self._ensure_directories()
        self._load_metadata()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.calendars_dir, exist_ok=True)
    
    def _get_calendar_lock(self, calendar_id: str) -> threading.RLock:
        """获取日历专用锁"""
        return LockManager.get_lock(f"calendar_{calendar_id}")
    
    def _get_metadata_lock(self) -> threading.RLock:
        """获取元数据锁"""
        return self.metadata_lock
    
    def _load_metadata(self):
        """加载日历元数据"""
        with self._get_metadata_lock():
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {"calendars": {}}
    
    def _save_metadata(self):
        """保存日历元数据"""
        with self._get_metadata_lock():
            # 创建临时文件以确保原子性写入
            temp_file = self.metadata_file + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2, default=str)
                # 原子性替换
                os.replace(temp_file, self.metadata_file)
            except Exception as e:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise e
    
    def _generate_uid(self) -> str:
        """生成唯一的事件UID"""
        return str(uuid.uuid4())
    
    def _timestamp_to_datetime(self, timestamp: int, timezone_str: str = "Asia/Shanghai") -> datetime:
        """将时间戳转换为带时区的datetime对象"""
        dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        target_tz = pytz.timezone(timezone_str)
        return dt.astimezone(target_tz)
    
    def _build_rrule_string(self, rrule_builder: RRuleBuilder) -> str:
        """根据RRuleBuilder构建完整的RRULE字符串"""
        if not rrule_builder:
            return None
        
        parts = []
        
        # 频率 (必需)
        if rrule_builder.freq:
            parts.append(f"FREQ={rrule_builder.freq.upper()}")
        
        # 间隔
        if rrule_builder.interval and rrule_builder.interval > 1:
            parts.append(f"INTERVAL={rrule_builder.interval}")
        
        # 结束条件
        if rrule_builder.until_timestamp:
            until_dt = self._timestamp_to_datetime(rrule_builder.until_timestamp)
            parts.append(f"UNTIL={until_dt.strftime('%Y%m%dT%H%M%SZ')}")
        elif rrule_builder.count:
            parts.append(f"COUNT={rrule_builder.count}")
        
        # 星期几
        if rrule_builder.by_weekday:
            weekdays = ",".join(rrule_builder.by_weekday)
            parts.append(f"BYDAY={weekdays}")
        
        # 月份中的日期
        if rrule_builder.by_monthday:
            monthdays = ",".join(map(str, rrule_builder.by_monthday))
            parts.append(f"BYMONTHDAY={monthdays}")
        
        # 月份
        if rrule_builder.by_month:
            months = ",".join(map(str, rrule_builder.by_month))
            parts.append(f"BYMONTH={months}")
        
        return ";".join(parts) if parts else None
    
    def _parse_location_string(self, location_str: str) -> Location:
        """解析地址字符串 {geo:string;name:string} 格式"""
        if not location_str:
            return None
            
        try:
            # 检查是否是结构化格式
            if location_str.startswith('{') and location_str.endswith('}'):
                # 移除大括号
                content = location_str.strip('{}')
                parts = content.split(';')
                
                geo_part = None
                name_part = None
                
                for part in parts:
                    part = part.strip()
                    if part.startswith('geo:'):
                        geo_part = part[4:]  # 移除 'geo:' 前缀
                    elif part.startswith('name:'):
                        name_part = part[5:]  # 移除 'name:' 前缀
                
                # 解析地理坐标
                latitude = None
                longitude = None
                address = None
                
                if geo_part:
                    if ',' in geo_part:
                        try:
                            lat_str, lon_str = geo_part.split(',', 1)
                            latitude = float(lat_str.strip())
                            longitude = float(lon_str.strip())
                        except ValueError:
                            # 如果不是坐标，当作地址处理
                            address = geo_part
                    else:
                        address = geo_part
                
                return Location(
                    name=name_part or "",
                    address=address,
                    latitude=latitude,
                    longitude=longitude
                )
            else:
                # 简单字符串格式，直接作为名称
                return Location(name=location_str)
                
        except Exception as e:
            print(f"Error parsing location string '{location_str}': {e}")
            # 如果解析失败，返回简单的位置对象
            return Location(name=location_str)
    
    def create_calendar(self, calendar: Calendar) -> str:
        """创建新日历"""
        calendar_file = os.path.join(self.calendars_dir, f"{calendar.id}.ics")
        
        # 获取日历锁
        calendar_lock = self._get_calendar_lock(calendar.id)
        
        with calendar_lock:
            # 检查日历是否已存在
            if calendar.id in self.metadata.get("calendars", {}):
                raise ValueError(f"日历 {calendar.id} 已存在")
            
            # 保存元数据
            with self._get_metadata_lock():
                self.metadata["calendars"][calendar.id] = {
                    "name": calendar.name,
                    "description": calendar.description,
                    "color": calendar.color,
                    "timezone": calendar.timezone,
                    "categories": [cat.dict() for cat in calendar.categories],
                    "version": calendar.version,
                    "created_timestamp": calendar.created_timestamp,
                    "modified_timestamp": calendar.modified_timestamp,
                    "file_path": calendar_file
                }
            self._save_metadata()
            
            # 生成ICS文件
            self._generate_ics_file(calendar, calendar_file)
            return calendar_file
    
    def get_calendar(self, calendar_id: str) -> Optional[CalendarResponse]:
        """获取日历信息"""
        with self._get_metadata_lock():
            if calendar_id not in self.metadata["calendars"]:
                return None
            
            meta = self.metadata["calendars"][calendar_id].copy()
        
        calendar_file = meta["file_path"]
        
        if not os.path.exists(calendar_file):
            return None
        
        # 获取日历锁
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            # 从ICS文件读取事件
            events = self._read_events_from_ics(calendar_file)
            
            # 构建Calendar对象
            categories = [CalendarCategory(**cat) for cat in meta.get("categories", [])]
            
            return CalendarResponse(
                id=calendar_id,
                name=meta["name"],
                description=meta.get("description"),
                color=meta["color"],
                timezone=meta["timezone"],
                categories=categories,
                events=events,
                version=meta.get("version", 1),
                created_timestamp=meta.get("created_timestamp", int(datetime.now().timestamp())),
                modified_timestamp=meta.get("modified_timestamp", int(datetime.now().timestamp()))
            )
    
    def list_calendars(self) -> List[Dict]:
        """列出所有日历"""
        calendars = []
        for cal_id, meta in self.metadata["calendars"].items():
            calendars.append({
                "id": cal_id,
                "name": meta["name"],
                "description": meta.get("description"),
                "color": meta["color"],
                "timezone": meta["timezone"],
                "version": meta.get("version", 1),
                "created_timestamp": meta.get("created_timestamp"),
                "modified_timestamp": meta.get("modified_timestamp")
            })
        return calendars
    
    def delete_calendar(self, calendar_id: str) -> bool:
        """删除日历"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return False
                
                calendar_file = self.metadata["calendars"][calendar_id]["file_path"]
            
            # 删除文件
            if os.path.exists(calendar_file):
                os.remove(calendar_file)
            
            # 删除元数据
            with self._get_metadata_lock():
                if calendar_id in self.metadata["calendars"]:
                    del self.metadata["calendars"][calendar_id]
            self._save_metadata()
            
            # 清理锁
            LockManager.cleanup_lock(f"calendar_{calendar_id}")
            return True
    
    def add_event(self, calendar_id: str, event_request: CreateEventRequest) -> Optional[EventResponse]:
        """向日历添加事件"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            # 检查日历是否存在
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return None
                calendar_file = self.metadata["calendars"][calendar_id]["file_path"]
            
            # 解析位置信息
            location = None
            if event_request.location:
                if isinstance(event_request.location, str):
                    location = self._parse_location_string(event_request.location)
                else:
                    location = event_request.location
            
            # 生成UID
            uid = self._generate_uid()
            
            # 构建RRULE字符串
            rrule_string = self._build_rrule_string(event_request.rrule_builder)
            
            # 创建事件对象
            current_timestamp = int(datetime.now().timestamp())
            event = Event(
                uid=uid,
                title=event_request.title,
                description=event_request.description,
                location=location,
                category_id=event_request.category_id,
                event_type=event_request.event_type,
                start_timestamp=event_request.start_timestamp,
                end_timestamp=event_request.end_timestamp,
                duration_minutes=event_request.duration_minutes,
                rrule_builder=event_request.rrule_builder,
                alarm_minutes=event_request.alarm_minutes,
                version=1,
                created_timestamp=current_timestamp,
                modified_timestamp=current_timestamp
            )
            
            # 读取现有日历
            calendar = self._load_calendar_from_file(calendar_id)
            if not calendar:
                return None
            
            # 添加事件
            calendar.events.append(event)
            calendar.modified_timestamp = current_timestamp
            calendar.version += 1
            
            # 更新元数据
            with self._get_metadata_lock():
                self.metadata["calendars"][calendar_id]["modified_timestamp"] = current_timestamp
                self.metadata["calendars"][calendar_id]["version"] = calendar.version
            self._save_metadata()
            
            # 重新生成ICS文件
            self._generate_ics_file(calendar, calendar_file)
            
            # 返回事件响应
            return EventResponse(
                uid=uid,
                title=event.title,
                description=event.description,
                location=location,
                category_id=event.category_id,
                event_type=event.event_type,
                start_timestamp=event.start_timestamp,
                end_timestamp=event.end_timestamp,
                duration_minutes=event.duration_minutes,
                rrule_builder=event.rrule_builder,
                rrule_string=rrule_string,
                alarm_minutes=event.alarm_minutes,
                version=event.version,
                created_timestamp=event.created_timestamp,
                modified_timestamp=event.modified_timestamp
            )
    
    def update_event(self, calendar_id: str, event_uid: str, update_request: UpdateEventRequest) -> Optional[EventResponse]:
        """更新事件"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            # 检查日历是否存在
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return None
                calendar_file = self.metadata["calendars"][calendar_id]["file_path"]
            
            # 读取现有日历
            calendar = self._load_calendar_from_file(calendar_id)
            if not calendar:
                return None
            
            # 查找事件
            event_index = None
            for i, event in enumerate(calendar.events):
                if event.uid == event_uid:
                    event_index = i
                    break
            
            if event_index is None:
                return None
            
            existing_event = calendar.events[event_index]
            
            # 检查版本冲突（乐观锁）
            if update_request.version is not None and existing_event.version != update_request.version:
                raise ConcurrencyError(f"版本冲突：期望版本 {update_request.version}，实际版本 {existing_event.version}")
            
            # 更新事件字段
            current_timestamp = int(datetime.now().timestamp())
            
            if update_request.title is not None:
                existing_event.title = update_request.title
            if update_request.description is not None:
                existing_event.description = update_request.description
            if update_request.location is not None:
                if isinstance(update_request.location, str):
                    existing_event.location = self._parse_location_string(update_request.location)
                else:
                    existing_event.location = update_request.location
            if update_request.category_id is not None:
                existing_event.category_id = update_request.category_id
            if update_request.event_type is not None:
                existing_event.event_type = update_request.event_type
            if update_request.start_timestamp is not None:
                existing_event.start_timestamp = update_request.start_timestamp
            if update_request.end_timestamp is not None:
                existing_event.end_timestamp = update_request.end_timestamp
            if update_request.duration_minutes is not None:
                existing_event.duration_minutes = update_request.duration_minutes
            if update_request.rrule_builder is not None:
                existing_event.rrule_builder = update_request.rrule_builder
            if update_request.alarm_minutes is not None:
                existing_event.alarm_minutes = update_request.alarm_minutes
            
            # 更新版本和时间戳
            existing_event.version += 1
            existing_event.modified_timestamp = current_timestamp
            
            # 更新日历
            calendar.events[event_index] = existing_event
            calendar.modified_timestamp = current_timestamp
            calendar.version += 1
            
            # 更新元数据
            with self._get_metadata_lock():
                self.metadata["calendars"][calendar_id]["modified_timestamp"] = current_timestamp
                self.metadata["calendars"][calendar_id]["version"] = calendar.version
            self._save_metadata()
            
            # 重新生成ICS文件
            self._generate_ics_file(calendar, calendar_file)
            
            # 构建RRULE字符串
            rrule_string = self._build_rrule_string(existing_event.rrule_builder)
            
            # 返回事件响应
            return EventResponse(
                uid=existing_event.uid,
                title=existing_event.title,
                description=existing_event.description,
                location=existing_event.location,
                category_id=existing_event.category_id,
                event_type=existing_event.event_type,
                start_timestamp=existing_event.start_timestamp,
                end_timestamp=existing_event.end_timestamp,
                duration_minutes=existing_event.duration_minutes,
                rrule_builder=existing_event.rrule_builder,
                rrule_string=rrule_string,
                alarm_minutes=existing_event.alarm_minutes,
                version=existing_event.version,
                created_timestamp=existing_event.created_timestamp,
                modified_timestamp=existing_event.modified_timestamp
            )
    
    def delete_event(self, calendar_id: str, event_uid: str) -> bool:
        """删除事件"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            # 检查日历是否存在
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return False
                calendar_file = self.metadata["calendars"][calendar_id]["file_path"]
            
            # 读取现有日历
            calendar = self._load_calendar_from_file(calendar_id)
            if not calendar:
                return False
            
            # 查找并删除事件
            for i, event in enumerate(calendar.events):
                if event.uid == event_uid:
                    calendar.events.pop(i)
                    calendar.modified_timestamp = int(datetime.now().timestamp())
                    calendar.version += 1
                    
                    # 更新元数据
                    with self._get_metadata_lock():
                        self.metadata["calendars"][calendar_id]["modified_timestamp"] = calendar.modified_timestamp
                        self.metadata["calendars"][calendar_id]["version"] = calendar.version
                    self._save_metadata()
                    
                    # 重新生成ICS文件
                    self._generate_ics_file(calendar, calendar_file)
                    return True
            
            return False
    
    def add_category(self, calendar_id: str, category: CalendarCategory) -> bool:
        """添加日程分类"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return False
                
                categories = self.metadata["calendars"][calendar_id].get("categories", [])
                categories.append(category.dict())
                self.metadata["calendars"][calendar_id]["categories"] = categories
                self.metadata["calendars"][calendar_id]["modified_timestamp"] = int(datetime.now().timestamp())
            
            self._save_metadata()
            return True
    
    def get_ics_content(self, calendar_id: str) -> Optional[str]:
        """获取ICS文件内容"""
        calendar_lock = self._get_calendar_lock(calendar_id)
        
        with calendar_lock:
            with self._get_metadata_lock():
                if calendar_id not in self.metadata["calendars"]:
                    return None
                calendar_file = self.metadata["calendars"][calendar_id]["file_path"]
            
            if not os.path.exists(calendar_file):
                return None
            
            with open(calendar_file, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _load_calendar_from_file(self, calendar_id: str) -> Optional[Calendar]:
        """从文件加载日历对象"""
        if calendar_id not in self.metadata["calendars"]:
            return None
        
        meta = self.metadata["calendars"][calendar_id]
        calendar_file = meta["file_path"]
        
        if not os.path.exists(calendar_file):
            return None
        
        # 从ICS文件读取事件
        events = self._read_events_from_ics_as_models(calendar_file)
        
        # 构建Calendar对象
        categories = [CalendarCategory(**cat) for cat in meta.get("categories", [])]
        
        return Calendar(
            id=calendar_id,
            name=meta["name"],
            description=meta.get("description"),
            color=meta["color"],
            timezone=meta["timezone"],
            categories=categories,
            events=events,
            version=meta.get("version", 1),
            created_timestamp=meta.get("created_timestamp", int(datetime.now().timestamp())),
            modified_timestamp=meta.get("modified_timestamp", int(datetime.now().timestamp()))
        )
    
    def _generate_ics_file(self, calendar: Calendar, file_path: str):
        """生成ICS文件"""
        cal = ICalendar()
        cal.add('prodid', '-//ICS Schedule Manager//mxm.dk//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', calendar.name)
        cal.add('x-wr-caldesc', calendar.description or '')
        cal.add('x-wr-timezone', calendar.timezone)
        cal.add('x-apple-calendar-color', calendar.color)
        
        # 设置时区
        timezone = pytz.timezone(calendar.timezone)
        
        for event in calendar.events:
            ical_event = ICalEvent()
            ical_event.add('uid', event.uid)
            ical_event.add('summary', event.title)
            
            if event.description:
                ical_event.add('description', event.description)
            
            # 处理位置信息
            if event.location:
                # 构建位置字符串
                location_parts = []
                if event.location.name:
                    location_parts.append(event.location.name)
                if event.location.address:
                    location_parts.append(event.location.address)
                
                location_str = ", ".join(location_parts) if location_parts else ""
                if location_str:
                    ical_event.add('location', location_str)
                
                # 添加地理坐标
                if event.location.latitude is not None and event.location.longitude is not None:
                    ical_event.add('geo', (event.location.latitude, event.location.longitude))
                    
                    # 添加Apple结构化位置支持 (X-APPLE-STRUCTURED-LOCATION)
                    structured_location_parts = []
                    structured_location_parts.append(f"geo:{event.location.latitude},{event.location.longitude}")
                    
                    if event.location.name:
                        # 对名称进行适当的转义
                        escaped_name = event.location.name.replace(';', '\\;').replace(',', '\\,')
                        structured_location_parts.append(f"name:{escaped_name}")
                    
                    if event.location.address:
                        escaped_address = event.location.address.replace(';', '\\;').replace(',', '\\,')
                        structured_location_parts.append(f"address:{escaped_address}")
                    
                    structured_location = ";".join(structured_location_parts)
                    ical_event.add('x-apple-structured-location', vText(structured_location))
            
            # 处理时间 - 从时间戳转换
            if event.start_timestamp:
                start_dt = self._timestamp_to_datetime(event.start_timestamp, calendar.timezone)
                
                if event.event_type == EventType.ALL_DAY:
                    # 全天事件使用日期
                    ical_event.add('dtstart', start_dt.date())
                    if event.end_timestamp:
                        end_dt = self._timestamp_to_datetime(event.end_timestamp, calendar.timezone)
                        # ICS全天事件的结束日期需要+1天
                        ical_event.add('dtend', end_dt.date() + timedelta(days=1))
                    else:
                        ical_event.add('dtend', start_dt.date() + timedelta(days=1))
                else:
                    # 时段事件使用datetime
                    ical_event.add('dtstart', start_dt)
                    
                    if event.end_timestamp:
                        end_dt = self._timestamp_to_datetime(event.end_timestamp, calendar.timezone)
                        ical_event.add('dtend', end_dt)
                    elif event.duration_minutes:
                        end_dt = start_dt + timedelta(minutes=event.duration_minutes)
                        ical_event.add('dtend', end_dt)
            
            # 添加重复规则
            if event.rrule_builder:
                rrule_string = self._build_rrule_string(event.rrule_builder)
                if rrule_string:
                    ical_event.add('rrule', vText(rrule_string))
            
            # 添加提醒
            if event.alarm_minutes is not None:
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('description', 'Reminder')
                alarm.add('trigger', timedelta(minutes=-event.alarm_minutes))
                ical_event.add_component(alarm)
            
            # 添加分类信息
            if event.category_id:
                # 查找分类名称
                category_name = None
                for cat in calendar.categories:
                    if cat.id == event.category_id:
                        category_name = cat.name
                        break
                if category_name:
                    ical_event.add('categories', category_name)
            
            # 添加时间戳
            created_dt = self._timestamp_to_datetime(event.created_timestamp, calendar.timezone)
            modified_dt = self._timestamp_to_datetime(event.modified_timestamp, calendar.timezone)
            
            ical_event.add('created', created_dt)
            ical_event.add('last-modified', modified_dt)
            ical_event.add('dtstamp', datetime.now(pytz.UTC))
            
            cal.add_component(ical_event)
        
        # 写入文件
        with open(file_path, 'wb') as f:
            f.write(cal.to_ical())
    
    def _read_events_from_ics(self, file_path: str) -> List[EventResponse]:
        """从ICS文件读取事件并返回EventResponse列表"""
        events = []
        
        if not os.path.exists(file_path):
            return events
        
        try:
            with open(file_path, 'rb') as f:
                cal = ICalendar.from_ical(f.read())
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = self._parse_ical_event_to_response(component)
                    if event:
                        events.append(event)
        
        except Exception as e:
            print(f"Error reading ICS file {file_path}: {e}")
        
        return events
    
    def _read_events_from_ics_as_models(self, file_path: str) -> List[Event]:
        """从ICS文件读取事件并返回Event模型列表"""
        events = []
        
        if not os.path.exists(file_path):
            return events
        
        try:
            with open(file_path, 'rb') as f:
                cal = ICalendar.from_ical(f.read())
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = self._parse_ical_event_to_model(component)
                    if event:
                        events.append(event)
        
        except Exception as e:
            print(f"Error reading ICS file {file_path}: {e}")
        
        return events
    
    def _parse_ical_event_to_response(self, ical_event) -> Optional[EventResponse]:
        """解析ICS事件为EventResponse对象"""
        try:
            uid = str(ical_event.get('uid', ''))
            title = str(ical_event.get('summary', ''))
            description = str(ical_event.get('description', '')) if ical_event.get('description') else None
            
            # 解析位置
            location = None
            if ical_event.get('location'):
                location_str = str(ical_event.get('location'))
                geo = ical_event.get('geo')
                location = Location(
                    name=location_str,
                    latitude=float(geo.latitude) if geo and hasattr(geo, 'latitude') else None,
                    longitude=float(geo.longitude) if geo and hasattr(geo, 'longitude') else None
                )
            
            # 解析时间并转换为时间戳
            dtstart = ical_event.get('dtstart')
            dtend = ical_event.get('dtend')
            
            event_type = EventType.TIMED
            start_timestamp = None
            end_timestamp = None
            duration_minutes = None
            
            if dtstart:
                if isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
                    # 全天事件
                    event_type = EventType.ALL_DAY
                    start_dt = datetime.combine(dtstart.dt, datetime.min.time())
                    start_timestamp = int(start_dt.timestamp())
                    
                    if dtend:
                        # ICS全天事件的结束日期需要-1天
                        end_date = dtend.dt - timedelta(days=1)
                        end_dt = datetime.combine(end_date, datetime.max.time())
                        end_timestamp = int(end_dt.timestamp())
                else:
                    # 时段事件
                    start_timestamp = int(dtstart.dt.timestamp())
                    if dtend:
                        end_timestamp = int(dtend.dt.timestamp())
                        # 计算持续时间
                        duration_seconds = end_timestamp - start_timestamp
                        duration_minutes = int(duration_seconds / 60)
            
            # 解析重复规则
            rrule_string = None
            if ical_event.get('rrule'):
                rrule_string = str(ical_event.get('rrule'))
            
            # 解析提醒
            alarm_minutes = None
            for subcomponent in ical_event.subcomponents:
                if subcomponent.name == 'VALARM':
                    trigger = subcomponent.get('trigger')
                    if trigger and hasattr(trigger, 'dt'):
                        if isinstance(trigger.dt, timedelta):
                            alarm_minutes = int(abs(trigger.dt.total_seconds()) / 60)
            
            # 解析分类
            category_id = None
            if ical_event.get('categories'):
                category_id = str(ical_event.get('categories'))
            
            # 解析时间戳
            created = ical_event.get('created')
            created_timestamp = int(created.dt.timestamp()) if created and hasattr(created, 'dt') else int(datetime.now().timestamp())
            
            modified = ical_event.get('last-modified')
            modified_timestamp = int(modified.dt.timestamp()) if modified and hasattr(modified, 'dt') else int(datetime.now().timestamp())
            
            return EventResponse(
                uid=uid,
                title=title,
                description=description,
                location=location,
                category_id=category_id,
                event_type=event_type,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                duration_minutes=duration_minutes,
                rrule_builder=None,  # 从ICS解析时暂不构建RRuleBuilder
                rrule_string=rrule_string,
                alarm_minutes=alarm_minutes,
                version=1,  # 默认版本
                created_timestamp=created_timestamp,
                modified_timestamp=modified_timestamp
            )
        
        except Exception as e:
            print(f"Error parsing event to response: {e}")
            return None
    
    def _parse_ical_event_to_model(self, ical_event) -> Optional[Event]:
        """解析ICS事件为Event模型对象"""
        try:
            uid = str(ical_event.get('uid', ''))
            title = str(ical_event.get('summary', ''))
            description = str(ical_event.get('description', '')) if ical_event.get('description') else None
            
            # 解析位置
            location = None
            if ical_event.get('location'):
                location_str = str(ical_event.get('location'))
                geo = ical_event.get('geo')
                location = Location(
                    name=location_str,
                    latitude=float(geo.latitude) if geo and hasattr(geo, 'latitude') else None,
                    longitude=float(geo.longitude) if geo and hasattr(geo, 'longitude') else None
                )
            
            # 解析时间并转换为时间戳
            dtstart = ical_event.get('dtstart')
            dtend = ical_event.get('dtend')
            
            event_type = EventType.TIMED
            start_timestamp = None
            end_timestamp = None
            duration_minutes = None
            
            if dtstart:
                if isinstance(dtstart.dt, date) and not isinstance(dtstart.dt, datetime):
                    # 全天事件
                    event_type = EventType.ALL_DAY
                    start_dt = datetime.combine(dtstart.dt, datetime.min.time())
                    start_timestamp = int(start_dt.timestamp())
                    
                    if dtend:
                        # ICS全天事件的结束日期需要-1天
                        end_date = dtend.dt - timedelta(days=1)
                        end_dt = datetime.combine(end_date, datetime.max.time())
                        end_timestamp = int(end_dt.timestamp())
                else:
                    # 时段事件
                    start_timestamp = int(dtstart.dt.timestamp())
                    if dtend:
                        end_timestamp = int(dtend.dt.timestamp())
                        # 计算持续时间
                        duration_seconds = end_timestamp - start_timestamp
                        duration_minutes = int(duration_seconds / 60)
            
            # 解析提醒
            alarm_minutes = None
            for subcomponent in ical_event.subcomponents:
                if subcomponent.name == 'VALARM':
                    trigger = subcomponent.get('trigger')
                    if trigger and hasattr(trigger, 'dt'):
                        if isinstance(trigger.dt, timedelta):
                            alarm_minutes = int(abs(trigger.dt.total_seconds()) / 60)
            
            # 解析分类
            category_id = None
            if ical_event.get('categories'):
                category_id = str(ical_event.get('categories'))
            
            # 解析时间戳
            created = ical_event.get('created')
            created_timestamp = int(created.dt.timestamp()) if created and hasattr(created, 'dt') else int(datetime.now().timestamp())
            
            modified = ical_event.get('last-modified')
            modified_timestamp = int(modified.dt.timestamp()) if modified and hasattr(modified, 'dt') else int(datetime.now().timestamp())
            
            return Event(
                uid=uid,
                title=title,
                description=description,
                location=location,
                category_id=category_id,
                event_type=event_type,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                duration_minutes=duration_minutes,
                rrule_builder=None,  # 从ICS解析时暂不构建RRuleBuilder
                alarm_minutes=alarm_minutes,
                version=1,  # 默认版本
                created_timestamp=created_timestamp,
                modified_timestamp=modified_timestamp
            )
        
        except Exception as e:
            print(f"Error parsing event to model: {e}")
            return None