from rest_framework import permissions

class IsOwnerOrCollaborator(permissions.BasePermission):
    """
    Object-level permission granting:
    - Safe methods (GET) if user is Owner OR has VIEW/COMMENT/EDIT share.
    - Write methods (PUT, PATCH) if user is Owner OR has EDIT share.
    - Delete method (DELETE) ONLY if user is Owner.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Owner has full permissions
        if obj.owner == user:
            return True

        # Check direct document shares
        doc_shares = obj.shares.filter(shared_with_user=user)
        user_permission = doc_shares.first().permission if doc_shares.exists() else None

        # Check inherited collection shares
        if not user_permission and obj.primary_collection:
            col_shares = obj.primary_collection.shares.filter(shared_with_user=user)
            if col_shares.exists():
                user_permission = col_shares.first().permission

        if not user_permission:
            return False

        # Read requests: VIEW, COMMENT, or EDIT
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write requests (PUT, PATCH): requires EDIT
        if request.method in ('PUT', 'PATCH'):
            return user_permission == 'EDIT'

        # Delete requests: strictly Owner only
        return False
