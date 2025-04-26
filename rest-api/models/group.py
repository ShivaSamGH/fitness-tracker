"""
Group model for the Fitness Tracker application.

This file contains the Group model and related association tables.
"""

from datetime import datetime
from models.user import db, User
from constants import Database, UserRole

# Association table for group members
group_members = db.Table(
    Database.GROUP_MEMBERS_TABLE,
    db.Column('group_id', db.Integer, db.ForeignKey(f'{Database.GROUPS_TABLE}.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey(f'{Database.USERS_TABLE}.id'), primary_key=True)
)

class Group(db.Model):
    """
    Group model for storing group related details.

    Attributes:
        id (int): Primary key for the group
        name (str): Name of the group
        description (str): Description of the group
        invite_code (str): Code for inviting users to the group
        trainer_id (int): ID of the trainer who created the group
        created_at (datetime): Timestamp when the group was created
        members (relationship): Users who are members of the group
        trainer (relationship): The trainer who created the group
    """
    __tablename__ = Database.GROUPS_TABLE

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(Database.NAME_SIZE), nullable=False)
    description = db.Column(db.String(Database.DESCRIPTION_SIZE))
    invite_code = db.Column(db.String(Database.INVITE_CODE_SIZE), unique=True, nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey(f'{Database.USERS_TABLE}.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    members = db.relationship('User', secondary=group_members, lazy='subquery',
                             backref=db.backref('groups', lazy=True))
    trainer = db.relationship('User', foreign_keys=[trainer_id])

    def __init__(self, name, description, trainer_id, invite_code):
        """
        Initialize a new Group instance.

        Args:
            name (str): The name of the group
            description (str): The description of the group
            trainer_id (int): The ID of the trainer who created the group
            invite_code (str): The invite code for the group
        """
        self.name = name
        self.description = description
        self.trainer_id = trainer_id
        self.invite_code = invite_code

    def to_dict(self):
        """
        Convert the group object to a dictionary for serialization.

        Returns:
            dict: Dictionary representation of the group
        """
        return {
            Database.ID_KEY: self.id,
            Database.NAME_KEY: self.name,
            Database.DESCRIPTION_KEY: self.description,
            'trainer_id': self.trainer_id,
            Database.INVITE_CODE_KEY: self.invite_code,
            Database.CREATED_AT_KEY: self.created_at.isoformat() if self.created_at else None,
            'members_count': len(self.members)
        }

    def __repr__(self):
        """
        String representation of the Group object.

        Returns:
            str: String representation
        """
        return f'<Group {self.name}, Trainer ID: {self.trainer_id}>'
