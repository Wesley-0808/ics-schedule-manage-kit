# ICS日程管理系统 - 改进版本

## 🚀 新功能和改进

### 1. 增强的地址支持
- **X-APPLE-STRUCTURED-LOCATION**: 完整支持Apple日历的结构化位置
- **灵活的地址格式**: 支持多种地址输入格式
  ```json
  // 简单字符串
  "location": "北京市朝阳区建国门外大街1号"
  
  // 完整结构化格式
  "location": "{geo:39.9042,116.4074;name:天安门广场}"
  
  // 仅坐标
  "location": "{geo:39.9042,116.4074}"
  
  // 仅名称
  "location": "{name:会议室A}"
  ```

### 2. 服务端UID生成
- 所有事件UID由服务端自动生成
- 确保全局唯一性
- 客户端无需处理UID冲突

### 3. 并发控制机制
- **乐观锁**: 基于版本号的并发控制
- **资源锁**: 防止多客户端同时修改
- **原子操作**: 确保数据一致性

### 4. 统一时间戳格式
- 所有时间使用Unix时间戳（秒）
- 服务端负责时区转换
- 简化客户端时间处理

### 5. 结构化RRULE构建
- 替代原始RRULE字符串
- 客户端提供结构化数据
- 服务端生成标准RRULE

## 📋 API改进

### 创建事件 API
```http
POST /calendars/{calendar_id}/events
```

**请求示例**:
```json
{
  "title": "重要会议",
  "description": "项目讨论会议",
  "location": "{geo:39.9042,116.4074;name:天安门广场}",
  "event_type": "timed",
  "start_timestamp": 1699776000,
  "end_timestamp": 1699779600,
  "rrule_builder": {
    "freq": "WEEKLY",
    "by_weekday": ["MO", "WE", "FR"],
    "count": 10
  },
  "alarm_minutes": 15
}
```

**响应示例**:
```json
{
  "uid": "550e8400-e29b-41d4-a716-446655440000",
  "title": "重要会议",
  "location": {
    "name": "天安门广场",
    "latitude": 39.9042,
    "longitude": 116.4074
  },
  "rrule_string": "FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=10",
  "version": 1,
  "created_timestamp": 1699776000,
  "modified_timestamp": 1699776000
}
```

### 更新事件 API
```http
PUT /calendars/{calendar_id}/events/{event_uid}
```

**乐观锁示例**:
```json
{
  "title": "更新后的标题",
  "version": 1  // 用于版本检查
}
```

**版本冲突响应**:
```http
HTTP/1.1 409 Conflict
{
  "detail": "版本冲突：期望版本 1，实际版本 2"
}
```

### RRULE构建器预览
```http
POST /utils/rrule/preview
```

**请求示例**:
```json
{
  "freq": "MONTHLY",
  "by_monthday": [15],
  "until_timestamp": 1730908800
}
```

**响应示例**:
```json
{
  "rrule_builder": {
    "freq": "MONTHLY",
    "by_monthday": [15],
    "until_timestamp": 1730908800
  },
  "rrule_string": "FREQ=MONTHLY;BYMONTHDAY=15;UNTIL=20241106T160000Z",
  "examples": {
    "每天": {"freq": "DAILY"},
    "每周一三五": {"freq": "WEEKLY", "by_weekday": ["MO", "WE", "FR"]},
    "每月15日": {"freq": "MONTHLY", "by_monthday": [15]}
  }
}
```

## 🔧 技术改进

### 并发控制架构
```python
# 资源级锁管理
class LockManager:
    @classmethod
    def get_lock(cls, resource_id: str) -> threading.RLock:
        # 获取资源专用锁
    
    @classmethod
    def cleanup_lock(cls, resource_id: str):
        # 清理不再使用的锁

# 乐观锁实现
def update_event(self, calendar_id, event_uid, update_request):
    if update_request.version != existing_event.version:
        raise ConcurrencyError("版本冲突")
```

### 地址解析引擎
```python
def _parse_location_string(self, location_str: str) -> Location:
    """
    解析多种地址格式：
    - 简单字符串: "地址名称"
    - 结构化: "{geo:lat,lon;name:名称}"
    - 仅坐标: "{geo:lat,lon}"
    - 仅名称: "{name:名称}"
    """
```

### X-APPLE-STRUCTURED-LOCATION生成
```python
# 生成Apple兼容的结构化位置
structured_location_parts = []
structured_location_parts.append(f"geo:{latitude},{longitude}")

if name:
    escaped_name = name.replace(';', '\\;').replace(',', '\\,')
    structured_location_parts.append(f"name:{escaped_name}")

structured_location = ";".join(structured_location_parts)
ical_event.add('x-apple-structured-location', vText(structured_location))
```

## 🧪 测试

运行完整的功能测试：
```bash
python test_improvements.py
```

测试覆盖：
- ✅ 地址格式解析
- ✅ RRULE构建器
- ✅ 并发控制
- ✅ Apple结构化位置
- ✅ 时间戳工具
- ✅ 服务端UID生成

## 📱 客户端兼容性

### Apple日历
- ✅ X-APPLE-STRUCTURED-LOCATION支持
- ✅ 地理坐标显示
- ✅ 重复规则完全兼容

### Google Calendar
- ✅ 标准ICS格式
- ✅ 地理坐标支持
- ✅ RRULE规则兼容

### Outlook
- ✅ 标准ICS导入
- ✅ 位置信息显示
- ✅ 重复事件支持

## 🔄 迁移指南

### 从旧版本升级

1. **地址格式更新**:
   ```javascript
   // 旧格式
   location: "北京市朝阳区"
   
   // 新格式（向后兼容）
   location: "北京市朝阳区"  // 仍然支持
   location: "{geo:39.9042,116.4074;name:北京市朝阳区}"  // 推荐
   ```

2. **RRULE更新**:
   ```javascript
   // 旧格式
   rrule: "FREQ=DAILY;COUNT=5"
   
   // 新格式
   rrule_builder: {
     freq: "DAILY",
     count: 5
   }
   ```

3. **时间格式**:
   ```javascript
   // 确保使用时间戳（秒）
   start_timestamp: Math.floor(Date.now() / 1000)
   ```

## 🚨 重要注意事项

1. **版本控制**: 更新事件时建议传入version字段以避免冲突
2. **时间戳**: 统一使用秒级时间戳，不是毫秒
3. **地址格式**: 推荐使用结构化格式以获得最佳兼容性
4. **并发**: 系统自动处理并发，客户端需要处理409冲突响应

## 📊 性能优化

- **原子文件操作**: 使用临时文件确保写入原子性
- **资源级锁**: 避免全局锁，提高并发性能
- **内存优化**: 及时清理不再使用的锁资源
- **错误恢复**: 完善的异常处理和资源清理

## 🔮 未来计划

- [ ] WebDAV支持
- [ ] 事件搜索API
- [ ] 批量操作API
- [ ] 实时同步通知
- [ ] 性能监控面板