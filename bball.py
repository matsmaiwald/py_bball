"""
Use Pymunk physics engine.

For more info on Pymunk see:
http://www.pymunk.org/en/latest/

To install pymunk:
pip install pymunk

Artwork from http://kenney.nl

If Python and Arcade are installed, this example can be run from the command line with:
python -m arcade.examples.pymunk_pegboard

Click and drag with the mouse to move the boxes.
"""

import arcade
import pymunk
import random
import math
import os
import pyglet
import time
from high_scores import update_high_scores, load_high_scores, save_high_scores

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Basketball Game"
BASE_THROW_POINT = SCREEN_WIDTH / 2, 60
SPRITE_SCALING_PLAYER = 0.5
GAME_LENGTH = 60


class MenuView(arcade.View):
    def on_show(self):
        arcade.set_background_color(arcade.color.WHITE)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text(
            """
            Basketball
            Shootout Challenge""",
            SCREEN_WIDTH / 2 - 200,
            SCREEN_HEIGHT / 2 + 100,
            arcade.color.BLACK,
            font_size=50,
            anchor_x="center",
        )
        arcade.draw_text(
            """
            How many points can you score in 60 seconds?
            Click to throw,
            move the mouse to adjust angle
            and strength of your shot.""",
            SCREEN_WIDTH / 2 - 70,
            SCREEN_HEIGHT / 2 - 75,
            arcade.color.GRAY,
            font_size=20,
            anchor_x="center",
        )

        arcade.draw_text(
            "Click to start!",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 175,
            arcade.color.GRAY,
            font_size=20,
            anchor_x="center",
        )

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    def __init__(self, score):
        super().__init__()
        self.time_taken = 0
        self.score = score
        try:
            self.high_scores = load_high_scores(path="high_scores.txt")
        except FileNotFoundError:
            empty_high_scores = []
            self.high_scores = empty_high_scores
        self.high_scores = update_high_scores(
            high_scores=self.high_scores, current_score=self.score
        )
        save_high_scores(self.high_scores)

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def draw_high_scores(self, high_scores: list, start_pos_x: int, start_pos_y: int):
        arcade.draw_text(
            "High Scores:", start_pos_x, start_pos_y, arcade.color.WHITE, 30
        )
        for count, item in enumerate(high_scores):
            arcade.draw_text(
                f"{count + 1}.)",
                start_pos_x,
                start_pos_y - 30 * (count + 1),
                arcade.color.WHITE,
                20,
            )
            arcade.draw_text(
                str(item[0]),
                start_pos_x + 120,
                start_pos_y - 30 * (count + 1),
                arcade.color.WHITE,
                20,
            )
            arcade.draw_text(
                str(item[1]),
                start_pos_x + 200,
                start_pos_y - 30 * (count + 1),
                arcade.color.WHITE,
                20,
            )

    def on_draw(self):
        arcade.start_render()
        """
        Draw "Game over" across the screen.
        """
        arcade.draw_text("Game Over", 240, 700, arcade.color.WHITE, 54)
        arcade.draw_text(
            "Score: {}".format(self.score), 240, 600, arcade.color.WHITE, 54
        )
        arcade.draw_text("Click to restart", 310, 50, arcade.color.YELLOW, 24)

        self.draw_high_scores(
            high_scores=self.high_scores, start_pos_x=240, start_pos_y=500
        )

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        self.window.show_view(game_view)


class ScoreArea(arcade.Sprite):
    def __init__(self, filename, x_pos, y_pos, sprite_scaling=1):
        super().__init__(filename, center_x=x_pos, center_y=y_pos, scale=sprite_scaling)
        self.alpha = 0


class CircleSprite(arcade.Sprite):
    def __init__(self, filename, pymunk_shape):
        super().__init__(
            filename,
            center_x=pymunk_shape.body.position.x,
            center_y=pymunk_shape.body.position.y,
        )
        self.width = pymunk_shape.radius * 2
        self.height = pymunk_shape.radius * 2
        self.pymunk_shape = pymunk_shape


