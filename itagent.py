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
                    self.make_move()
                    message.uuid = self.agentuuid
                    message.id = self.agentid
                    message.position = [self.agentpos[0], self.agentpos[1]]
                    message.freeze = self.agentFreeze
                    self.publish("ItTopic", message)
                    time.sleep(0.5)
                    if len(self.notitAgentsPos) == 0:
                        print("All Not It Agents Caught")
                        break
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
        minimum_distance = float('inf')
        closest_position = None
        keys_to_remove = []
        for key, value in self.notitAgentsPos.items():
            # If the not-it agent is frozen or has been caught (position equal to IT), mark for removal
            if value[2] == True or self.agentpos == value[:2]:
                keys_to_remove.append(key)
                continue
            distance = abs(self.agentpos[0] - value[0]) + abs(self.agentpos[1] - value[1])
            if distance < minimum_distance:
                minimum_distance = distance
                closest_position = value
        
        # Remove caught or frozen agents after the loop
        for key in keys_to_remove:
            self.notitAgentsPos.pop(key, None)
        
        if closest_position is not None:    
            if self.agentpos[0] < closest_position[0]:
                self.agentpos[0] += 1
            elif self.agentpos[0] > closest_position[0]:
                self.agentpos[0] -= 1
            elif self.agentpos[1] < closest_position[1]:
                self.agentpos[1] += 1
            elif self.agentpos[1] > closest_position[1]:
                self.agentpos[1] -= 1