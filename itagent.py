import time
from node import Node
from messages import agents, start_stop

class ITAgent(Node):
    def __init__(self, agent, width, height, debug_mode):
        super().__init__()
        self.agentuuid = agent.uuid
        self.agentid = agent.id
        self.agentpos = [agent.position[0], agent.position[1]]
        self.agentFreeze = agent.freeze
        self.width = width
        self.height = height
        self.debug_mode = debug_mode
        self.freeze = False
        self.start = False
        self.notitAgentsPos = {}

    def on_start(self):
        self.subscribe("Start_Stop", self.start_call)
        self.subscribe("NotItTopic", self.getNotItPositions)

    def run(self):
        try:
            while True:
                message = agents()
                if self.start == True:
                    if len(self.notitAgentsPos) == 0:
                        print("All Not It Agents Caught")
                        break
                    self.make_move()
                    message.uuid = self.agentuuid
                    message.id = self.agentid
                    message.position = [self.agentpos[0], self.agentpos[1]]
                    message.freeze = self.agentFreeze
                    self.publish("ItTopic", message)
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"Error running the IT Agent: {e}")

    def on_stop(self):
        pass

    def start_call(self, topic, message):
        try:
            message = start_stop.decode(message)
            if message.start:
                self.start = True
        except Exception as e:
            print(f"Error handling Getting Start Call: {e}")

    def getNotItPositions(self, topic, message):
        try:
            message = agents.decode(message)
            self.notitAgentsPos[message.uuid] = [message.position[0], message.position[1], message.freeze]
        except Exception as e:
            print(f"Error Getting NotIt Agent Positions: {e}")
        

    def make_move(self):
        try:
            keys_to_remove = [
                key for key, value in self.notitAgentsPos.items() if value[2] == True or self.agentpos == value[:2]
            ]

            # Remove caught or frozen agents after the loop
            for key in keys_to_remove:
                self.notitAgentsPos.pop(key, None)

            targets = [(value[0], value[1]) for key, value in self.notitAgentsPos.items() if value[2] == False]
            if not targets:
                return

            agentPos = (self.agentpos[0], self.agentpos[1])
            route = []
            remaining_targets = targets.copy()
            while remaining_targets:
                nearest = min(remaining_targets, key=lambda pos: abs(agentPos[0] - pos[0]) + abs(agentPos[1] - pos[1]))
                route.append(nearest)
                remaining_targets.remove(nearest)
            next_target = route[0]

            new_x, new_y = self.agentpos[0], self.agentpos[1]
            if agentPos[0] < next_target[0]:
                new_x += 1
            elif agentPos[0] > next_target[0]:
                new_x -= 1
            elif agentPos[1] < next_target[1]:
                new_y += 1
            elif agentPos[1] > next_target[1]:
                new_y -= 1
            
            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                self.agentpos = [new_x, new_y]
            else:
                print("Invalid move")
        except Exception as e:
            print(f"Error Making Move: {e}")