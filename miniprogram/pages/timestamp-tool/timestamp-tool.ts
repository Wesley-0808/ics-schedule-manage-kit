import { api } from '../../utils/api';
import Toast from 'tdesign-miniprogram/toast/index';

Page({
  data: {
    currentTimestamp: 0,
    currentIsoFormat: '',
    inputTimestamp: '',
    convertedTimestamp: null as any,
  },

  onLoad() {
    this.loadCurrentTimestamp();
  },

  async loadCurrentTimestamp() {
    try {
      const res = await api.getCurrentTimestamp();
      if (res.errcode === 0) {
        this.setData({
          currentTimestamp: res.data.timestamp,
          currentIsoFormat: res.data.iso_format,
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `获取当前时间戳失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('获取当前时间戳异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '获取当前时间戳异常',
        theme: 'error',
      });
    }
  },

  onInputTimestampChange(e: WechatMiniprogram.Input) {
    this.setData({
      inputTimestamp: e.detail.value,
    });
  },

  async convertTimestamp() {
    const timestamp = parseInt(this.data.inputTimestamp);
    if (isNaN(timestamp)) {
      Toast({
        context: this,
        selector: '#t-toast',
        message: '请输入有效的时间戳',
        theme: 'warning',
      });
      return;
    }

    try {
      const res = await api.convertTimestamp(timestamp);
      if (res.errcode === 0) {
        this.setData({
          convertedTimestamp: res.data,
        });
      } else {
        Toast({
          context: this,
          selector: '#t-toast',
          message: `时间戳转换失败: ${res.errmsg}`,
          theme: 'error',
        });
      }
    } catch (error) {
      console.error('时间戳转换异常', error);
      Toast({
        context: this,
        selector: '#t-toast',
        message: '时间戳转换异常',
        theme: 'error',
      });
    }
  },
});