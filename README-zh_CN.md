# ICS日程管理系统

一个功能完整的ICS日程管理系统，基于FastAPI构建，兼容Apple日历、Google Calendar、Outlook Calendar等主流日历应用。

## ✨ 主要特性

- 🗓️ **多日历支持**: 支持创建和管理多个独立的日历
- 📱 **跨平台兼容**: 完美兼容Apple日历、Google Calendar、Outlook等
- 🔗 **日历订阅**: 支持标准ICS订阅，实时同步更新
- 📍 **位置支持**: 支持地理位置信息，包括地址和GPS坐标
- ⏰ **多种事件类型**: 
  - 全天事件 (All-day events)
  - 时段事件 (Timed events) 
  - 区间事件 (Duration events)
- 🎨 **自定义分类**: 支持自定义日程分类和颜色标记
- 🔔 **提醒功能**: 支持事件提醒设置
- 🔄 **重复事件**: 支持RRULE重复规则
- 🚀 **RESTful API**: 完整的REST API接口
- 📊 **统计分析**: 提供日历和事件的统计信息

## 🛠️ 技术栈

- **后端框架**: FastAPI
- **ICS处理**: icalendar
- **数据验证**: Pydantic
- **时区处理**: pytz
- **异步支持**: uvicorn

## 📦 安装和运行

### 1. 克隆项目

```bash
git clone <repository-url>
cd ics-schedule-manage-kit
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 4. 查看API文档

访问 `http://localhost:8000/docs` 查看交互式API文档

## 🚀 快速开始

### 运行示例

```bash
python example_usage.py
```

这将创建一个示例日历，包含各种类型的事件，演示系统的完整功能。

### 基本使用流程

1. **创建日历**
```bash
curl -X POST "http://localhost:8000/calendars" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的日历",
    "description": "个人日程安排",
    "color": "#FF6B6B",
    "timezone": "Asia/Shanghai"
  }'
```

2. **添加事件**
```bash
curl -X POST "http://localhost:8000/calendars/{calendar_id}/events" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "重要会议",
    "description": "项目讨论会议",
    "event_type": "timed",
    "start_datetime": "2024-01-15T10:00:00",
    "end_datetime": "2024-01-15T11:30:00",
    "location": {
      "name": "会议室A",
      "address": "公司大楼3楼"
    },
    "alarm_minutes": 15
  }'
```

3. **订阅日历**
```
订阅URL: http://localhost:8000/calendars/{calendar_id}/subscribe
```

## 📚 API文档

### 日历管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/calendars` | 创建新日历 |
| GET | `/calendars` | 获取所有日历 |
| GET | `/calendars/{id}` | 获取日历详情 |
| DELETE | `/calendars/{id}` | 删除日历 |

### 事件管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/calendars/{id}/events` | 创建事件 |
| GET | `/calendars/{id}/events` | 获取事件列表 |
| GET | `/calendars/{id}/events/{uid}` | 获取事件详情 |
| PUT | `/calendars/{id}/events/{uid}` | 更新事件 |
| DELETE | `/calendars/{id}/events/{uid}` | 删除事件 |

### 分类管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/calendars/{id}/categories` | 创建分类 |
| GET | `/calendars/{id}/categories` | 获取分类列表 |

### 日历订阅

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/calendars/{id}/subscribe` | 日历订阅(ICS格式) |
| GET | `/calendars/{id}/download` | 下载日历文件 |

### 统计信息

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/calendars/{id}/stats` | 获取日历统计 |
| GET | `/health` | 系统健康检查 |

## 📱 在日历应用中使用

### Apple 日历 (iOS/macOS)
1. 打开日历应用
2. 点击"日历" → "添加账户" → "其他"
3. 选择"添加已订阅的日历"
4. 输入订阅URL: `http://localhost:8000/calendars/{calendar_id}/subscribe`

### Google Calendar
1. 打开Google Calendar
2. 点击左侧"其他日历"旁的"+"
3. 选择"通过URL添加"
4. 输入订阅URL: `http://localhost:8000/calendars/{calendar_id}/subscribe`

### Microsoft Outlook
1. 打开Outlook
2. 点击"添加日历" → "从Internet添加"
3. 输入订阅URL: `http://localhost:8000/calendars/{calendar_id}/subscribe`

## 🎯 事件类型说明

### 1. 全天事件 (all_day)
适用于生日、节假日等不需要具体时间的事件
```json
{
  "event_type": "all_day",
  "start_date": "2024-01-15",
  "end_date": "2024-01-15"
}
```

### 2. 时段事件 (timed)
适用于会议、约会等有明确开始和结束时间的事件
```json
{
  "event_type": "timed",
  "start_datetime": "2024-01-15T10:00:00",
  "end_datetime": "2024-01-15T11:30:00"
}
```

### 3. 区间事件 (duration)
适用于只知道开始时间和持续时长的事件
```json
{
  "event_type": "duration",
  "start_datetime": "2024-01-15T10:00:00",
  "duration_minutes": 90
}
```

## 🔄 重复事件

支持标准RRULE格式的重复规则：

```json
{
  "rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR",  // 每周一、三、五
  "rrule": "FREQ=MONTHLY;BYMONTHDAY=15",  // 每月15日
  "rrule": "FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=25"  // 每年12月25日
}
```

## 📍 位置信息

支持丰富的位置信息：

```json
{
  "location": {
    "name": "会议室A",
    "address": "北京市朝阳区xxx路123号",
    "latitude": 39.9042,
    "longitude": 116.4074
  }
}
```

## 🎨 自定义分类

支持为日历创建自定义分类：

```json
{
  "name": "工作会议",
  "color": "#FF6B6B",
  "description": "所有工作相关的会议"
}
```

## 📊 数据存储

- 日历元数据存储在 `calendars/metadata.json`
- 每个日历对应一个独立的ICS文件
- 支持标准ICS格式，确保跨平台兼容性

## 🔧 配置选项

### 时区设置
系统支持全球时区，默认为 `Asia/Shanghai`

### 颜色主题
支持十六进制颜色代码，如 `#FF6B6B`

### 提醒设置
支持分钟级提醒设置，如提前15分钟、1小时、1天等

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 常见问题

### Q: 如何修改服务端口？
A: 修改 `main.py` 中的 `uvicorn.run(app, host="0.0.0.0", port=8000)` 中的端口号

### Q: 日历不显示事件怎么办？
A: 检查时区设置是否正确，确保事件时间格式符合ISO 8601标准

### Q: 如何备份日历数据？
A: 备份 `calendars/` 目录下的所有文件即可

### Q: 支持哪些重复规则？
A: 支持标准RFC 5545 RRULE格式的所有重复规则

## 📞 支持

如有问题或建议，请提交 Issue 或联系开发团队。