class PymunkSprite(arcade.Sprite):
    """
    We need a Sprite and a Pymunk physics object. This class blends them
    together.
    """

    def __init__(
        self,
        filename,
        center_x=0,
        center_y=0,
        scale=1,
        body_type=pymunk.Body.DYNAMIC,
        sprite_width=None,
        sprite_height=None,
        elasticity=0.6,
        friction=10,
    ):

        super().__init__(filename, scale=scale, center_x=center_x, center_y=center_y)

        if sprite_height:
            width = sprite_width
            self.width = sprite_width
        if sprite_height:
            height = sprite_height
            self.height = sprite_height
        if sprite_height is None and sprite_width is None:
            width = self.texture.width * scale
            height = self.texture.height * scale

        self.body = pymunk.Body(body_type=body_type)
        self.body.position = pymunk.Vec2d(center_x, center_y)

        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        self.shape.mass = 0.1


class HoopPart(arcade.Sprite):
    def __init__(self, filename, pymunk_shape):
        super().__init__(
            filename,
            center_x=pymunk_shape.body.position.x,
            center_y=pymunk_shape.body.position.y,
        )
        self.pymunk_shape = pymunk_shape


def add_net_part(
    space, sprite_list, x, y, height=None, width=None, orientation="vertical"
):
    sprite = PymunkSprite(
        "assets/hoop_element_{}.png".format(orientation),
        x,
        y,
        scale=1,
        body_type=pymunk.Body.STATIC,
        sprite_width=width,
        sprite_height=height,
        elasticity=0.2,
    )

    sprite_list.append(sprite)
    space.add(sprite.body, sprite.shape)


def add_hoop_part_vertical(space, sprite_list, x, y, height=None, width=None):
    sprite = PymunkSprite(
        "assets/hoop_element_vertical.png",
        x,
        y,
        scale=1,
        body_type=pymunk.Body.STATIC,
        sprite_width=width,
        sprite_height=height,
    )
    collision_offset = 10
    x1, y1 = -sprite.width / 2 - collision_offset, -sprite.height / 2 - collision_offset
    x2, y2 = +sprite.width / 2 + collision_offset, -sprite.height / 2 - collision_offset
    x3, y3 = +sprite.width / 2 + collision_offset, +sprite.height / 2 + collision_offset
    x4, y4 = -sprite.width / 2 - collision_offset, +sprite.height / 2 + collision_offset

    sprite.set_points(((x1, y1), (x2, y2), (x3, y3), (x4, y4)))
    sprite_list.append(sprite)
    space.add(sprite.body, sprite.shape)


def add_rim_part_horizontal(space, sprite_list, x, y, height=None, width=None):
    sprite = PymunkSprite(
        "assets/basketball_rim_small.png",
        x,
        y,
        scale=1,
        body_type=pymunk.Body.STATIC,
        sprite_width=width,
        sprite_height=height,
        elasticity=0.99,
    )
    collision_offset = 10
    x1, y1 = -sprite.width / 2 - collision_offset, -sprite.height / 2 - collision_offset
    x2, y2 = +sprite.width / 2 + collision_offset, -sprite.height / 2 - collision_offset
    x3, y3 = +sprite.width / 2 + collision_offset, +sprite.height / 2 + collision_offset
    x4, y4 = -sprite.width / 2 - collision_offset, +sprite.height / 2 + collision_offset

    sprite.set_points(((x1, y1), (x2, y2), (x3, y3), (x4, y4)))
    sprite_list.append(sprite)
    space.add(sprite.body, sprite.shape)


