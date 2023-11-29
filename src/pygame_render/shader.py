from moderngl import Buffer, Program, Texture
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
        # Set program
        self._program: Program = program

        # UBO
        self._fresh_ubo_binding: int = 1
        self._ubo_dict: dict[str, Buffer] = {}

        # sampler2D locations
        self._fresh_location: int = 1
        self._sampler2D_locations: dict[str, tuple[Texture, int]] = {}

    @property
    def program(self) -> Program:
        """Get the ModernGL shader program."""
        return self._program

    def __getitem__(self, key):
        """
        Get the value associated with a uniform variable, UBO, or sampler2D.

        Parameters:
        - key: The name of the uniform variable, UBO, or sampler2D.

        Returns:
        - Union[Buffer, Texture, any]: The value associated with the specified key.
        """
        if key in self._ubo_dict:  # UBO
            return self._ubo_dict[key]
        elif key in self._sampler2D_locations:  # sampler2D
            texture, _ = self._sampler2D_locations[key]
            return texture
        else:  # uniform variable
            return self._program[key]

    def __setitem__(self, key, value):
        """
        Set the value of a uniform variable, UBO, or sampler2D.

        Parameters:
        - key: The name of the uniform variable, UBO, or sampler2D.
        - value: The value to be assigned.

        Raises:
        - AssertionError: If the key represents a UBO and the value is not of type 'bytes'.
        """
        if key in self._ubo_dict:  # UBO
            assert isinstance(
                value, bytes), 'Make sure to convert your data into bytes before writing it to the uniform buffer.'
            self._ubo_dict[key].write(value)
        elif isinstance(value, Texture):  # sampler2D
            self._program[key].value = self._fresh_location
            self._sampler2D_locations[key] = (value, self._fresh_location)
            self._fresh_location += 1
        else:  # uniform variable
            self._program[key] = value

    def sample_ubo_binding(self) -> int:
        """
        Get the next available UBO binding point.

        Note: This function is used in RenderEngine.reserve_uniform_block.
        """
        binding = self._fresh_ubo_binding
        self._fresh_ubo_binding += 1
        return binding

    def add_ubo(self, ubo: Buffer, name: str):
        """
        Add a UBO with a specified name to the Shader.

        Note: This method is used in RenderEngine.reserve_uniform_block.
        """
        self._ubo_dict[name] = ubo

    def bind_sampler2D_uniforms(self):
        """
        Bind the sampler2d uniforms to their assigned locations.

        Note: This method is used in RenderEngine.render.
        """
        for tex, location in self._sampler2D_locations.values():
            tex.use(location)

    def clear_sampler2D_uniforms(self):
        """
        Clear the sampler2D uniform dictionary.

        Note: This method is used in RenderEngine.render.
        """
        self._sampler2D_locations.clear()
        self._fresh_location = 1

    def release(self):
        """
        Release the ModernGL objects associated with the shader.
        """
        for ubo in self._ubo_dict.values():
            ubo.release()
        self._program.release()
