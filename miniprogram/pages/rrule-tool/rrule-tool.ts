import { api } from '../../utils/api';
import Toast from 'tdesign-miniprogram/toast/index';

Page({
  data: {
    freqOptions: [
      { label: '每天', value: 'DAILY' },
      { label: '每周', value: 'WEEKLY' },
      { label: '每月', value: 'MONTHLY' },
      { label: '每年', value: 'YEARLY' },
    ],
    freq: 'DAILY',
    interval: 1,
    count: '',
    untilTimestamp: '',
    byWeekdayOptions: [
      { label: '周一', value: 'MO' },
      { label: '周二', value: 'TU' },
      { label: '周三', value: 'WE' },
      { label: '周四', value: 'TH' },
      { label: '周五', value: 'FR' },
      { label: '周六', value: 'SA' },
      { label: '周日', value: 'SU' },
    ],
    byWeekday: [],
    byMonthday: '',
    byMonth: '',
    rruleString: '',
    rruleExamples: null as any,
  },

  onLoad() {
    // Optionally load some default examples or initial state
  },

  onFreqChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({
      freq: e.detail.value,
    });
  },

  onIntervalChange(e: WechatMiniprogram.Input) {
    this.setData({
      interval: parseInt(e.detail.value) || 1,
    });
  },

  onCountChange(e: WechatMiniprogram.Input) {
    this.setData({
      count: e.detail.value,
    });
  },

  onUntilTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({
      untilTimestamp: e.detail.value,
    });
  },

  onByWeekdayChange(e: WechatMiniprogram.CustomEvent) {
    this.setData({
      byWeekday: e.detail.value,
    });
  },

  onByMonthdayChange(e: WechatMiniprogram.Input) {
    this.setData({
      byMonthday: e.detail.value,
    });
  },

  onByMonthChange(e: WechatMiniprogram.Input) {
    this.setData({
      byMonth: e.detail.value,
    });
  },

  async previewRrule() {
    const { freq, interval, count, untilTimestamp, byWeekday, byMonthday, byMonth } = this.data;

    const rruleBuilder: any = {
      freq: freq,
      interval: interval,
    };

    if (count) {
      rruleBuilder.count = parseInt(count);
    }
    if (untilTimestamp) {
      rruleBuilder.until_timestamp = parseInt(untilTimestamp);
    }
    if (byWeekday.length > 0) {
      rruleBuilder.by_weekday = byWeekday;
    }
    if (byMonthday) {
      rruleBuilder.by_monthday = parseInt(byMonthday);
    }
    if (byMonth) {
      rruleBuilder.by_month = parseInt(byMonth);
    }

    try {
      const res = await api.previewRrule(rruleBuilder);
      if (res.errcode === 0) {
        this.setData({
          rruleString: res.data.rrule_string,
          rruleExamples: res.data.examples,
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `预览RRULE失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('预览RRULE异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '预览RRULE异常',
        theme: 'error',
      });
    }
  },
});