class GameView(arcade.View):
    """ Main application class. """

    def __init__(self):
        super().__init__()

        # Set the working directory (where we expect to find files) to the same
        # directory this .py file is in. You can leave this out of your own
        # code, but it is needed to easily run the examples using "python -m"
        # as mentioned at the top of this program.
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        self.peg_list = arcade.SpriteList()
        self.ball_list: arcade.SpriteList[CircleSprite] = arcade.SpriteList()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.time = 0

        # -- Pymunk
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)

        self.static_lines = []

        self.ticks_to_next_ball = 10

        # Draw ground
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape = pymunk.Segment(body, [0, 10], [SCREEN_WIDTH, 10], 0.0)
        shape.elasticity = 0.8
        shape.friction = 10
        self.space.add(shape)
        self.static_lines.append(shape)

        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        shape = pymunk.Segment(body, [0, 10], [0, SCREEN_HEIGHT], 1.0)
        shape.friction = 10
        shape.elasticity = 0.6
        self.space.add(shape)
        self.static_lines.append(shape)
        self.total_time = 0

        # Game set up
        self.t0 = time.time()
        self.time_over = False

        self.mouse_position = 0, 0
        self.ball_texture = arcade.load_texture("assets/ball_basket4.png")
        self.score = 0
        self.throw_point = BASE_THROW_POINT
        # Initialise sounds
        self.score_sound = pyglet.media.load("assets/Swish.wav")
        self.back_board_sound = pyglet.media.load("assets/Back_Board.wav")
        self.buzzer_sound = pyglet.media.load("assets/whistle.wav")

        # Player sprite
        self.player_list = arcade.SpriteList()
        # Character image from kenney.nl
        self.player_sprite = arcade.Sprite(
            "assets/player_idle.png", SPRITE_SCALING_PLAYER
        )
        self.player_sprite.center_x = BASE_THROW_POINT[0]
        self.player_sprite.center_y = BASE_THROW_POINT[1]
        self.player_sprite.filter = pymunk.ShapeFilter(categories=0b1)
        self.player_list.append(self.player_sprite)

        # Hoop set up
        self.hoop_list: arcade.SpriteList[HoopPart] = arcade.SpriteList()

        self.create_hoop(x_base=0, y_base=SCREEN_HEIGHT / 2)

    def create_hoop(self, x_base: int, y_base: int):

        add_hoop_part_vertical(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 10,
            y=y_base + 70,
            height=200,
            width=20,
        )

        add_rim_part_horizontal(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 35,
            y=y_base + 5,
            height=10,
            width=35,
        )
        add_rim_part_horizontal(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 125,
            y=y_base + 5,
            height=10,
            width=10,
        )

        add_net_part(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 125,
            y=y_base - 33,
            orientation="vertical",
        )
        add_net_part(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 46,
            y=y_base - 33,
            orientation="vertical",
        )
        add_net_part(
            space=self.space,
            sprite_list=self.hoop_list,
            x=x_base + 85,
            y=y_base - 60,
            orientation="horizontal",
        )

        self.score_area = ScoreArea(
            filename="assets/ball_basket4.png",
            x_pos=x_base + 85,
            y_pos=y_base - 55,
            sprite_scaling=2.3,
        )

    def move_start_point(self):
        self.throw_point = random.randint(160, SCREEN_WIDTH), 60
        self.player_sprite.center_x = self.throw_point[0]
        self.player_sprite.center_y = self.throw_point[1]

    def draw_shooting_arc(self):
        x_base, y_base = self.player_sprite.center_x, self.player_sprite.center_y
        x_target = (self.mouse_position[0] - x_base) / 3 + x_base
        y_target = (self.mouse_position[1] - y_base) / 3 + y_base
        arcade.draw_line(x_target, y_target, x_base, y_base, arcade.color.ORANGE, 1)
        arcade.draw_circle_outline(
            center_x=x_target, center_y=y_target, radius=10, color=arcade.color.ORANGE
        )

    def draw_score(self):

        arcade.draw_text(
            f"Score: {self.score}",
            SCREEN_WIDTH - 200,
            SCREEN_HEIGHT - 40,
            arcade.color.WHITE,
            24,
        )

    def draw_time_left(self):
        if self.time_over:
            time_left = 0
        else:
            time_left = GAME_LENGTH - self.total_time
        output = f"Time left: {time_left:.0f}"
        arcade.draw_text(output, 20, SCREEN_HEIGHT - 60, arcade.color.WHITE, 24)

    def draw_static_lines(self):

        for line in self.static_lines:
            body = line.body

            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            arcade.draw_line(pv1.x, pv1.y, pv2.x, pv2.y, arcade.color.WHITE, 2)

    def draw_new_ball(self):
        scale = 2
        arcade.draw_scaled_texture_rectangle(
            self.player_sprite.center_x,
            self.player_sprite.center_y,
            self.ball_texture,
            scale,
            0,
        )

    def on_draw(self):
        """
        Render the screen.
        """

        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw dynamic sprites
        self.ball_list.draw()
        self.player_list.draw()

        # Draw static elements
        self.hoop_list.draw()
        self.draw_static_lines()

        # Draw score and time left
        self.draw_score()
        self.draw_time_left()

        # Shooting arc
        self.draw_shooting_arc()

        # Spawn new ball if old one has vanished

        if len(self.ball_list) == 0:
            self.draw_new_ball()

    def on_mouse_motion(self, x, y, dx, dy):
        """
        Called whenever the mouse moves.
        """

        self.mouse_position = x, y

    def on_mouse_press(self, x, y, button, modifiers):
        if (
            button == arcade.MOUSE_BUTTON_LEFT
            and len(self.ball_list) < 1
            and not self.time_over
        ):
            self.last_mouse_position = x, y
            impulse_scaling = 8
            mass = 5
            radius = 20
            inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
            body = pymunk.Body(mass, inertia)
            x = self.throw_point[0]
            y = self.throw_point[1]
            body.position = x, y
            x_impulse = (self.last_mouse_position[0] - x) * impulse_scaling
            y_impulse = (self.last_mouse_position[1] - y) * impulse_scaling
            body.apply_impulse_at_local_point((x_impulse, y_impulse))
            shape = pymunk.Circle(body, radius, pymunk.Vec2d(0, 0))
            shape.friction = 0.3
            shape.elasticity = 0.99
            self.space.add(body, shape)

            sprite = CircleSprite("assets/ball_basket4.png", shape)
            self.ball_list.append(sprite)

    def on_update(self, delta_time):
        self.total_time = time.time() - self.t0

        # Check for scores
        balls_that_scored = arcade.check_for_collision_with_list(
            self.score_area, self.ball_list
        )
        for score_ball in balls_that_scored:
            print("SCORE")
            # Play sound
            self.score_sound.play()
            # Remove balls from physics space
            self.space.remove(score_ball.pymunk_shape, score_ball.pymunk_shape.body)
            self.score += 1
            # Remove balls from physics list
            score_ball.remove_from_sprite_lists()
            self.move_start_point()
        for ball in self.ball_list:
            # Check for colluisions

            balls_on_backboard = arcade.check_for_collision_with_list(
                ball, self.hoop_list
            )
            for back_board_ball in balls_on_backboard:
                print("YES")
                try:
                    self.back_board_sound.play()
                except Exception as e:
                    print(e)
            if ball.pymunk_shape.body.position.y <= 40:
                self.space.remove(ball.pymunk_shape, ball.pymunk_shape.body)
                ball.remove_from_sprite_lists()

        # Update physics
        # Use a constant time step, don't use delta_time
        # See "Game loop / moving time forward"
        # http://www.pymunk.org/en/latest/overview.html#game-loop-moving-time-forward
        self.space.step(1 / 60.0)

        # Move sprites to where physics objects are
        for ball in self.ball_list:
            ball.center_x = ball.pymunk_shape.body.position.x
            ball.center_y = ball.pymunk_shape.body.position.y
            ball.angle = math.degrees(ball.pymunk_shape.body.angle)
        if self.total_time >= GAME_LENGTH and not self.time_over:
            self.time_over = True
            try:
                self.buzzer_sound.play()
            except Exception as e:
                print(e)
        if self.time_over and len(self.ball_list) == 0:
            game_over_view = GameOverView(score=self.score)
            self.window.set_mouse_visible(True)
            self.window.show_view(game_over_view)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Basketball Shootout Challenge")
    window.total_score = 0
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
