from . import patches
from . patches import marker_default_params


try:
    import PySide2
    pyside_installed = True
except ImportError:
    pyside_installed = False

if pyside_installed:
    from . interactive import interactive_subplots
