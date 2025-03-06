from flask import Flask, jsonify
from agent_manager import AgentManager
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='multiagent.log'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
agent_manager = AgentManager()

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/agents')
def get_agents():
    try:
        agents = agent_manager.get_all_agents()
        return jsonify(agents)
    except Exception as e:
        logger.error(f"获取agents列表失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/agents/<agent_type>')
def get_agent(agent_type):
    try:
        agent = agent_manager.get_agent(agent_type)
        if agent:
            return jsonify(agent)
        logger.warning(f"未找到agent: {agent_type}")
        return jsonify({"error": "Agent not found"}), 404
    except Exception as e:
        logger.error(f"获取agent失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/agents/<agent_type>/greet')
def greet_agent(agent_type):
    try:
        greeting = agent_manager.greet(agent_type)
        return jsonify({"greeting": greeting})
    except Exception as e:
        logger.error(f"获取问候语失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
