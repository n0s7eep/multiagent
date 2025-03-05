from flask import jsonify
from app.api import bp

@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '服务正常运行'
    })
