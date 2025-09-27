import { api } from "../../utils/api";
import Toast from "tdesign-miniprogram/toast/index";

Page({
  data: {
    calendars: [],
    showCreateDialog: false,
    newCalendarName: "",
    newCalendarDescription: "",
    newCalendarColor: "#0052D9", // 默认颜色
    colors: ["#0052D9", "#00A870", "#E37318", "#E75541", "#8E44AD"], // 预设颜色
  },

  onLoad() {
    this.loadCalendars();
  },

  async loadCalendars() {
    try {
      const res = await api.listCalendars();
      if (res.errcode === 0) {
        this.setData({
          calendars: res.data.calendars,
        });
      } else {
        Toast({
          context: this,
          selector: "#t-toast",
          message: `加载日历失败: ${res.errmsg}`,
          theme: "error",
        });
      }
    } catch (error) {
      console.error("加载日历异常", error);
      Toast({
        context: this,
        selector: "#t-toast",
        message: "加载日历异常",
        theme: "error",
      });
    }
  },

  showCreateCalendarDialog() {
    this.setData({
      showCreateDialog: true,
      newCalendarName: "",
      newCalendarDescription: "",
      newCalendarColor: "#0052D9",
    });
  },

  closeCreateCalendarDialog() {
    this.setData({
      showCreateDialog: false,
    });
  },

  onNameChange(e: WechatMiniprogram.Input) {
    this.setData({
      newCalendarName: e.detail.value,
    });
  },

  onDescriptionChange(e: WechatMiniprogram.Input) {
    this.setData({
      newCalendarDescription: e.detail.value,
    });
  },

  onColorSelect(e: WechatMiniprogram.CustomEvent) {
    this.setData({
      newCalendarColor: e.currentTarget.dataset.color,
    });
  },

  async createNewCalendar() {
    const {
      newCalendarName,
      newCalendarDescription,
      newCalendarColor,
    } = this.data;
    if (!newCalendarName) {
      Toast({
        context: this,
        selector: "#t-toast",
        message: "日历名称不能为空",
        theme: "warning",
      });
      return;
    }

    try {
      const res = await api.createCalendar({
        name: newCalendarName,
        description: newCalendarDescription,
        color: newCalendarColor,
        timezone: "Asia/Shanghai", // 默认时区
      });

      if (res.errcode === 0) {
        Toast({
          context: this,
          selector: "#t-toast",
          message: "日历创建成功",
          theme: "success",
        });
        this.closeCreateCalendarDialog();
        this.loadCalendars(); // 重新加载日历列表
      } else {
        Toast({
          context: this,
          selector: "#t-toast",
          message: `创建日历失败: ${res.errmsg}`,
          theme: "error",
        });
      }
    } catch (error) {
      console.error("创建日历异常", error);
      Toast({
        context: this,
        selector: "#t-toast",
        message: "创建日历异常",
        theme: "error",
      });
    }
  },

  navigateToCalendarDetail(e: WechatMiniprogram.CustomEvent) {
    const { calendarId } = e.currentTarget.dataset;
    wx.navigateTo({
      url: `/pages/calendar-detail/calendar-detail?calendarId=${calendarId}`,
    });
  },

  async deleteCalendar(e: WechatMiniprogram.CustomEvent) {
    const { id, name } = e.currentTarget.dataset;
    wx.showModal({
      title: "删除日历",
      content: `确定要删除日历 "${name}" 吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            const deleteRes = await api.deleteCalendar(id);
            if (deleteRes.errcode === 0) {
              Toast({
                context: this,
                selector: "#t-toast",
                message: "日历删除成功",
                theme: "success",
              });
              this.loadCalendars();
            } else {
              Toast({
                context: this,
                selector: "#t-toast",
                message: `删除日历失败: ${deleteRes.errmsg}`,
                theme: "error",
              });
            }
          } catch (error) {
            console.error("删除日历异常", error);
            Toast({
              context: this,
              selector: "#t-toast",
              message: "删除日历异常",
              theme: "error",
            });
          }
        }
      },
    });
  },

  navigateToTimestampTool() {
    wx.navigateTo({
      url: '/pages/timestamp-tool/timestamp-tool',
    });
  },

  navigateToRruleTool() {
    wx.navigateTo({
      url: '/pages/rrule-tool/rrule-tool',
    });
  },
});
