from rest_framework import permissions

# Share levels in increasing order of privilege.
PERMISSION_RANK = {'VIEW': 1, 'COMMENT': 2, 'EDIT': 3, 'OWNER': 4}

# Minimum share level per DocumentViewSet action for non-safe requests.
# Actions not listed here (destroy, toggle_trash, duplicate, reindex, shares) stay owner-only.
ACTION_MIN_PERMISSION = {
    'chat': 'VIEW',
    'summarize': 'VIEW',
    'annotations': 'COMMENT',
    'update': 'EDIT',
    'partial_update': 'EDIT',
    'toggle_read': 'EDIT',
    'related': 'EDIT',
}


def get_document_permission(user, doc):
    """Return 'OWNER', 'EDIT', 'COMMENT', 'VIEW' or None for this user on this document."""
    if not user or not user.is_authenticated:
        return None
    if doc.owner_id == user.id:
        return 'OWNER'

    # Direct document shares take precedence over inherited collection shares
    share = doc.shares.filter(shared_with_user=user).first()
    if share:
        return share.permission
    if doc.primary_collection_id:
        col_share = doc.primary_collection.shares.filter(shared_with_user=user).first()
        if col_share:
            return col_share.permission
    return None


def has_document_permission(user, doc, required):
    level = get_document_permission(user, doc)
    return level is not None and PERMISSION_RANK[level] >= PERMISSION_RANK[required]


class IsOwnerOrCollaborator(permissions.BasePermission):
    """
    Object-level permission granting:
    - Safe methods (GET) if user is Owner OR has VIEW/COMMENT/EDIT share.
    - Grounded chat / summarize (POST) with VIEW or higher.
    - Annotation creation with COMMENT or higher.
    - Write methods (PUT, PATCH), toggle-read and related-document links with EDIT.
    - Delete, trash, duplicate, reindex and share management ONLY for the Owner.
    """

    def has_object_permission(self, request, view, obj):
        level = get_document_permission(request.user, obj)
        if level is None:
            return False
        if level == 'OWNER':
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        required = ACTION_MIN_PERMISSION.get(getattr(view, 'action', None) or '')
        if required is None:
            return False
        return PERMISSION_RANK[level] >= PERMISSION_RANK[required]


def can_file_into_collection(user, collection):
    """True if the user may put documents into this collection (owner, or an EDIT share)."""
    if not user or not user.is_authenticated or collection is None:
        return False
    if collection.owner_id == user.id:
        return True
    return collection.shares.filter(shared_with_user=user, permission='EDIT').exists()
