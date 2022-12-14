from ..db import db

class User_manager(object):
    ##This is handled via a separate function in case we want to hardcode certain users to other id's (such as rawb having two discord accounts, or a user wanting a separate database entry for the same discord user for some reason)
    ##This is also a good place to ensure that the user even has an entry to begin with
    def get_user_id(self, user: int) -> int:
        userID = user.id

        if userID == 968649137635614793: userID = 90956966947467264

        db.execute("INSERT OR IGNORE INTO users (userID) VALUES (?)",
            userID)

        return userID
    
    def has_tag(self, userID: int, tag_name: str) -> bool:
        return self.has_tag_active(userID, tag_name) or self.has_tag_inactive(userID, tag_name)

    def has_tag_active(self, userID: int, tag_name: str) -> bool:
        if tag_name in self.get_tags_active(userID):
            return True
        else:
            return False
    
    def has_tag_inactive(self, userID: int, tag_name: str) -> bool:
        if tag_name in self.get_tags_inactive(userID):
            return True
        else:
            return False
    
    def is_user_privacy_mode(self, userID: int) -> bool:
        return db.field("SELECT privacy FROM users WHERE userID = ?", userID) == 1

    def get_tags_active_csv(self, userID: int) -> str:
        tags = db.field("SELECT promptTagsActive FROM users WHERE userID = ?",
            userID
        )
        return tags

    def get_tags_active(self, userID: int) -> list[str]:
        tags = self.get_tags_active_csv(userID)
        if tags == ",":
            return []
        else:
            return tags[1:-1].split(",")

    def get_tags_inactive(self, userID: int) -> list[str]:
        tags = db.field("SELECT promptTagsInactive FROM users WHERE userID = ?",
            userID
        )
        if tags == ",":
            return []
        else:
            return tags[1:-1].split(",")
    
    def get_tags_total(self, userID) -> int:
        return len(self.get_tags_active(userID)) + len(self.get_tags_inactive(userID))

    def add_tag_active(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsActive = promptTagsActive || ? WHERE UserID = ?",
            tag_name + ",",
            userID
        )
    
    def add_tag_inactive(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsInactive = promptTagsInactive || ? WHERE UserID = ?",
            tag_name + ",",
            userID
        )
    
    def set_tags(self, userID: int, activeTags: str, inactiveTags: str):
        db.execute("UPDATE users SET promptTagsActive = ?, promptTagsInactive = ? WHERE UserID = ?",
            activeTags,
            inactiveTags,
            userID
        )
    
    def set_tags_inactive(self, userID: int, tags: str):
        db.execute("UPDATE users SET promptTagsInactive = ? WHERE UserID = ?",
            tags + ",",
            userID
        )
    
    def remove_tag(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsActive = replace(promptTagsActive, ?, ',') WHERE promptTagsActive LIKE ? AND UserID = ?",
            "," + tag_name + ",",
            "%," + tag_name + ",%",
            userID
        )
        
        db.execute("UPDATE users SET promptTagsInactive = replace(promptTagsInactive, ?, ',') WHERE promptTagsInactive LIKE ? AND UserID = ?",
            "," + tag_name + ",",
            "%," + tag_name + ",%",
            userID
        )