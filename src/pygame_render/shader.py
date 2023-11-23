from moderngl import Buffer, Program
import numpy as np


class Shader:
    """
    A class for managing shader programs and related objects.

    Note: A Shader object cannot be instantiated directly. 
    Use RenderEngine.make_shader or RenderEngine.load_shader_from_path to create one.
    """

    def __init__(self, program: Program):
        """
        Initialize the Shader with a ModernGL shader program.

        Note: A Shader object cannot be instantiated directly. 
        Use RenderEngine.make_shader or RenderEngine.load_shader_from_path to create one.
        """
        self._program: Program = program
        self._fresh_ubo_binding: int = 1
        self._ubo_dict: dict[Buffer] = {}

    @property
    def program(self) -> Program:
        """Get the ModernGL shader program."""
        return self._program

    def __getitem__(self, key):
        """
        Get the value associated with a uniform variable or UBO.

        Parameters:
        - key: The name of the uniform variable or UBO.

        Returns:
        - Union[Buffer, any]: The value associated with the specified key.
        """
        if key in self._ubo_dict:
            return self._ubo_dict[key]
        else:
            return self._program[key]

    def __setitem__(self, key, value):
        """
        Set the value of a uniform variable or UBO.

        Parameters:
        - key: The name of the uniform variable or UBO.
        - value: The value to be assigned.

        Raises:
        - AssertionError: If the key represents a UBO and the value is not of type 'bytes'.
        """
        if key in self._ubo_dict:
            assert isinstance(
                value, bytes), 'Make sure to convert your data into bytes before writing it to the uniform buffer.'
            self._ubo_dict[key].write(value)
        else:
            self._program[key] = value

    def sample_ubo_binding(self) -> int:
        """
        Get the next available UBO binding point.
        """
        binding = self._fresh_ubo_binding
        self._fresh_ubo_binding += 1
        return binding

    def add_ubo(self, ubo: Buffer, name: str):
        """
        Add a UBO with a specified name to the Shader.
        """
        self._ubo_dict[name] = ubo
