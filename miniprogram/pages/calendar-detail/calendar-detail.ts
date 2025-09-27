import { api, BASE_URL } from '../../utils/api';
import Toast from 'tdesign-miniprogram/toast/index';
import { EventType } from '../../types/event'; // 假设你有一个types/event.ts文件定义EventType

Page({
  data: {
    calendarId: '',
    calendarDetails: null,
    events: [],
    categories: [],
    stats: null,
    activeTab: 'events', // 'events', 'categories', 'stats'

    // 创建事件相关
    showCreateEventDialog: false,
    newEventTitle: '',
    newEventDescription: '',
    newEventLocation: '',
    newEventEventType: EventType.TIMED,
    newEventStartTimestamp: '',
    newEventEndTimestamp: '',
    newEventDurationMinutes: '',
    newEventCategoryId: '',
    eventTypes: [
      { label: '全天事件', value: EventType.ALL_DAY },
      { label: '时段事件', value: EventType.TIMED },
      { label: '区间事件', value: EventType.DURATION },
    ],

    // 编辑事件相关
    showEditEventDialog: false,
    editingEventUid: '',
    editingEventTitle: '',
    editingEventDescription: '',
    editingEventLocation: '',
    editingEventEventType: EventType.TIMED,
    editingEventStartTimestamp: '',
    editingEventEndTimestamp: '',
    editingEventDurationMinutes: '',
    editingEventCategoryId: '',
    editingEventVersion: 0,

    // 创建分类相关
    showCreateCategoryDialog: false,
    newCategoryName: '',
    newCategoryDescription: '',
    newCategoryColor: '#0052D9',
    colors: ['#0052D9', '#00A870', '#E37318', '#E75541', '#8E44AD'], // 预设颜色
  },

  onLoad(options: { calendarId?: string }) {
    const { calendarId } = options;
    if (calendarId) {
      this.setData({ calendarId });
      this.loadPageData(calendarId);
    } else {
      Toast({
        context: this,
        selector: '#t-toast',
        message: '日历ID缺失',
        theme: 'error',
      });
      wx.navigateBack();
    }
  },

  onShow() {
    // 页面显示时刷新数据，确保从其他页面返回时数据是最新的
    if (this.data.calendarId) {
      this.loadPageData(this.data.calendarId);
    }
  },

  async loadPageData(calendarId: string) {
    wx.showLoading({ title: '加载中...' });
    await Promise.all([
      this.loadCalendarDetails(calendarId),
      this.loadEvents(calendarId),
      this.loadCategories(calendarId),
      this.loadStats(calendarId),
    ]);
    wx.hideLoading();
  },

  async loadCalendarDetails(calendarId: string) {
    try {
      const res = await api.getCalendar(calendarId);
      if (res.errcode === 0) {
        const calendar = res.data;
        // 构建订阅和下载URL
        const subscribeUrl = `${BASE_URL}/calendars/${calendar.id}/subscribe`;
        const downloadUrl = `${BASE_URL}/calendars/${calendar.id}/download`;
        this.setData({
          calendarDetails: {
            ...calendar,
            subscribeUrl,
            downloadUrl,
          },
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `加载日历详情失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('加载日历详情异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '加载日历详情异常',
        theme: 'error',
      });
    }
  },

  async loadEvents(calendarId: string) {
    try {
      const res = await api.getCalendarEvents(calendarId);
      if (res.errcode === 0) {
        const eventsWithCategoryNames = res.data.events.map((event: any) => {
          const category = this.data.categories.find((cat: any) => cat.id === event.category_id);
          return {
            ...event,
            categoryName: category ? category.name : '未知',
          };
        });
        this.setData({ events: eventsWithCategoryNames });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `加载事件失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('加载事件异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '加载事件异常',
        theme: 'error',
      });
    }
  },

  async loadCategories(calendarId: string) {
    try {
      const res = await api.getCategories(calendarId);
      if (res.errcode === 0) {
        this.setData({ categories: res.data.categories });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `加载分类失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('加载分类异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '加载分类异常',
        theme: 'error',
      });
    }
  },

  async loadStats(calendarId: string) {
    try {
      const res = await api.getCalendarStats(calendarId);
      if (res.errcode === 0) {
        this.setData({ stats: res.data });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `加载统计失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('加载统计异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '加载统计异常',
        theme: 'error',
      });
    }
  },

  onTabChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({
      activeTab: e.detail.value,
    });
  },

  // 事件相关方法
  showCreateEventDialog() {
    this.setData({
      showCreateEventDialog: true,
      newEventTitle: '',
      newEventDescription: '',
      newEventLocation: '',
      newEventEventType: EventType.TIMED,
      newEventStartTimestamp: '',
      newEventEndTimestamp: '',
      newEventDurationMinutes: '',
      newEventCategoryId: '',
    });
  },

  closeCreateEventDialog() {
    this.setData({ showCreateEventDialog: false });
  },

  async editEvent(e: WechatMiniprogram.CustomEvent) {
    const { calendarId } = this.data;
    const { uid } = e.currentTarget.dataset;
    try {
      const res = await api.getEvent(calendarId, uid);
      if (res.errcode === 0) {
        const event = res.data;
        this.setData({
          showEditEventDialog: true,
          editingEventUid: event.uid,
          editingEventTitle: event.title,
          editingEventDescription: event.description || '',
          editingEventLocation: event.location || '',
          editingEventEventType: event.event_type,
          editingEventStartTimestamp: event.start_timestamp ? String(event.start_timestamp) : '',
          editingEventEndTimestamp: event.end_timestamp ? String(event.end_timestamp) : '',
          editingEventDurationMinutes: event.duration_minutes ? String(event.duration_minutes) : '',
          editingEventCategoryId: event.category_id || '',
          editingEventVersion: event.version,
        });
      } else {
        Toast({ context: this, selector: '#t-toast', message: `获取事件详情失败: ${res.errmsg}`, theme: 'error' });
      }
    } catch (error) {
      console.error('获取事件详情异常', error);
      Toast({ context: this, selector: '#t-toast', message: '获取事件详情异常', theme: 'error' });
    }
  },

  closeEditEventDialog() {
    this.setData({ showEditEventDialog: false });
  },

  onEditingEventTitleChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventTitle: e.detail.value });
  },
  onEditingEventDescriptionChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventDescription: e.detail.value });
  },
  onEditingEventLocationChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventLocation: e.detail.value });
  },
  onEditingEventTypeChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({ editingEventEventType: e.detail.value });
  },
  onEditingEventStartTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventStartTimestamp: e.detail.value });
  },
  onEditingEventEndTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventEndTimestamp: e.detail.value });
  },
  onEditingEventDurationMinutesChange(e: WechatMiniprogram.Input) {
    this.setData({ editingEventDurationMinutes: e.detail.value });
  },
  onEditingEventCategoryChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({ editingEventCategoryId: e.detail.value });
  },

  async updateExistingEvent() {
    const {
      calendarId,
      editingEventUid,
      editingEventTitle,
      editingEventDescription,
      editingEventLocation,
      editingEventEventType,
      editingEventStartTimestamp,
      editingEventEndTimestamp,
      editingEventDurationMinutes,
      editingEventCategoryId,
      editingEventVersion,
    } = this.data;

    if (!editingEventTitle) {
      Toast({ context: this, selector: '#t-toast', message: '事件标题不能为空', theme: 'warning' });
      return;
    }

    const eventData: any = {
      title: editingEventTitle,
      description: editingEventDescription,
      location: editingEventLocation,
      event_type: editingEventEventType.toLowerCase(), // 转换为小写
      category_id: editingEventCategoryId || undefined,
      version: editingEventVersion,
    };

    if (editingEventEventType === EventType.ALL_DAY) {
      if (!editingEventStartTimestamp) {
        Toast({ context: this, selector: '#t-toast', message: '全天事件必须提供开始时间戳', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(editingEventStartTimestamp);
    } else if (editingEventEventType === EventType.TIMED) {
      if (!editingEventStartTimestamp || !editingEventEndTimestamp) {
        Toast({ context: this, selector: '#t-toast', message: '时段事件必须提供开始和结束时间戳', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(editingEventStartTimestamp);
      eventData.end_timestamp = parseInt(editingEventEndTimestamp);
    } else if (editingEventEventType === EventType.DURATION) {
      if (!editingEventStartTimestamp || !editingEventDurationMinutes) {
        Toast({ context: this, selector: '#t-toast', message: '区间事件必须提供开始时间戳和持续时长', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(editingEventStartTimestamp);
      eventData.duration_minutes = parseInt(editingEventDurationMinutes);
    }

    try {
      const res = await api.updateEvent(calendarId, editingEventUid, eventData);
      if (res.errcode === 0) {
        Toast({ context: this, selector: '#t-toast', message: '事件更新成功', theme: 'success' });
        this.closeEditEventDialog();
        this.loadEvents(calendarId); // 刷新事件列表
        this.loadStats(calendarId); // 刷新统计
      } else {
        Toast({ context: this, selector: '#t-toast', message: `更新事件失败: ${res.errmsg}`, theme: 'error' });
      }
    } catch (error) {
      console.error('更新事件异常', error);
      Toast({ context: this, selector: '#t-toast', message: '更新事件异常', theme: 'error' });
    }
  },

  onEventTitleChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventTitle: e.detail.value });
  },
  onEventDescriptionChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventDescription: e.detail.value });
  },
  onEventLocationChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventLocation: e.detail.value });
  },
  onEventTypeChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({ newEventEventType: e.detail.value });
  },
  onEventStartTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventStartTimestamp: e.detail.value });
  },
  onEventEndTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventEndTimestamp: e.detail.value });
  },
  onEventDurationMinutesChange(e: WechatMiniprogram.Input) {
    this.setData({ newEventDurationMinutes: e.detail.value });
  },
  onEventCategoryChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({ newEventCategoryId: e.detail.value });
  },

  async createNewEvent() {
    const {
      calendarId,
      newEventTitle,
      newEventDescription,
      newEventLocation,
      newEventEventType,
      newEventStartTimestamp,
      newEventEndTimestamp,
      newEventDurationMinutes,
      newEventCategoryId,
    } = this.data;

    if (!newEventTitle) {
      Toast({ context: this, selector: '#t-toast', message: '事件标题不能为空', theme: 'warning' });
      return;
    }

    const eventData: any = {
      title: newEventTitle,
      description: newEventDescription,
      location: newEventLocation,
      event_type: newEventEventType.toLowerCase(), // 转换为小写
      category_id: newEventCategoryId || undefined,
    };

    if (newEventEventType === EventType.ALL_DAY) {
      if (!newEventStartTimestamp) {
        Toast({ context: this, selector: '#t-toast', message: '全天事件必须提供开始时间戳', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(newEventStartTimestamp);
    } else if (newEventEventType === EventType.TIMED) {
      if (!newEventStartTimestamp || !newEventEndTimestamp) {
        Toast({ context: this, selector: '#t-toast', message: '时段事件必须提供开始和结束时间戳', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(newEventStartTimestamp);
      eventData.end_timestamp = parseInt(newEventEndTimestamp);
    } else if (newEventEventType === EventType.DURATION) {
      if (!newEventStartTimestamp || !newEventDurationMinutes) {
        Toast({ context: this, selector: '#t-toast', message: '区间事件必须提供开始时间戳和持续时长', theme: 'warning' });
        return;
      }
      eventData.start_timestamp = parseInt(newEventStartTimestamp);
      eventData.duration_minutes = parseInt(newEventDurationMinutes);
    }

    try {
      const res = await api.createEvent(calendarId, eventData);
      if (res.errcode === 0) {
        Toast({ context: this, selector: '#t-toast', message: '事件创建成功', theme: 'success' });
        this.closeCreateEventDialog();
        this.loadEvents(calendarId); // 刷新事件列表
        this.loadStats(calendarId); // 刷新统计
      } else {
        Toast({ context: this, selector: '#t-toast', message: `创建事件失败: ${res.errmsg}`, theme: 'error' });
      }
    } catch (error) {
      console.error('创建事件异常', error);
      Toast({ context: this, selector: '#t-toast', message: '创建事件异常', theme: 'error' });
    }
  },

  async deleteEvent(e: WechatMiniprogram.CustomEvent) {
    const { calendarId } = this.data;
    const { uid, title } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除事件',
      content: `确定要删除事件 "${title}" 吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const deleteRes = await api.deleteEvent(calendarId, uid);
            if (deleteRes.errcode === 0) {
              Toast({ context: this, selector: '#t-toast', message: '事件删除成功', theme: 'success' });
              this.loadEvents(calendarId);
              this.loadStats(calendarId);
            } else {
              Toast({ context: this, selector: '#t-toast', message: `删除事件失败: ${deleteRes.errmsg}`, theme: 'error' });
            }
          } catch (error) {
            console.error('删除事件异常', error);
            Toast({ context: this, selector: '#t-toast', message: '删除事件异常', theme: 'error' });
          }
        }
      },
    });
  },

  // 分类相关方法
  showCreateCategoryDialog() {
    this.setData({
      showCreateCategoryDialog: true,
      newCategoryName: '',
      newCategoryDescription: '',
      newCategoryColor: '#0052D9',
    });
  },

  closeCreateCategoryDialog() {
    this.setData({ showCreateCategoryDialog: false });
  },

  onCategoryNameChange(e: WechatMiniprogram.Input) {
    this.setData({ newCategoryName: e.detail.value });
  },
  onCategoryDescriptionChange(e: WechatMiniprogram.Input) {
    this.setData({ newCategoryDescription: e.detail.value });
  },
  onCategoryColorSelect(e: WechatMiniprogram.CustomEvent) {
    this.setData({ newCategoryColor: e.currentTarget.dataset.color });
  },

  async createNewCategory() {
    const { calendarId, newCategoryName, newCategoryDescription, newCategoryColor } = this.data;

    if (!newCategoryName) {
      Toast({ context: this, selector: '#t-toast', message: '分类名称不能为空', theme: 'warning' });
      return;
    }

    try {
      const res = await api.createCategory(calendarId, {
        name: newCategoryName,
        description: newCategoryDescription,
        color: newCategoryColor,
      });
      if (res.errcode === 0) {
        Toast({ context: this, selector: '#t-toast', message: '分类创建成功', theme: 'success' });
        this.closeCreateCategoryDialog();
        this.loadCategories(calendarId); // 刷新分类列表
        this.loadStats(calendarId); // 刷新统计
      } else {
        Toast({ context: this, selector: '#t-toast', message: `创建分类失败: ${res.errmsg}`, theme: 'error' });
      }
    } catch (error) {
      console.error('创建分类异常', error);
      Toast({ context: this, selector: '#t-toast', message: '创建分类异常', theme: 'error' });
    }
  },

  copySubscribeUrl() {
    const { calendarDetails } = this.data;
    if (calendarDetails && calendarDetails.subscribeUrl) {
      wx.setClipboardData({
        data: calendarDetails.subscribeUrl,
        success: () => {
          Toast({ context: this, selector: '#t-toast', message: '订阅链接已复制', theme: 'success' });
        },
        fail: (err) => {
          console.error('复制失败', err);
          Toast({ context: this, selector: '#t-toast', message: '复制失败', theme: 'error' });
        },
      });
    }
  },

  async deleteCategory(e: WechatMiniprogram.CustomEvent) {
    const { calendarId } = this.data;
    const { id, name } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除分类',
      content: `确定要删除分类 "${name}" 吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const deleteRes = await api.deleteCategory(calendarId, id);
            if (deleteRes.errcode === 0) {
              Toast({ context: this, selector: '#t-toast', message: '分类删除成功', theme: 'success' });
              this.loadCategories(calendarId);
              this.loadStats(calendarId);
            } else {
              Toast({ context: this, selector: '#t-toast', message: `删除分类失败: ${deleteRes.errmsg}`, theme: 'error' });
            }
          } catch (error) {
            console.error('删除分类异常', error);
            Toast({ context: this, selector: '#t-toast', message: '删除分类异常', theme: 'error' });
          }
        }
      },
    });
  },
});