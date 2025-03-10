# 多智能体系统

这是一个基于Python的多智能体系统，支持多个专门化代理协同工作。

## 项目结构

```
multiagent/
├── app/                    # 主应用目录
│   ├── api/               # API 接口定义
│   ├── core/             # 核心业务逻辑
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic 模型
│   ├── services/         # 业务服务层
│   └── utils/            # 工具函数
├── agents/                # 智能代理目录
│   ├── base/             # 基础代理类
│   └── specialized/      # 专门化代理
├── config/                # 配置文件目录
├── tests/                 # 测试目录
├── docs/                  # 文档目录
└── scripts/              # 脚本工具
```

## 安装

1. 克隆仓库：
```bash
git clone <repository-url>
cd multiagent
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
- 复制 `.env.example` 到 `.env`
- 根据需要修改配置

## 运行

启动服务器：
```bash
python startup.py
```

## 开发

### 添加新代理

1. 在 `agents/specialized` 目录下创建新的代理类
2. 继承 `BaseAgent` 类
3. 实现 `process` 方法

### 运行测试

```bash
python -m pytest tests/
```

## 许可证

MIT License
