import time
from src.node import Node
from messages import agents, start_stop, freezeCommand
import random

class NotITAgent(Node):
    def __init__(self, agent, width, height, debug_mode):
        super().__init__()
        self.agentuuid = agent.uuid
        self.agentid = agent.id
        self.agentpos = [agent.position[0], agent.position[1]]
        self.agentFreeze = agent.freeze
        self.width = width
        self.height = height
        self.debug_mode = debug_mode
        self.otherPos = {}
        self.start = False

    def on_start(self):
        self.subscribe("Start_Stop", self.start_call)
        self.subscribe("FreezeTopic", self.freeze_handler)
        self.subscribe("NotItTopic", self.othernotit_agent_handler)
        
        

    def run(self):
        while True:
            if self.agentFreeze:
                message = agents()
                message.uuid = self.agentuuid
                message.id = self.agentid
                message.position = [self.agentpos[0], self.agentpos[1]]
                message.freeze = True
                self.publish("NotItTopic", message)
                break
            if self.start:
                self.make_move()
                message = agents()
                message.uuid = self.agentuuid
                message.id = self.agentid
                message.position = [self.agentpos[0], self.agentpos[1]]
                message.freeze = self.agentFreeze
                self.publish("NotItTopic", message)
                time.sleep(1)

    def othernotit_agent_handler(self, topic, message):
        try:
            message = agents.decode(message)
            if message.uuid != self.agentuuid:
                self.otherPos[message.uuid] = message.position
        except Exception as e:
            print(f"Error handling other Not-It agents message: {e}")
        

    def on_stop(self):
        pass

    def freeze_handler(self, topic, message):
        try:
            message = freezeCommand.decode(message)
            if message.id == self.agentuuid:
                if not self.agentFreeze:
                    print(f"Agent {self.agentid} Freezed")
                    self.agentFreeze = True
                    # Immediately publish the frozen update
                    update_msg = agents()
                    update_msg.uuid = self.agentuuid
                    update_msg.id = self.agentid
                    update_msg.position = [self.agentpos[0], self.agentpos[1]]
                    update_msg.freeze = True
                    self.publish("NotItTopic", update_msg)
        except Exception as e:
            print(f"Error handling freeze command: {e}")
                

    def make_move(self):
        movement = random.choice([[0, 1], [0, -1], [1, 0], [-1, 0]])
        if self.agentpos[0] + movement[0] >= 0 and self.agentpos[0] + movement[0] < self.width and self.agentpos[1] + movement[1] >= 0 and self.agentpos[1] + movement[1] < self.height:
            self.agentpos[0] += movement[0]
            self.agentpos[1] += movement[1]
            for key, value in self.otherPos.items():
                if self.agentpos[0] == value[0] and self.agentpos[1] == value[1]:
                    self.agentpos[0] -= movement[0]
                    self.agentpos[1] -= movement[1]
                    break
    
    def start_call(self, topic, message):
        try:
            message = start_stop.decode(message)
            if message.start:
                self.start = True
        except Exception as e:
            print(f"Error handling Getting Start Call: {e}")