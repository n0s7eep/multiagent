from flask import Flask, jsonify
from agent_manager import AgentManager

app = Flask(__name__)
agent_manager = AgentManager()

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/agents')
def get_agents():
    return jsonify(agent_manager.get_all_agents())

@app.route('/api/agents/<agent_type>/greet')
def greet_agent(agent_type):
    return jsonify({"message": agent_manager.greet(agent_type)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
