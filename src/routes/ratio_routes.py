"""
Ratio routes for Flask API.

Provides endpoints for Ratio domain:
- POST /api/ratio - Create a new ratio document
- GET /api/ratio - Get all ratio documents (with optional ?name= query parameter)
- GET /api/ratio/<id> - Get a specific ratio document by ID
- PATCH /api/ratio/<id> - Update a ratio document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.ratio_service import RatioService

import logging
logger = logging.getLogger(__name__)


def create_ratio_routes():
    """
    Create a Flask Blueprint exposing ratio endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with ratio routes
    """
    ratio_routes = Blueprint('ratio_routes', __name__)
    
    @ratio_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_ratio():
        """
        POST /api/ratio - Create a new ratio document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created ratio document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        ratio_id = RatioService.create_ratio(data, token, breadcrumb)
        ratio = RatioService.get_ratio(ratio_id, token, breadcrumb)
        
        logger.info(f"create_ratio Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratio), 201
    
    @ratio_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_ratios():
        """
        GET /api/ratio - Retrieve infinite scroll batch of sorted, filtered ratio documents.
        
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
        result = RatioService.get_ratios(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_ratios Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @ratio_routes.route('/<ratio_id>', methods=['GET'])
    @handle_route_exceptions
    def get_ratio(ratio_id):
        """
        GET /api/ratio/<id> - Retrieve a specific ratio document by ID.
        
        Args:
            ratio_id: The ratio ID to retrieve
            
        Returns:
            JSON response with the ratio document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        ratio = RatioService.get_ratio(ratio_id, token, breadcrumb)
        logger.info(f"get_ratio Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratio), 200
    
    @ratio_routes.route('/<ratio_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_ratio(ratio_id):
        """
        PATCH /api/ratio/<id> - Update a ratio document.
        
        Args:
            ratio_id: The ratio ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated ratio document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        ratio = RatioService.update_ratio(ratio_id, data, token, breadcrumb)
        
        logger.info(f"update_ratio Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(ratio), 200
    
    logger.info("Ratio Flask Routes Registered")
    return ratio_routes