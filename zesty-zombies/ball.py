"""Ball class for server module."""

import random


class Ball:
    def __init__(self, screen_size: tuple[int, int], server):
        self.screen_size = screen_size
        self.server = server
        self.texture = 0
        self.size = (10, 10)
        self.paddle_size = (10, 100)
        self.position_start: tuple[int, int] = self.randomize_start_position()
        self.position: tuple[int, int] = self.position_start
        self.speed_angle: tuple[int, int] = self.randomize_start_angle()
        self.angle: tuple[int, int] = self.speed_angle
        self.speed = 10
        self.bounced = False
        self.last_collided_side = 0
        self.paddle_bounce_counter = 0
        self.invulnerability = 15
        self.total_bounces = 0

    def update_position(self):
        """Handle game calculations."""
        collided_side = None
        ball_x = self.position[0]
        ball_y = self.position[1]

        # Check if ball collides with a wall
        if ball_x <= 0 and self.invulnerability <= 0:
            if self.server.active_clients.get(0) is not None:
                self.server.add_score(0)
                self.reset()
            else:
                collided_side = 0

        if ball_x >= self.screen_size[0] and self.invulnerability <= 0:
            if self.server.active_clients.get(1) is not None:
                self.server.add_score(1)
                self.reset()
            else:
                collided_side = 1

        if ball_y <= 0 and self.invulnerability <= 0:
            if self.server.active_clients.get(2) is not None:
                self.server.add_score(2)
                self.reset()
            else:
                collided_side = 2

        if ball_y >= self.screen_size[1] and self.invulnerability <= 0:
            if self.server.active_clients.get(3) is not None:
                self.server.add_score(3)
                self.reset()
            else:
                collided_side = 3

        # Check if ball collides with a paddle
        if collided_side is None:
            for client in self.server.active_clients.values():
                if self.check_collision(client.paddle_position, self.paddle_size, client.player_number):
                    collided_side = client.player_number
                    self.server.last_client_bounced = client
                    self.paddle_bounce_counter += 1
                    break
            for brick in self.server.bricks.brick_list:
                if (
                    self.check_collision(brick.position, brick.size)
                    and self.server.last_client_bounced is not None
                ):
                    collided_side = self.last_collided_side
                    self.server.bricks.delete_brick(brick, self.server.last_client_bounced)
                    self.server.add_score(collided_side)

        # Ball collision logic
        if collided_side is not None:
            self.bounced = True
            self.last_collided_side = collided_side

            # Calculate new ball angle
            if collided_side == 0:
                self.angle = (-self.angle[0], self.angle[1])
            if collided_side == 1:
                self.angle = (-self.angle[0], self.angle[1])
            if collided_side == 2:
                self.angle = (self.angle[0], -self.angle[1])
            if collided_side == 3:
                self.angle = (self.angle[0], -self.angle[1])
            self.invulnerability = 5
            self.total_bounces += 1

            if random.randint(5, 15) < self.total_bounces < 10000:
                self.server.bricks.generate_based_on_pattern()
                self.total_bounces = 10000
        else:
            self.bounced = False

        # Update the ball position
        self.position = (self.position[0] + self.angle[0], self.position[1] + self.angle[1])
        self.invulnerability -= 1
        if (
            (self.position[0] <= 0 and self.position[1] <= 0)
            or (self.position[0] <= 0 and self.position[1] >= self.screen_size[1])
            or (self.position[0] >= self.screen_size[0] and self.position[1] <= 0)
            or (self.position[0] >= self.screen_size[0] and self.position[1] >= self.screen_size[1])
        ):
            self.server.add_score(self.last_collided_side, 10)
            self.reset()
            self.texture = 1

    def randomize_start_position(self) -> tuple[int, int]:
        """Pick a starting location in a rectangle whos border is 25% the width of the arena."""
        return (
            random.randint(int(self.screen_size[0] * 0.25), int(self.screen_size[0] * 0.75)),
            random.randint(int(self.screen_size[1] * 0.25), int(self.screen_size[1] * 0.75)),
        )

    def randomize_start_angle(self) -> tuple[int, int]:
        x = random.choice([-3, -4, -5, -6, -7, 3, 4, 5, 6, 7])
        yy = 10 - abs(x)
        y = random.choice([yy, -yy])
        return x, y

    def reset(self):
        """Reset the ball position."""
        self.position = self.randomize_start_position()
        self.angle = self.randomize_start_angle()
        self.total_bounces = 0
        self.server.bricks.empty_bricks()
        self.server.last_client_bounced = None
        self.texture = 0

    def check_collision(self, object_pos, object_size, player_number=0) -> bool:
        """Check if the ball is colliding with a paddle or brick."""
        bx1 = self.position[0] + self.size[0] // 2
        by1 = self.position[1] + self.size[1] // 2
        bx2 = self.position[0] - self.size[0] // 2
        by2 = self.position[1] - self.size[1] // 2
        if player_number >= 2:
            px1 = object_pos[0] + object_size[1] // 2
            py1 = object_pos[1] + object_size[0] // 2
            px2 = object_pos[0] - object_size[1] // 2
            py2 = object_pos[1] - object_size[0] // 2
        else:
            px1 = object_pos[0] + object_size[0] // 2
            py1 = object_pos[1] + object_size[1] // 2
            px2 = object_pos[0] - object_size[0] // 2
            py2 = object_pos[1] - object_size[1] // 2
        return not (bx1 < px2 or bx2 > px1 or by2 > py1 or by1 < py2)
