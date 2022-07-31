import random


class Ball:
    def __init__(self, screen_size, server):
        self.texture = 0
        self.server = server
        self.ball_size = (10, 10)
        self.paddle_size = (10, 100)
        self.ball_position_start: tuple[int, int] = self.randomize_ball_start_position()
        self.ball_position: tuple[int, int] = self.ball_position_start
        self.ball_speed_angle: tuple[int, int] = self.randomize_ball_start_angle()
        self.ball_angle: tuple[int, int] = self.ball_speed_angle
        self.ball_speed: 10
        self.ball_bounced: bool = False
        self.ball_last_side_bounced_off_of = None
        self.paddle_bounce_counter = 0
        self.invulnerability = 15
        self.total_bounces = 0

    async def update_ball_position(self):
        """Handle game calculations."""
        collided_side = None
        ball_x = self.ball_position[0]
        ball_y = self.ball_position[1]

        # Check if ball collides with a wall
        if ball_x <= 0 and self.invulnerability <= 0:
            print('wall bounce 0', ball_x, ball_y, self.invulnerability)
            if self.server.active_clients.get(0) is not None:
                self.server.add_score()
                self.reset_ball()
            else:
                collided_side = 0
                self.ball_last_side_bounced_off_of = 0

        if ball_x >= self.server.screen_size[0] and self.invulnerability <= 0:
            print('wall bounce 1', ball_x, ball_y, self.invulnerability)
            if self.server.active_clients.get(1) is not None:
                self.server.add_score()
                self.reset_ball()
            else:
                collided_side = 1
                self.ball_last_side_bounced_off_of = 1

        if ball_y <= 0 and self.invulnerability <= 0:
            print('wall bounce 2', ball_x, ball_y, self.invulnerability)
            if self.server.active_clients.get(2) is not None:
                self.server.add_score()
                self.reset_ball()
            else:
                collided_side = 2
                self.ball_last_side_bounced_off_of = 2

        if ball_y >= self.server.screen_size[1] and self.invulnerability <= 0:
            print('wall bounce 3', ball_x, ball_y, self.invulnerability)
            if self.server.active_clients.get(3) is not None:
                self.server.add_score()
                self.reset_ball()
            else:
                collided_side = 3
                self.ball_last_side_bounced_off_of = 3

        # Check if ball collides with a paddle
        if collided_side is None:
            for client in self.server.active_clients.values():
                if self.check_ball_paddle_collision(client.paddle_position, self.paddle_size, client.player_number):
                    collided_side = client.player_number
                    self.server.last_client_bounced = client
                    self.paddle_bounce_counter += 1
                    break
            for brick in self.server.bricks.brick_list:
                if self.check_ball_paddle_collision(brick.position, brick.size) \
                        and self.server.last_client_bounced is not None:
                    print('hit a brick')
                    # self.server.add_score(brick.points)
                    collided_side = self.ball_last_side_bounced_off_of
                    self.server.bricks.delete_brick(brick, self.server.last_client_bounced)
                    self.server.add_score(brick.points)

        # Ball collision logic
        if collided_side is not None:
            self.ball_bounced = True

            # Calculate new ball speed
            if collided_side == 0:
                self.ball_angle = (-self.ball_angle[0], self.ball_angle[1])
            if collided_side == 1:
                self.ball_angle = (-self.ball_angle[0], self.ball_angle[1])
            if collided_side == 2:
                self.ball_angle = (self.ball_angle[0], -self.ball_angle[1])
            if collided_side == 3:
                self.ball_angle = (self.ball_angle[0], -self.ball_angle[1])
            self.invulnerability = 5
            self.total_bounces += 1

            if random.randint(5, 15) < self.total_bounces < 10000:
                self.server.bricks.generate_based_on_pattern()
                self.total_bounces = 10000

        else:
            self.ball_bounced = False

        # Update the ball position
        self.ball_position = (
            self.ball_position[0] + self.ball_angle[0],
            self.ball_position[1] + self.ball_angle[1]
        )
        self.invulnerability -= 1
        if (self.ball_position[0] < 1 or self.ball_position[1] < 1
                or self.ball_position[0] > 700 or self.ball_position[1] > 700):
            print(self.ball_position)
        if (self.ball_position[0] < -10 or self.ball_position[1] < -10
                or self.ball_position[0] > 750 or self.ball_position[1] > 750):
            self.debug(collided_side)
            self.reset_ball()
            self.texture = 1

    def debug(self, collided_side):
        print(self.ball_last_side_bounced_off_of)
        print(self.ball_position)
        print(collided_side)

    def collision_v2(self, collided_side: int, angle_adjustment: int):
        if collided_side == 0:
            self.ball_angle = (-self.ball_angle[0], self.ball_angle[1])
        if collided_side == 1:
            self.ball_angle = (-self.ball_angle[0], self.ball_angle[1])
        if collided_side == 2:
            self.ball_angle = (self.ball_angle[0], -self.ball_angle[1])
        if collided_side == 3:
            self.ball_angle = (self.ball_angle[0], -self.ball_angle[1])

    def randomize_ball_start_position(self):
        """picks a starting location in a rectangle whos border is 25% the width of the arena"""
        return (random.randint(self.server.screen_size[0] * 0.25, self.server.screen_size[0] * 0.75),
                random.randint(self.server.screen_size[1] * 0.25, self.server.screen_size[1] * 0.75))

    def randomize_ball_start_angle(self):
        """generates a random ball speed with angles between -7 - -3 and 3 - 7. The opposition value but be equal to
        either the negative or the positive of 10 minutes the absolute value of the first
        """
        x = random.choice([-3, -4, -5, -6, -7, 3, 4, 5, 6, 7])
        yy = 10 - abs(x)
        y = random.choice([yy, -yy])
        return [x, y]

    def reset_ball(self):
        """Reset the ball position."""
        self.ball_position = self.randomize_ball_start_position()
        self.ball_angle = self.randomize_ball_start_angle()
        self.total_bounces = 0
        self.server.bricks.empty_bricks()
        self.server.last_client_bounced = None
        self.texture = 0

    def check_ball_paddle_collision(self, object_pos, object_size, player_number=0):
        """Check if the ball is colliding with a paddle."""
        bx1 = self.ball_position[0] + self.ball_size[0] // 2
        by1 = self.ball_position[1] + self.ball_size[1] // 2
        bx2 = self.ball_position[0] - self.ball_size[0] // 2
        by2 = self.ball_position[1] - self.ball_size[1] // 2
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
        return not (
            bx1 < px2
            or bx2 > px1
            or by2 > py1
            or by1 < py2
        )
