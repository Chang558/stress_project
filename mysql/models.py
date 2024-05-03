from sqlalchemy import Column, TEXT, INT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class year_barGraph(Base):
    __tablename__ = 'year_barGraph'
    
    id	=  Column(INT, nullable=False, primary_key=True)
    image_url =  Column(TEXT, nullable=False)
    name = Column(TEXT, nullable=False)

class region_versus(Base):
    __tablename__ = 'region_versus'
    
    id	=  Column(INT, nullable=False, primary_key=True)
    image_url =  Column(TEXT, nullable=False)
    name = Column(TEXT, nullable=False)    
    
class social_graph(Base):
    __tablename__ = 'social_graph'
    
    id	=  Column(INT, nullable=False, primary_key=True)
    image_url =  Column(TEXT, nullable=False)
    name = Column(TEXT, nullable=False)    