from flask import jsonify
from api import bp

bp = bp.route('/health')
@bp.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': '服务正常运行'
    })

def init_app(app):
    app.register_blueprint(bp)
