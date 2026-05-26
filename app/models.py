from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, Column, Integer, String, Numeric, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    role_name = Column(String(100), nullable=False, unique=True)
    
    users = relationship('User', back_populates='role')
    user_roles = relationship('UserRole', back_populates='role')


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    national_id = Column(String(50), nullable=False, unique=True)
    phone = Column(String(20))
    name = Column(String(255), nullable=False)
    member_number = Column(String(50), unique=True)
    password = Column(String(255), nullable=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    role_id = Column(Integer, ForeignKey('roles.id'))
    created_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    
    role = relationship('Role', back_populates='users')
    wallet = relationship('Wallet', back_populates='user', uselist=False)
    transactions = relationship('Transaction', back_populates='user')
    user_roles = relationship('UserRole', back_populates='user')
    audit_logs = relationship('Audit', back_populates='user')


class UserRole(Base):
    __tablename__ = 'user_roles'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)
    
    user = relationship('User', back_populates='user_roles')
    role = relationship('Role', back_populates='user_roles')


class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    balance = Column(Numeric(12, 2), default=Decimal('0.00'))
    created_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    
    user = relationship('User', back_populates='wallet')
    transactions = relationship('Transaction', back_populates='wallet')


class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    wallet_id = Column(Integer, ForeignKey('wallets.id'), nullable=False)
    reference_id = Column(String(100))
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50))
    description = Column(Text)
    direction = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship('User', back_populates='transactions')
    wallet = relationship('Wallet', back_populates='transactions')


class Audit(Base):
    __tablename__ = 'audit'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.now)
    ip_address = Column(String(45))
    table_name = Column(String(100))
    action = Column(String(50))
    old_value = Column(Text)
    new_value = Column(Text)
    
    user = relationship('User', back_populates='audit_logs')
