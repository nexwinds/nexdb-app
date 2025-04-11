"""
NEXDB - Error handlers
"""

from flask import render_template, jsonify, request

def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Bad request", message=str(error)), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Unauthorized", message="Authentication required"), 401
        return render_template('errors/401.html', error=error), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Forbidden", message="You don't have permission to access this resource"), 403
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Not found", message="Resource not found"), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Handle 429 Too Many Requests errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Too many requests", message="Rate limit exceeded"), 429
        return render_template('errors/429.html', error=error), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error errors."""
        if request.path.startswith('/api/'):
            return jsonify(error="Internal server error", message="An internal error occurred"), 500
        return render_template('errors/500.html', error=error), 500 