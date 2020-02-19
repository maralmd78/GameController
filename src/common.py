from protoCompiled.SIM2REF import packet_pb2
from enum import Enum

class Robot():
    def __init__(self):
        self.id = 0
        self.x = 0.0
        self.y = 0.0
        self.orientation = 0.0
        self.isYellow = True
        self.wheel_right = 0.0
        self.wheel_left = 0.0

class Ball():
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

class WorldModel():
    def __init__(self):
        self.ball = Ball()
        self.yellows = []
        self.blues = []
        for i in range(5):
            yel = Robot()
            yel.id = i
            yel.isYellow = True
            self.yellows.append(yel)
            blu = Robot()
            blu.id = i
            blu.isYellow = False
            blu.isYellow = False
            self.blues.append(blu)

    def update_worldmodel(self, enviroment):
        self.ball.x = enviroment.frame.ball.x
        self.ball.y = enviroment.frame.ball.y
        self.ball.z = enviroment.frame.ball.z

        for i in range(len(enviroment.frame.robots_yellow)):
            self.blues[i].id = enviroment.frame.robots_yellow[i].robot_id
            self.blues[i].x = enviroment.frame.robots_yellow[i].x
            self.blues[i].y = enviroment.frame.robots_yellow[i].y
            self.blues[i].orientation = enviroment.frame.robots_yellow[i].orientation
        for i in range(len(enviroment.frame.robots_blue)):
            self.blues[i].id = enviroment.frame.robots_blue[i].robot_id
            self.blues[i].x = enviroment.frame.robots_blue[i].x
            self.blues[i].y = enviroment.frame.robots_blue[i].y
            self.blues[i].orientation = enviroment.frame.robots_blue[i].orientation


class GameStateEnum(Enum):
    Halt = 1
    PlayOn = 2
    Stop = 3
    KickOff = 4
    Penalty = 5
    FreeKick = 6
    GoalKick = 7
    FreeBallLeftTop = 8
    FreeBallRightTop = 9
    FreeBallLeftBot = 10
    FreeBallRightBot = 11


class ActorEnum(Enum):
    Yellow = 1
    Blue = 2
    NoOne = 3


class GameState():
    def __init__(self):
        self.state = GameStateEnum()
        self.actor = ActorEnum()
        self.state = GameStateEnum.Halt
        self.actor = ActorEnum.NoOne

