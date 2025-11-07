"""
Database models for Dog Walker Tracker
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Walker(Base):
    """Represents a unique dog walker"""
    __tablename__ = 'walkers'
    
    id = Column(Integer, primary_key=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_walks = Column(Integer, default=0)
    
    # Relationships
    detections = relationship('Detection', back_populates='walker', cascade='all, delete-orphan')
    images = relationship('WalkerImage', back_populates='walker', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Walker(id={self.id}, walks={self.total_walks})>"


class Detection(Base):
    """Represents a single detection event of a walker"""
    __tablename__ = 'detections'
    
    id = Column(Integer, primary_key=True)
    walker_id = Column(Integer, ForeignKey('walkers.id'))
    camera = Column(String)
    zone = Column(String)
    path_name = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)  # 'enter' or 'leave'
    has_dog = Column(Boolean, default=False)
    person_confidence = Column(Float)
    dog_confidence = Column(Float, nullable=True)
    
    # Relationships
    walker = relationship('Walker', back_populates='detections')
    
    def __repr__(self):
        return f"<Detection(walker={self.walker_id}, camera={self.camera}, time={self.timestamp})>"


class WalkerImage(Base):
    """Stores captured images of walkers and their dogs"""
    __tablename__ = 'walker_images'
    
    id = Column(Integer, primary_key=True)
    walker_id = Column(Integer, ForeignKey('walkers.id'))
    image_path = Column(String)
    image_type = Column(String)  # 'person', 'dog', or 'combined'
    timestamp = Column(DateTime, default=datetime.utcnow)
    camera = Column(String)
    quality_score = Column(Float)  # Image quality rating
    
    # Relationships
    walker = relationship('Walker', back_populates='images')
    
    def __repr__(self):
        return f"<WalkerImage(walker={self.walker_id}, type={self.image_type})>"


class WalkSession(Base):
    """Represents a complete walk session across multiple cameras"""
    __tablename__ = 'walk_sessions'
    
    id = Column(Integer, primary_key=True)
    walker_id = Column(Integer, ForeignKey('walkers.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    cameras_visited = Column(String)  # Comma-separated list
    paths_taken = Column(String)  # Comma-separated list
    has_dog = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<WalkSession(walker={self.walker_id}, start={self.start_time})>"


def init_database(db_path='dog_walker_tracker.db'):
    """Initialize the database"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
