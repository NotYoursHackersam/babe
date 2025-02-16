from typing import Dict, Optional

class AFKStatus:
    """
    Represents an AFK status for a user
    """
    def __init__(self, user_id: int, message: Optional[str] = None):
        self.user_id = user_id
        self.message = message or "Away"

class AFKTracker:
    """
    In-memory tracker for managing AFK statuses
    """
    def __init__(self):
        self._afk_users: Dict[int, AFKStatus] = {}

    def set_afk(self, user_id: int, message: Optional[str] = None):
        """Set a user's AFK status"""
        self._afk_users[user_id] = AFKStatus(user_id, message)

    def remove_afk(self, user_id: int):
        """Remove a user's AFK status"""
        if user_id in self._afk_users:
            del self._afk_users[user_id]

    def get_afk_status(self, user_id: int) -> Optional[AFKStatus]:
        """Get a user's AFK status"""
        return self._afk_users.get(user_id)

    def is_afk(self, user_id: int) -> bool:
        """Check if a user is AFK"""
        return user_id in self._afk_users
