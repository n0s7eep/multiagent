from flask import Blueprint, jsonify

def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '服务正常运行'
    })

def init_routes(bp):
    """注册健康检查路由"""
    bp.add_url_rule('/health', 'health_check', health_check, methods=['GET'])
