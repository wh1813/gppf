import os
import subprocess
import shutil
import sys

def build():
    print("🚀 开始打包流程...")

    # 自动获取脚本所在目录作为项目根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # 1. 编译前端
    print("📦 正在编译前端代码...")
    frontend_path = os.path.join(base_dir, "frontend")
    
    if not os.path.exists(frontend_path):
        print(f"❌ 错误：找不到前端目录 {frontend_path}")
        return

    # 确保安装了依赖并执行 build
    try:
        subprocess.run("npm run build", cwd=frontend_path, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ 前端编译失败，请检查 Node.js 环境及依赖是否安装（npm install）")
        return

    # 2. 移动前端资源到后端可访问的目录
    dist_path = os.path.join(frontend_path, "dist")
    target_dist = os.path.join(base_dir, "frontend_dist")
    
    if not os.path.exists(dist_path):
        print(f"❌ 错误：前端编译未生成 dist 文件夹")
        return

    if os.path.exists(target_dist):
        shutil.rmtree(target_dist)
    shutil.copytree(dist_path, target_dist)
    print("✅ 前端资源已就绪")

    # 3. 使用 PyInstaller 打包
    print("🛠️ 正在生成执行文件 (此过程较慢，请稍候)...")
    
    # 获取 run_app.py 的绝对路径
    run_app_path = os.path.join(base_dir, "run_app.py")

    if not os.path.exists(run_app_path):
        print(f"❌ 错误：找不到启动入口文件 {run_app_path}")
        return

    # 构造打包命令
    # 🌟 修复：通过 --exclude-module 排除冲突的 Qt 库和不需要的庞大库
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--name=A股智能研判终端",
        f"--add-data=frontend_dist{os.pathsep}frontend_dist",
        f"--add-data=.env{os.pathsep}.",
        "--exclude-module=PyQt5",
        "--exclude-module=PySide6",
        "--exclude-module=PyQt6",
        "--exclude-module=PySide2",
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--clean",
        "run_app.py"
    ]
    
    subprocess.run(" ".join(cmd), shell=True, check=True)

    print("\n✨ 打包完成！")
    print(f"📁 请在目录 {os.path.join(base_dir, 'dist')} 下查看 'A股智能研判终端.exe'")

if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print(f"❌ 打包意外终止: {e}")