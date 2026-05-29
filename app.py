from flask import Flask, request, Response, stream_with_context
import requests
import os
import json

app = Flask(__name__)

# Target API base URL from environment variable
TARGET_API = os.getenv("TARGET_API", "https://huggingface.co")

# Path mappings from environment variable
def get_path_mappings():
    mappings_str = os.getenv("PATH_MAPPINGS", '{"/": "/"}')
    try:
        return json.loads(mappings_str)
    except json.JSONDecodeError:
        return {"/": "/"}

PATH_MAPPINGS = get_path_mappings()


@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    # Construct the full path
    full_path = f"/{path}"

    # Apply path mapping if matches
    for original_path, new_path in PATH_MAPPINGS.items():
        if full_path.startswith(original_path):
            full_path = full_path.replace(original_path, new_path, 1)
            break

    # Construct target URL
    target_url = f"{TARGET_API}{full_path}"

    # ==================== HEADER 过滤逻辑 ====================
    # 定义允许转发的必要 Header 白名单（统一小写，方便匹配）
    ESSENTIAL_HEADERS = {'content-type', 'accept', 'user-agent'}
    
    headers = {}
    for key, value in request.headers.items():
        if key.lower() in ESSENTIAL_HEADERS:
            headers[key] = value
    # ========================================================

    # 统一构建 requests 请求参数
    request_kwargs = {
        "method": request.method,
        "url": target_url,
        "headers": headers,
        "params": request.args,
        "stream": True
    }

    # 仅在有请求体的动词中带上 JSON 数据
    if request.method in ['POST', 'PUT', 'PATCH']:
        request_kwargs["json"] = request.get_json(silent=True)

    # 发起请求
    response = requests.request(**request_kwargs)

    # Create a response with the same status code, headers, and streaming content
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk

    # Create flask response
    proxy_response = Response(
        stream_with_context(generate()),
        status=response.status_code
    )

    # Forward response headers
    for key, value in response.headers.items():
        if key.lower() not in ('content-length', 'transfer-encoding', 'connection'):
            proxy_response.headers[key] = value

    return proxy_response


@app.route('/', methods=['GET'])
def index():
    return "service running."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=False)