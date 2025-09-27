export const BASE_URL = "https://ics.wwen.work";

interface ApiResponse<T> {
  errcode: number;
  errmsg: string;
  data: T;
}

function request<T>(
  url: string,
  method: "GET" | "POST" | "PUT" | "DELETE",
  data?: any
): Promise<ApiResponse<T>> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: {
        "Content-Type": "application/json",
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data as ApiResponse<T>);
        } else {
          reject(res.data);
        }
      },
      fail: (err) => {
        reject(err);
      },
    });
  });
}

export const api = {
  // 日历管理
  createCalendar: (data: any) => request<any>("/calendars", "POST", data),
  listCalendars: () => request<{ calendars: any[] }>("/calendars", "GET"),
  getCalendar: (calendarId: string) =>
    request<any>(`/calendars/${calendarId}`, "GET"),
  deleteCalendar: (calendarId: string) =>
    request<any>(`/calendars/${calendarId}`, "DELETE"),

  // 事件管理
  createEvent: (calendarId: string, data: any) =>
    request<any>(`/calendars/${calendarId}/events`, "POST", data),
  getCalendarEvents: (calendarId: string, params?: any) =>
    request<{ events: any[] }>(
      `/calendars/${calendarId}/events`,
      "GET",
      params
    ),
  getEvent: (calendarId: string, eventUid: string) =>
    request<any>(`/calendars/${calendarId}/events/${eventUid}`, "GET"),
  updateEvent: (calendarId: string, eventUid: string, data: any) =>
    request<any>(`/calendars/${calendarId}/events/${eventUid}`, "PUT", data),
  deleteEvent: (calendarId: string, eventUid: string) =>
    request<any>(`/calendars/${calendarId}/events/${eventUid}`, "DELETE"),

  // 分类管理
  createCategory: (calendarId: string, data: any) =>
    request<any>(`/calendars/${calendarId}/categories`, "POST", data),
  getCategories: (calendarId: string) =>
    request<{ categories: any[] }>(
      `/calendars/${calendarId}/categories`,
      "GET"
    ),
  deleteCategory: (calendarId: string, categoryId: string) =>
    request<any>(`/calendars/${calendarId}/categories/${categoryId}`, "DELETE"),

  // 统计信息
  getCalendarStats: (calendarId: string) =>
    request<any>(`/calendars/${calendarId}/stats`, "GET"),

  // 工具
  getCurrentTimestamp: () => request<any>("/utils/timestamp", "GET"),
  convertTimestamp: (timestamp: number) =>
    request<any>(`/utils/timestamp/${timestamp}`, "GET"),
  previewRrule: (data: any) =>
    request<any>("/utils/rrule/preview", "POST", data),
  healthCheck: () => request<any>("/health", "GET"),
};
