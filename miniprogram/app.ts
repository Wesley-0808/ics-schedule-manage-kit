App({
  onLaunch() {
    // 应用启动时执行
    console.log('App Launch');
  },
  onShow() {
    // 应用显示时执行
    console.log('App Show');
  },
  onHide() {
    // 应用隐藏时执行
    console.log('App Hide');
  },
  onError(msg) {
    // 应用发生错误时执行
    console.error('App Error:', msg);
  },
  globalData: {
    // 全局数据
    userInfo: null,
  },
});