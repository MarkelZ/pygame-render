# Standard modules
from importlib import resources
import enum


# Import tests for non-standard modules
try:
    import numpy as np
except ImportError:
    raise ImportError('Missing package: numpy.')
except Exception as e:
    raise ImportError(f'Error importing numpy: {e}')

try:
    import pygame
except ImportError:
    raise ImportError('Missing package: pygame.')
except Exception as e:
    raise ImportError(f'Error importing pygame: {e}')

try:
    import moderngl
except ImportError:
    raise ImportError('Missing package: moderngl.')
except Exception as e:
    raise ImportError(f'Error importing moderngl: {e}')


# Local modules
from .engine import RenderEngine
from .layer import Layer
from .shader import Shader
from .font_atlas import FontAtlas
from moderngl import Program, Buffer, Framebuffer, Texture

NEAREST = moderngl.NEAREST
LINEAR = moderngl.LINEAR

__all__ = ['RenderEngine', 'FontAtlas', 'Layer', 'Shader', 'Program', 'Buffer',
           'Framebuffer', 'Texture', 'NEAREST', 'LINEAR']

# Version of the pygame_render package
__version__ = '1.4.0'
