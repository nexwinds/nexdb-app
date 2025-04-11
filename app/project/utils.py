"""
NEXDB - Project utilities
"""

def can_access_project(project, user):
    """Check if a user can access a project."""
    if project.created_by == user.id:
        return True
    
    if user in project.members:
        return True
    
    return False


def can_edit_project(project, user):
    """Check if a user can edit a project."""
    if project.created_by == user.id:
        return True
    
    if user in project.members:
        access_level = project.get_member_access_level(user.id)
        return access_level in ['write', 'admin']
    
    return False


def can_delete_project(project, user):
    """Check if a user can delete a project."""
    if project.created_by == user.id:
        return True
    
    if user in project.members:
        access_level = project.get_member_access_level(user.id)
        return access_level == 'admin'
    
    return False


def can_manage_members(project, user):
    """Check if a user can manage project members."""
    if project.created_by == user.id:
        return True
    
    if user in project.members:
        access_level = project.get_member_access_level(user.id)
        return access_level == 'admin'
    
    return False


def can_manage_servers(project, user):
    """Check if a user can manage database servers in a project."""
    if project.created_by == user.id:
        return True
    
    if user in project.members:
        access_level = project.get_member_access_level(user.id)
        return access_level in ['write', 'admin']
    
    return False 