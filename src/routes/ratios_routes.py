"""
ratios routes for Flask API.

Provides endpoints for ratios domain:
- POST /api/ratios - Create a new ratios document
- GET /api/ratios - Get all ratios documents (with optional ?name= query parameter)
- GET /api/ratios/<id> - Get a specific ratios document by ID
- PATCH /api/ratios/<id> - Update a ratios document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.ratios_service import ratiosService

import logging
logger = logging.getLogger(__name__)


def create_ratios_routes():
    """
    Create a Flask Blueprint exposing ratios endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with ratios routes
    """
    ratios_routes = Blueprint('ratios_routes', __name__)
    
    @ratios_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_ratios():
        """
        POST /api/ratios - Create a new ratios document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created ratios document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        ratios_id = ratiosService.create_ratios(data, token, breadcrumb)
        ratios = ratiosService.get_ratios(ratios_id, token, breadcrumb)
        
        logger.info(f"create_ratios Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratios), 201
    
    @ratios_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_ratioss():
        """
        GET /api/ratios - Retrieve infinite scroll batch of sorted, filtered ratios documents.
        
        Query Parameters:
            name: Optional name filter
            after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
            limit: Items per batch (default: 10, max: 100)
            sort_by: Field to sort by (default: 'name')
            order: Sort order 'asc' or 'desc' (default: 'asc')
        
        Returns:
            JSON response with infinite scroll results: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None
            }
        
        Raises:
            400 Bad Request: If invalid parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get query parameters
        name = request.args.get('name')
        after_id = request.args.get('after_id')
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        # Service layer validates parameters and raises HTTPBadRequest if invalid
        # @handle_route_exceptions decorator will catch and format the exception
        result = ratiosService.get_ratioss(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_ratioss Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @ratios_routes.route('/<ratios_id>', methods=['GET'])
    @handle_route_exceptions
    def get_ratios(ratios_id):
        """
        GET /api/ratios/<id> - Retrieve a specific ratios document by ID.
        
        Args:
            ratios_id: The ratios ID to retrieve
            
        Returns:
            JSON response with the ratios document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        ratios = ratiosService.get_ratios(ratios_id, token, breadcrumb)
        logger.info(f"get_ratios Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratios), 200
    
    @ratios_routes.route('/<ratios_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_ratios(ratios_id):
        """
        PATCH /api/ratios/<id> - Update a ratios document.
        
        Args:
            ratios_id: The ratios ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated ratios document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        ratios = ratiosService.update_ratios(ratios_id, data, token, breadcrumb)
        
        logger.info(f"update_ratios Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratios), 200
    
    logger.info("ratios Flask Routes Registered")
    return ratios_routes