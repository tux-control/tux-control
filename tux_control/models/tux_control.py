import datetime
import uuid
import hashlib
from sqlalchemy.event import listens_for
from werkzeug.security import generate_password_hash, check_password_hash
from tux_control.extensions import db
from sqlalchemy.orm import relationship
from tux_control.tools.sqlalchemy.uuid import GUID
from tux_control.tools.IDictify import IDictify


class BaseTable(db.Model):
    __abstract__ = True
    id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)


user_role_association_table = db.Table(
    'user_role_association',
    BaseTable.metadata,
    db.Column('user_id', GUID(), db.ForeignKey('user.id'), index=True),
    db.Column('role_id', GUID(), db.ForeignKey('role.id'), index=True)
)

role_permission_association_table = db.Table(
    'role_permission_association',
    BaseTable.metadata,
    db.Column('role_id', GUID(), db.ForeignKey('role.id'), index=True),
    db.Column('permission_id', GUID(), db.ForeignKey('permission.id'), index=True)
)


class User(BaseTable, IDictify):
    __tablename__ = 'user'
    system_user = db.Column(db.String(255), index=True, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    email = db.Column(db.String(255), index=True, nullable=False, unique=True)
    email_hash = db.Column(db.String(35), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    full_name = db.Column(db.String(255), nullable=False)

    roles = relationship(
        "Role",
        order_by="Role.name.asc()",
        secondary=user_role_association_table,
        back_populates="users"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password, password)

    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __eq__(self, other):
        """
        Checks the equality of two `UserMixin` objects using `get_id`.
        """
        if isinstance(other, User):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        """
        Checks the inequality of two `UserMixin` objects using `get_id`.
        """
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    __hash__ = object.__hash__

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'system_user': self.system_user,
            'last_login': self.last_login,
            'email': self.email,
            'email_hash': self.email_hash,
            'roles': [role.to_dict() for role in self.roles]
        }


class Role(BaseTable, IDictify):
    __tablename__ = 'role'
    name = db.Column(db.String(255), nullable=False, index=True, unique=True)
    users = relationship(
        "User",
        secondary=user_role_association_table,
        back_populates="roles"
    )

    permissions = relationship(
        "Permission",
        secondary=role_permission_association_table,
        back_populates="roles"
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'permissions': [permission.to_dict() for permission in self.permissions],
        }


class Permission(BaseTable, IDictify):
    __tablename__ = 'permission'
    name = db.Column(db.String(255), nullable=False, index=True, unique=True)
    identifier = db.Column(db.String(255), nullable=False, index=True, unique=True)
    roles = relationship(
        "Role",
        secondary=role_permission_association_table,
        back_populates="permissions"
    )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'identifier': self.identifier,
        }


class Package(BaseTable):
    __tablename__ = 'package'
    name = db.Column(db.String(255))
    key = db.Column(db.String(255))
    endpoint = db.Column(db.String(255))
    config_path = db.Column(db.String(255))
    info = db.Column(db.PickleType)
    is_installed = db.Column(db.Boolean)
    is_control_services_restart = db.Column(db.Boolean)
    package_services = relationship("PackageService", order_by="PackageService.position", backref="package", lazy='dynamic')
    package_updates = relationship("PackageUpdate", order_by="PackageUpdate.created", backref="package", lazy='dynamic')


class PackageService(BaseTable):
    __tablename__ = 'package_service'
    package_id = db.Column(GUID(), db.ForeignKey('package.id'))
    name = db.Column(db.String(255))
    is_enabled = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean)
    is_failed = db.Column(db.Boolean)
    position = db.Column(db.Integer)


class Update(BaseTable):
    __tablename__ = 'update'
    identifier = db.Column(db.String(64))
    is_done = db.Column(db.Boolean)
    is_canceled = db.Column(db.Boolean)
    package_updates = relationship("PackageUpdate", order_by="PackageUpdate.created", backref="update", lazy='dynamic')


class PackageUpdate(BaseTable):
    __tablename__ = 'package_update'
    update_id = db.Column(GUID(), db.ForeignKey('update.id'))
    package_id = db.Column(GUID(), db.ForeignKey('package.id'), nullable=False)
    is_updated = db.Column(db.Boolean)
    version_from = db.Column(db.String(255))
    version_to = db.Column(db.String(255))


@listens_for(User, 'before_update')
@listens_for(User, 'before_insert')
def _preprocess_user(mapper, connect, target):
    target.full_name = '{} {}'.format(target.first_name, target.last_name)
    fixed = target.email.lower().strip()
    target.email_hash = hashlib.md5(fixed.encode()).hexdigest()

