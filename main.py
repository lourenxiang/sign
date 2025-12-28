import time
import logging
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from flask import Flask, request, jsonify
import sign

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ========== 日志配置 ==========
# 创建日志目录
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志格式
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建文件处理器（带滚动功能）
file_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, 'app.log'),
    when='midnight',           # 每天午夜轮转
    interval=1,                # 间隔1天
    backupCount=7,            # 保留7天日志
    encoding='utf-8',
    atTime=None               # 在 when='midnight' 时使用本地时间
)
file_handler.setFormatter(log_format)
file_handler.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.INFO)

# 配置应用日志
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)

# 配置sign模块日志
sign_logger = logging.getLogger('sign')
sign_logger.setLevel(logging.DEBUG)
sign_logger.addHandler(file_handler)
sign_logger.addHandler(console_handler)


# ========== 路由 ==========

@app.route('/hello', methods=['GET'])
def hello():
    app.logger.info("hello接口被调用")
    return {'message': 'hello world'}


@app.route('/yjj', methods=['GET'])
def yjj():
    app.logger.info("yjj接口被调用")
    response = jsonify({
        'message': '你个猪'
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response



@app.route('/run', methods=['GET'])
def run():
    text = request.args.get('text', '').strip()
    name = request.args.get('name', 'unknow')
    app.logger.info(f"{name}---run接口被调用，text参数：{text}")

    if not text:
        return jsonify({
            'code': 400,
            'message': '参数 text 不能为空',
            'data': None
        }), 400

    items = [item.strip() for item in text.split(',') if item.strip()]
    total = len(items)

    result = {
        '成功': [],
        '失败': []
    }
    success_count = 0
    fail_count = 0

    app.logger.info(f"{name}---开始并发处理 {total} 个账号（每次最多5个）")

    # -----------------------------
    # 线程池（5个并发）
    # -----------------------------
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_map = {}

        # 提交任务
        for idx, item in enumerate(items, 1):
            parts = item.split(':')

            if len(parts) != 3:
                user = parts[0].strip() if parts else "未知"
                result['失败'].append(f"{user}: 格式错误，应为 user:password:transfer")
                app.logger.error(f"{name}---格式不正确：{item}")
                fail_count += 1
                continue

            user = parts[0].strip()
            password = parts[1].strip()
            transfer = parts[2].strip()

            # 把每个执行任务提交给线程池
            future = executor.submit(sign.sign_and_transfer, name, user, password, transfer)
            future_map[future] = user

            app.logger.info(f"{name}---已提交账号 {user}")

        # 收集线程执行结果
        for future in as_completed(future_map):
            user = future_map[future]
            try:
                res, log = future.result()

                if res:
                    result['成功'].append(f"{user}: {log}")
                    success_count += 1
                    app.logger.info(f"{name}---账号 {user} 处理成功")
                else:
                    result['失败'].append(f"{user}: {log}")
                    fail_count += 1
                    app.logger.warning(f"{name}---账号 {user} 处理失败")

            except Exception as e:
                msg = f"{user}: 处理异常 - {str(e)}"
                result['失败'].append(msg)
                fail_count += 1
                app.logger.error(f"{name}---账号 {user} 处理异常：{str(e)}", exc_info=True)

    # -----------------------------
    # 处理完成
    # -----------------------------
    app.logger.info(
        f"{name}---所有账号处理完成 - 总数：{total}，成功：{success_count}，失败：{fail_count}"
    )

    response = jsonify({
        '总数': total,
        '成功': success_count,
        '失败': fail_count,
        'users': result
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response, 200


@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f"404错误：请求路径不存在")
    return jsonify({'code': 404, 'message': '接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500错误：{str(error)}", exc_info=True)
    return jsonify({'code': 500, 'message': '服务器内部错误'}), 500


if __name__ == '__main__':
    app.logger.info("=" * 50)
    app.logger.info("应用启动")
    app.logger.info("=" * 50)
    app.run(host='0.0.0.0', port=9999, debug=False)
