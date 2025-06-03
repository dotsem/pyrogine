import glfw
import numpy as np
import moderngl
from PIL import Image

class Window:
    def __init__(self, width=800, height=600, title="Pyrogine Window"):
        if not glfw.init():
            raise Exception("GLFW initialization failed!")
        self.width, self.height = width, height
        self.window = glfw.create_window(width, height, title, None, None)
        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context()
        
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_pos;
                in vec2 in_texcoord;
                in vec2 in_offset;
                out vec2 v_texcoord;
                void main() {
                    vec2 new_pos = in_pos + in_offset; 
                    gl_Position = vec4(new_pos, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex;
                in vec2 v_texcoord;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(tex, v_texcoord);
                }
            """
        )

    def should_close(self):
        return glfw.window_should_close(self.window)

    def poll_events(self):
        glfw.poll_events()

    def swap_buffers(self):
        glfw.swap_buffers(self.window)

    def terminate(self):
        glfw.terminate()

class TextureAtlas:
    def __init__(self, ctx, texture_files):
        self.textures = []
        for file in texture_files:
            image = Image.open(file).convert("RGBA")
            image_data = np.array(image, dtype=np.uint8)
            texture = ctx.texture(image.size, 4, image_data.tobytes())
            texture.use()
            self.textures.append(texture)

    def get_texture(self, index):
        return self.textures[index]

class Sprite:
    def __init__(self, x, y, width, height, texture_id):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.x_end = x + width  # Calculate bottom-right corner
        self.y_end = y + height  # Calculate bottom-right corner
        self.texture_id = texture_id
        self.visible = True

class Renderer:
    def __init__(self, ctx, window):
        self.ctx = ctx
        self.window = window

        # Correct UV mapping, ensuring no flipping occurs
        self.vbo = ctx.buffer(np.array([
            0.0, 1.0, 0.0, 1.0, 0.0, 0.0,  # Top-left
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0,  # Top-right
            1.0, 0.0, 1.0, 0.0, 0.0, 0.0,  # Bottom-right
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # Bottom-left
        ], dtype='f4'))

    def render(self, atlas, sprites):
        self.ctx.clear(0.1, 0.1, 0.1)
        for sprite in sprites:
            if sprite.visible:
                atlas.get_texture(sprite.texture_id).use()
                
                vbo_data = np.array([
                    sprite.x, sprite.y, 0.0, 1.0,  # Top-left
                    sprite.x_end, sprite.y, 1.0, 1.0,  # Top-right
                    sprite.x_end, sprite.y_end, 1.0, 0.0,  # Bottom-right
                    sprite.x, sprite.y_end, 0.0, 0.0,  # Bottom-left
                ], dtype='f4')

                self.vbo.write(vbo_data.tobytes())
                vao = self.ctx.vertex_array(
                    self.window.prog, [(self.vbo, "2f 2f", "in_pos", "in_texcoord")]
                )
                vao.render(moderngl.TRIANGLE_FAN)

def main():
    window = Window()
    atlas = TextureAtlas(window.ctx, ["assets/enemy.jpg", "assets/player.jpg"])  
    renderer = Renderer(window.ctx, window)

    sprites = [
        Sprite(100, 100, 128, 128, texture_id=0),  
        Sprite(400, 200, 128, 128, texture_id=1)  
    ]

    while not window.should_close():
        window.poll_events()
        renderer.render(atlas, sprites)
        window.swap_buffers()

    window.terminate()

if __name__ == "__main__":
    main()
