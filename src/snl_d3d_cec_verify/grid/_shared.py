
import numpy as np


def generate_grid_nodes(self, x0,
                              y0,
                              xsize,
                              ysize,
                              dx,
                              dy):
    """
    Generate nodes for a rectangular grid based on the origin (x0, y0) and 
    size (xsize, ysize) with the cell sizes (dx, dy). Last row and column
    will have size adjusted if dx and dy do not divide perfectly.
    """
    
    # Generate x and y spacing
    ncols = int(xsize / dx)
    nrows = int(ysize / dy)
    
    x1 = x0 + xsize
    y1 = y0 + ysize
    
    x = np.linspace(x0, x0 + dx * (ncols), ncols + 1)
    y = np.linspace(y0, y0 + dy * (nrows), nrows + 1)
    
    # Adjust last row and column if overlap
    if not np.isclose(x[-1], x1):
        x = np.append(x, x1) 
    
    if not np.isclose(y[-1], y1):
        y = np.append(y, y1)
    
    return (x, y)
