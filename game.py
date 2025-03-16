# game.py
import multiprocessing
import argparse
from node import Node
import random
import numpy as np
import time
import tkinter as tk
from messages.agents import agents
import uuid

class GameNode(Node):
    def __init__(self, width, height, notitPos, itPos):
        super().__init__()
        self.width = width
        self.height = height
        self.notitPos = notitPos
        self.itPos = itPos
        self.globalStates = np.zeros((self.width, self.height))
        self.agentUUID = {}
        self.agentPos = {}

    def on_start(self):
        print("Game Node Started")
        all_Agents = []
        itagent = agents()
        itagent.uuid = str(uuid.uuid4())
        itagent.id = -1
        itagent.position = [1, 1]
        itagent.freeze = False
        self.processes = []
        
        
        for i, pos in enumerate(self.notitPos):
            notitagent = agents()
            notitagent.id = i
            self.agentUUID[i] = "0"
            notitagent.position = pos
            notitagent.freeze = False
            all_Agents.append(notitagent)
        
        
        itNode = ItNode(itagent)
        itNode_process = multiprocessing.Process(target=itNode.launch_node, name="It Node")
        itNode_process.start()
        self.processes.append(itNode_process)



        for agent in all_Agents:
            notItNode = NotItNode(agent, self.width, self.height)
            notItNode_process = multiprocessing.Process(target=notItNode.launch_node, name="Not It Node")
            notItNode_process.start()
            self.processes.append(notItNode_process)

        print("All Nodes Launched")







    def run(self):
        while True:    
            print("Game Node Running")
            self.subscribe("NotItMessage", self.my_handler)
            self.publish("agentPos", self.agentPos)
            self.subscribe("itAgent", self.it_handler)
            time.sleep(0.5)





    def on_stop(self):
        print("Game Node Stopped")

    def it_handler(self, channel, data):
        msg = agents.decode(data)
        self.agentUUID[msg.id] = msg.uuid
        self.agentPos[msg.id] = msg.position
        print(f"Received message on {channel} | ID: {msg.id} | UUID: {msg.uuid} | Position: {msg.position} | Enabled: {msg.freeze}")


    def my_handler(self, channel, data):
        msg = agents.decode(data)
        if(self.agentUUID[msg.id] != msg.uuid):
            self.agentUUID[msg.id] = msg.uuid
            self.agentPos[msg.id] = msg.position
            print(f"Received message on {channel} | ID: {msg.id} | UUID: {msg.uuid} | Position: {msg.position} | Enabled: {msg.freeze}")




class ItNode(Node):
    def __init__(self, agent):
        super().__init__()
        self.id = agent.id
        self.uuid = agent.uuid
        self.position = agent.position
        self.freeze = agent.freeze
        self.notitPos = agent.position
        self.move = [[1, 0], [-1, 0], [0, 1], [0, -1]]
    
    def on_start(self):
        print("It Node Started")

    def run(self):
        while True:
            print("It Node Running{%d}", self.id)
            self.subscribe("agentPos", self.notit_handler)
            self.make_move()
            message = agents()
            message.uuid = self.uuid
            message.id = self.id
            message.position = self.position
            message.freeze = self.freeze
            self.publish("itAgent", message)
            time.sleep(0.5)

            
    def make_move(self):
        #find which move make the distance between the agent and the closest agent smaller
        minimum_distance = 1000000
        for temp in self.move:
            new_pos = [self.position[0] + temp[0], self.position[1] + temp[1]]
            calculated_distance = np.linalg.norm(np.array(new_pos) - np.array(self.notitPos))
            if calculated_distance < minimum_distance:
                minimum_distance = calculated_distance
                self.position = new_pos

    def notit_handler(self, channel, data):
        msg = agents.decode(data)
        minimum_distance = 1000000
        for key, value in msg.items():
            calculated_distance = np.linalg.norm(np.array(self.position) - np.array(value))
            if calculated_distance < minimum_distance:
                minimum_distance = calculated_distance
                self.closest_agent = key
                self.notitPos = value

        




    def on_stop(self):
        print("It Node Stopped")






class NotItNode(Node):
    def __init__(self, agent, width, height):
        super().__init__()
        self.id = agent.id
        self.width = width
        self.height = height
        self.position = agent.position
        self.freeze = agent.freeze
        self.move = [[1, 0], [-1, 0], [0, 1], [0, -1]]
    
    def on_start(self):
        print("Not It Node Started")

    def run(self):
        while True:
            
            message = agents()
            message.uuid = str(uuid.uuid1())
            message.id = self.id
            self.subscribe("freeze", self.freeze_handler)
            if self.freeze:
                print("Not It Node Frozen{%d}", self.id)
                message.position = self.position
                message.freeze = self.freeze
                message.uuid = self.uuid
                self.publish("NotItMessage", message)
                break
            self.make_move()
            message.position = self.position
            message.freeze = self.freeze
            self.publish("NotItMessage", message)
            time.sleep(1)
            print("Not It Node Running{%d}", self.id)
    
    def make_move(self):
        move = random.choice(self.move)
        self.position = [self.position[0] + move[0], self.position[1] + move[1]]
        self.position[0] = max(0, min(self.position[0], self.width - 1))
        self.position[1] = max(0, min(self.position[1], self.height - 1))

    def freeze_handler(self, channel, data):
        msg = agents.decode(data)
        if(msg.id == self.id):
            self.freeze = msg.freeze
            print(f"Received message on {channel} | ID: {msg.id} | UUID: {msg.uuid} | Position: {msg.position} | Enabled: {msg.freeze}")

    def on_stop(self):
        print("Not It Node Stopped")





def main():

    #Parsing Arguments
    parser = argparse.ArgumentParser(description='Freezer Tag.')
    parser.add_argument('--width', type=int, default=0, required = True, help='Width of the Map')
    parser.add_argument('--height', type=int, default=0, required = True, help='Height of the Map')
    parser.add_argument('--notitPos', type=int, nargs="+", default=0, required = True, help='Position of the Not It Player')

    args = parser.parse_args()
    height = args.height
    width = args.width
    if len(args.notitPos) % 2 != 0: #Changing it later with better solution for error catching
        raise ValueError("The number of not it player positions must be even")
    notitPos = [(args.notitPos[i], args.notitPos[i+1]) for i in range(0, len(args.notitPos), 2)]
    itPos = notitPos[-2:]
    notitPos = notitPos[:-2]

    # Example of launching a Node and then killing it.
    node = GameNode(width, height, notitPos, itPos)
    node_process = multiprocessing.Process(target=node.launch_node, name="Node")
    node_process.start()
    node_process.join()

if __name__ == "__main__":
    main()
