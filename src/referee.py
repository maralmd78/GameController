import sys
sys.path.insert(1, '../protoCompiled')

from protoCompiled.SIM2REF import packet_pb2
from protoCompiled import common_pb2
from protoCompiled.REF2CLI import messages_pb2, service_pb2_grpc, service_pb2
from src.firasimClient import FIRASimClient
from src.firasimServer import FIRASimServer
from src.teamClient import TeamClient
from src.threadClient import ThreadClient, WhatToCallEnum
from src.common import WorldModel, GameState, ActorEnum, Converter
from multiprocessing import Process
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSlot, QTimer, QObject
from src.gameControllerWidget import GameControllerWidget
import math, time


class Referee():
    def __init__(self):
        self.app = QApplication(sys.argv)

        self.firasimserver = FIRASimServer('127.0.0.1', 50055)
        self.firasimclient = FIRASimClient('127.0.0.1', 50051)
        self.yellowThread = ThreadClient('127.0.0.1', 50053, True, self.firasimclient)
        self.blueThread = ThreadClient('127.0.0.1', 50052, False, self.firasimclient)

        self.yellowThread.set_arguments(WhatToCallEnum.Register)
        self.blueThread.set_arguments(WhatToCallEnum.Register)
        self.yellowThread.wait()
        self.blueThread.wait()


        self.firasimserver.set_function(self.vision_detection)
        self.worldmodel = WorldModel()
        self.gamestate = GameState()
        self.converter = Converter()
        self.gamecontrollerWidget = None
        self.createGUI()
        self.gamecontrollerWidget.set_teamnames(self.yellowThread.teamName, self.blueThread.teamName)

        sys.exit(self.app.exec_())



    def vision_detection(self, data):
        environment = packet_pb2.Environment()
        environment.ParseFromString(data)
        # self.worldmodel.update_worldmodel(environment)

        (foulinfo_yellow, foulinfo_blue) = self.generate_foulinfo()
        (frame_yellow, frame_blue) = self.generate_frame(environment)

        if self.gamestate.need_ball_placement():
            if self.gamestate.actor == ActorEnum.Yellow:
                self.yellowThread.set_arguments(WhatToCallEnum.SetBall, frame_yellow, foulinfo_yellow)
            else:
                self.blueThread.set_arguments(WhatToCallEnum.SetBall, frame_blue, foulinfo_blue)
        elif self.gamestate.need_robot_placement():
            self.yellowThread.set_arguments(WhatToCallEnum.SetFormerRobots, frame_yellow, foulinfo_yellow)
            self.blueThread.set_arguments(WhatToCallEnum.SetLaterRobots, frame_blue, foulinfo_blue)
        elif self.gamestate.is_play_on():
            self.yellowThread.set_arguments(WhatToCallEnum.RunStrategy, frame_yellow, foulinfo_yellow)
            self.blueThread.set_arguments(WhatToCallEnum.RunStrategy, frame_blue, foulinfo_blue)


    def createGUI(self):
        self.gamecontrollerWidget = GameControllerWidget()
        self.gamecontrollerWidget.button_clicked.connect(self.button_listener)
        self.gamecontrollerWidget.widget_closed.connect(self.widget_closed)

    def widget_closed(self):
        pass

    def button_listener(self, buttonName):
        dict_state = {'pbPlaceKickBlue': messages_pb2.FoulInfo.FoulType.PlaceKick,
                'pbPnaltyKickBlue': messages_pb2.FoulInfo.FoulType.PenaltyKick,
                'pbFreeKickBlue': messages_pb2.FoulInfo.FoulType.FreeKick,
                'pbGoalKickBlue': messages_pb2.FoulInfo.FoulType.GoalKick,
                'pbFreeBallLeftTopBlue': messages_pb2.FoulInfo.FoulType.FreeBallLeftTop,
                'pbFreeBallRightTopBlue': messages_pb2.FoulInfo.FoulType.FreeBallRightTop,
                'pbFreeBallLeftBotBlue': messages_pb2.FoulInfo.FoulType.FreeBallLeftBot,
                'pbFreeBallRightBotBlue': messages_pb2.FoulInfo.FoulType.FreeBallRightBot,

                'pbPlaceKickYellow': messages_pb2.FoulInfo.FoulType.PlaceKick,
                'pbPnaltyKickYellow': messages_pb2.FoulInfo.FoulType.PenaltyKick,
                'pbFreeKickYellow': messages_pb2.FoulInfo.FoulType.FreeKick,
                'pbGoalKickYellow': messages_pb2.FoulInfo.FoulType.GoalKick,
                'pbFreeBallLeftTopYellow': messages_pb2.FoulInfo.FoulType.FreeBallLeftTop,
                'pbFreeBallRightTopYellow': messages_pb2.FoulInfo.FoulType.FreeBallRightTop,
                'pbFreeBallLeftBotYellow': messages_pb2.FoulInfo.FoulType.FreeBallLeftBot,
                'pbFreeBallRightBotYellow': messages_pb2.FoulInfo.FoulType.FreeBallRightBot,

                'pbPlayOn': messages_pb2.FoulInfo.FoulType.PlayOn
                }
        dict_phase = {'pbStop': messages_pb2.FoulInfo.PhaseType.Stopped,
                      'pbfirstHalf': messages_pb2.FoulInfo.PhaseType.FirstHalf,
                      'pbsecondHalf': messages_pb2.FoulInfo.PhaseType.SecondHalf,
                      'pbpenalty': messages_pb2.FoulInfo.PhaseType.PenaltyShootout
        }
        try:
            self.gamestate.state = dict_state[buttonName]
        except:
            pass

        self.gamestate.actor = ActorEnum.Blue if buttonName.endswith('Blue') else ActorEnum.Yellow

        try:
            self.gamestate.phase = dict_phase[buttonName]
        except:
            pass
        print('state = {}, actor = {}, phase = {}'.format(self.gamestate.state, self.gamestate.actor, self.gamestate.phase))



    def generate_foulinfo(self):
        foulinfo_yellow = messages_pb2.FoulInfo()
        foulinfo_yellow.type = self.gamestate.state
        foulinfo_yellow.phase = self.gamestate.phase

        foulinfo_blue = messages_pb2.FoulInfo()
        foulinfo_blue.CopyFrom(foulinfo_yellow)
        if self.gamestate.actor == ActorEnum.Yellow:
            foulinfo_blue.actor = messages_pb2.Side.Opponent
            foulinfo_yellow.actor = messages_pb2.Side.Self
        else:
            foulinfo_yellow.actor = messages_pb2.Side.Opponent
            foulinfo_blue.actor = messages_pb2.Side.Self

        return foulinfo_yellow, foulinfo_blue

    def generate_frame(self, environment):
        frame_blue = common_pb2.Frame()
        frame_yellow = common_pb2.Frame()
        frame_blue.CopyFrom(environment.frame)
        frame_yellow.CopyFrom(environment.frame)
        frame_yellow.ball.x *= -1
        for robot in frame_yellow.robots_yellow:
            robot.x *= -1
            robot.orientation = math.pi - robot.orientation
        for robot in frame_yellow.robots_blue:
            robot.x *= -1
            robot.orientation = math.pi - robot.orientation

        return frame_yellow, frame_blue

    def runStrategy_teams(self, frame, foulInfo):
        yellowCommand = self.yellowClient.call_RunStrategy(frame, foulInfo)
        BlueCommand = self.blueClient.call_RunStrategy(frame, foulInfo)
        yelbot = self.converter.convert_protocommand_to_Robot(yellowCommand, True)
        blubot = self.converter.convert_protocommand_to_Robot(BlueCommand, False)
        self.firasimclient.send_robot_command(yelbot, blubot)

    def robotPlacement_teams(self, frame, foulInfo):
        if self.gamestate.actor == ActorEnum.Yellow:
            yelbot = self.yellowClient.call_SetFormerRobots(frame, foulInfo)
            blubot = self.blueClient.call_SetLaterRobots(frame, foulInfo)
        else:
            blubot = self.blueClient.call_SetFormerRobots(frame, foulInfo)
            yelbot = self.yellowClient.call_SetLaterRobots(frame, foulInfo)
        yelbot = self.converter.convert_protoRobots_to_Robot(yelbot, True)
        blubot = self.converter.convert_protoRobots_to_Robot(blubot, False)
        self.firasimclient.send_robot_replacement(yelbot, blubot)

    def ballPlacement_teams(self, frame, foulInfo):
        if self.gamestate.actor == ActorEnum.Yellow:
            protoball = self.yellowClient.call_SetBall(frame, foulInfo)
        else:
            protoball = self.blueClient.call_SetBall(frame, foulInfo)
        ball = self.converter.convert_protoBall_to_Ball(protoball)
        self.firasimclient.send_ball_replacement(ball)


if __name__ == "__main__":
    referee = Referee()
