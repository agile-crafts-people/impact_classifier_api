"""
Sentiment routes for Flask API.

Provides endpoints for Sentiment domain:
- POST /api/sentiment - Create a new sentiment document
- GET /api/sentiment - Get all sentiment documents (with optional ?name= query parameter)
- GET /api/sentiment/<id> - Get a specific sentiment document by ID
- PATCH /api/sentiment/<id> - Update a sentiment document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.sentiment_service import SentimentService

import logging
logger = logging.getLogger(__name__)


def create_sentiment_routes():
    """
    Create a Flask Blueprint exposing sentiment endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with sentiment routes
    """
    sentiment_routes = Blueprint('sentiment_routes', __name__)
    
    @sentiment_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_sentiment():
        """
        POST /api/sentiment - Create a new sentiment document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created sentiment document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        sentiment_id = SentimentService.create_sentiment(data, token, breadcrumb)
        sentiment = SentimentService.get_sentiment(sentiment_id, token, breadcrumb)
        
        logger.info(f"create_sentiment Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(sentiment), 201
    
    @sentiment_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_sentiments():
        """
        GET /api/sentiment - Retrieve infinite scroll batch of sorted, filtered sentiment documents.
        
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
        result = SentimentService.get_sentiments(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_sentiments Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @sentiment_routes.route('/<sentiment_id>', methods=['GET'])
    @handle_route_exceptions
    def get_sentiment(sentiment_id):
        """
        GET /api/sentiment/<id> - Retrieve a specific sentiment document by ID.
        
        Args:
            sentiment_id: The sentiment ID to retrieve
            
        Returns:
            JSON response with the sentiment document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        sentiment = SentimentService.get_sentiment(sentiment_id, token, breadcrumb)
        logger.info(f"get_sentiment Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(sentiment), 200
    
    @sentiment_routes.route('/<sentiment_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_sentiment(sentiment_id):
        """
        PATCH /api/sentiment/<id> - Update a sentiment document.
        
        Args:
            sentiment_id: The sentiment ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated sentiment document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        sentiment = SentimentService.update_sentiment(sentiment_id, data, token, breadcrumb)
        
        logger.info(f"update_sentiment Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(sentiment), 200
    
    logger.info("Sentiment Flask Routes Registered")
    return sentiment_routes