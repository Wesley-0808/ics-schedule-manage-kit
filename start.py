#!/usr/bin/env python3
"""
ICS日程管理系统启动脚本
提供更友好的启动方式和配置选项
"""

import argparse
import os
import sys
import uvicorn
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'icalendar', 
        'python-multipart', 'aiofiles', 'python-dateutil', 'pytz'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def create_directories():
    """创建必要的目录"""
    directories = ['calendars', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 目录已创建: {directory}/")

def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    ICS日程管理系统                           ║
║                                                              ║
║  🗓️  功能完整的日程管理系统                                  ║
║  📱  兼容Apple日历、Google Calendar、Outlook                ║
║  🔗  支持日历订阅和实时同步                                  ║
║  🎨  支持自定义分类和颜色                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    parser = argparse.ArgumentParser(description='ICS日程管理系统')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口 (默认: 8000)')
    parser.add_argument('--reload', action='store_true', help='启用自动重载 (开发模式)')
    parser.add_argument('--log-level', default='info', 
                       choices=['critical', 'error', 'warning', 'info', 'debug'],
                       help='日志级别 (默认: info)')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数 (默认: 1)')
    parser.add_argument('--check-deps', action='store_true', help='仅检查依赖')
    
    args = parser.parse_args()
    
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    if args.check_deps:
        print("✅ 所有依赖已正确安装")
        return
    
    # 创建必要目录
    create_directories()
    
    # 检查主应用文件
    if not os.path.exists('main.py'):
        print("❌ 找不到 main.py 文件")
        sys.exit(1)
    
    print(f"🚀 启动服务...")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   API文档: http://{args.host}:{args.port}/docs")
    print(f"   日志级别: {args.log_level}")
    
    if args.reload:
        print("   模式: 开发模式 (自动重载)")
    
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        # 启动服务
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=args.workers if not args.reload else 1,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()