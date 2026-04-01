"""
Ratio service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Ratio domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Ratio domain
ALLOWED_SORT_FIELDS = ['name', 'description', 'status', 'created.at_time', 'saved.at_time']


class RatioService:
    """
    Service class for Ratio domain operations.
    
    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Ratio domain
    """
    
    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.
        
        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read', 'create', 'update')
        
        Raises:
            HTTPForbidden: If user doesn't have required permission
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        
        Example RBAC implementation:
            if operation == 'update':
                # Update requires admin role
                if 'admin' not in token.get('roles', []):
                    raise HTTPForbidden("Admin role required to update ratio documents")
            elif operation == 'create':
                # Create requires staff or admin role
                if not any(role in token.get('roles', []) for role in ['staff', 'admin']):
                    raise HTTPForbidden("Staff or admin role required to create ratio documents")
            elif operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                pass
        """
        pass
    
    @staticmethod
    def _validate_update_data(data):
        """
        Validate update data to prevent security issues.
        
        Args:
            data: Dictionary of fields to update
            
        Raises:
            HTTPForbidden: If update data contains restricted fields
        """
        # Prevent updates to _id and system-managed fields
        restricted_fields = ['_id', 'created', 'saved']
        for field in restricted_fields:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")
    
    @staticmethod
    def create_ratio(data, token, breadcrumb):
        """
        Create a new ratio document.
        
        Args:
            data: Dictionary containing ratio data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging (contains at_time, by_user, from_ip, correlation_id)
            
        Returns:
            str: The ID of the created ratio document
        """
        try:
            RatioService._check_permission(token, 'create')
            
            # Remove _id if present (MongoDB will generate it)
            if '_id' in data:
                del data['_id']
            
            # Automatically populate required fields: created and saved
            # These are system-managed and should not be provided by the client
            # Use breadcrumb directly as it already has the correct structure
            data['created'] = breadcrumb
            data['saved'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            ratio_id = mongo.create_document(config.RATIO_COLLECTION_NAME, data)
            logger.info(f"Created ratio { ratio_id} for user {token.get('user_id')}")
            return ratio_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating ratio: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create ratio: {error_msg}")
    
    @staticmethod
    def get_ratios(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered ratio documents.
        
        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            name: Optional name filter (simple search)
            after_id: Cursor (ID of last item from previous batch, None for first request)
            limit: Items per batch
            sort_by: Field to sort by
            order: Sort order ('asc' or 'desc')
        
        Returns:
            dict: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None  # ID of last item, or None if no more
            }
        
        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            RatioService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.RATIO_COLLECTION_NAME)
            result = execute_infinite_scroll_query(
                collection,
                name=name,
                after_id=after_id,
                limit=limit,
                sort_by=sort_by,
                order=order,
                allowed_sort_fields=ALLOWED_SORT_FIELDS,
            )
            logger.info(
                f"Retrieved {len(result['items'])} ratios (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving ratios: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve ratios")
    
    @staticmethod
    def get_ratio(ratio_id, token, breadcrumb):
        """
        Retrieve a specific ratio document by ID.
        
        Args:
            ratio_id: The ratio ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The ratio document
            
        Raises:
            HTTPNotFound: If ratio is not found
        """
        try:
            RatioService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            ratio = mongo.get_document(config.RATIO_COLLECTION_NAME, ratio_id)
            if ratio is None:
                raise HTTPNotFound(f"Ratio { ratio_id} not found")
            
            logger.info(f"Retrieved ratio { ratio_id} for user {token.get('user_id')}")
            return ratio
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving ratio { ratio_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve ratio { ratio_id}")
    
    @staticmethod
    def update_ratio(ratio_id, data, token, breadcrumb):
        """
        Update a ratio document.
        
        Args:
            ratio_id: The ratio ID to update
            data: Dictionary containing fields to update
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The updated ratio document
            
        Raises:
            HTTPNotFound: If ratio is not found
        """
        try:
            RatioService._check_permission(token, 'update')
            RatioService._validate_update_data(data)
            
            # Build update data with $set operator (excluding restricted fields)
            restricted_fields = ['_id', 'created', 'saved']
            set_data = {k: v for k, v in data.items() if k not in restricted_fields}
            
            # Automatically update the 'saved' field with current breadcrumb (system-managed)
            # Use breadcrumb directly as it already has the correct structure
            set_data['saved'] = breadcrumb
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.RATIO_COLLECTION_NAME,
                document_id=ratio_id,
                set_data=set_data
            )
            
            if updated is None:
                raise HTTPNotFound(f"Ratio { ratio_id} not found")
            
            logger.info(f"Updated ratio { ratio_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating ratio { ratio_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to update ratio { ratio_id}")