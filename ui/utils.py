import fitz
from collections import namedtuple
import sqlite3

book_attr = 'path format title author creator producer'
book_info = namedtuple('info', book_attr)

# 设置缩放比例 
class Size:
    def __init__(self, x, y):
        self._x = x
        self._y = y
        
    @property
    def x(self):
        return self._x
        
    @x.setter
    def x(self, x):
        if x > 1 and x < 5:
            self._x = x
            
    @property
    def y(self):
        return self._y
        
    @y.setter
    def y(self, y):
        if y > 1 and y < 5:
            self._y = y
      

        
# 设置属性点
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def update(self, x, y):
        self.x = x
        self.y = y
