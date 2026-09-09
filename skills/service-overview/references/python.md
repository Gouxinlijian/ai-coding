# Python 扫描规则

## 入口与路由

- 从 `pyproject.toml`、入口脚本和 ASGI/WSGI 命令找应用入口。
- FastAPI 查 `@app/@router`，Flask 查 `@app.route/Blueprint`，Django 查 `urls.py`，同时查 gRPC servicer、管理命令和定时任务。

## 消息消费

搜索 Celery task、Kafka consumer、pika、Dramatiq、RQ、NATS 等装饰器和注册代码；队列、topic 和 routing key 附配置来源。

## 外部调用

搜索 requests/httpx/aiohttp、gRPC stub、SDK client 与消息发布。区分只定义 client 和在主流程中实际调用。

## 数据层与表名

Django 查 Model `Meta.db_table` 和 migrations；SQLAlchemy 查 `__tablename__`、Table 和 Alembic；其他 ORM 查显式 collection/table 元数据。无显式名只可按框架命名规则推断并标注置信度。

## 配置

读取 Django settings、Pydantic Settings、dotenv、`os.getenv/os.environ`、YAML/TOML 和部署参数。区分默认 settings、环境覆盖与 secrets 挂载。


