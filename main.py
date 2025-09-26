import sys
import os

# 获取当前脚本的目录（main.py所在的目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
print(current_dir )
# 将该目录添加到sys.path
sys.path.insert(0, current_dir)

import sys
import uvicorn
from src.configs.server_config import FASTAPI_HOST, FASTAPI_PORT

if __name__ == "__main__":
    # 启动后，修改代码，不用重启服务，热重载
    # uvicorn.run(app="src.api.app:app", host=FASTAPI_SERVER["host"], port=FASTAPI_SERVER["port"], reload=True)

    print("=== Python Application Starting ===")
    print(f"Uvicorn running on: http://{FASTAPI_HOST}:{FASTAPI_PORT}")  # 明确的启动信息
    print("Application startup complete")
    print("账户:admin  密码:000000")

    sys.stdout.flush()

    uvicorn.run(app="src.api.app:app", host=FASTAPI_HOST, port=FASTAPI_PORT)

    

