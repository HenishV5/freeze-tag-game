#!/usr/bin/env python3
import multiprocessing
import argparse
from node import Node
import numpy as np
import time
import random
import tkinter as tk
from messages import agents
from messages import freezeCommand
import uuid



class Game(Node):
    def __init__(self, width, height, notitPos, itPos):
        super().__init__()

        # Parameter Initialization
        self.width = width
        self.height = height
        self.notitAgent_Pos = notitPos
        self.itAgent_Pos = itPos

    def on_start(self):
        self.agentUUIDs = {}
        self.allAgents_Pos = {}

        # Process Store
        processes = []

        # Creating IT Agent
        itAgentMessage = agents()
        itAgentMessage.id = -1
        itAgentMessage.uuid = str(uuid.uuid4())
        itAgentMessage.position = [self.itAgent_Pos[0], self.itAgent_Pos[1]]
        itAgentMessage.freeze = False

        self.agentUUIDs[-1] = itAgentMessage.uuid
        self.allAgents_Pos[-1] = [self.itAgent_Pos[0], self.itAgent_Pos[1]]

        notitAgents = []
        # Creating Not It Agents
        for i, pos in enumerate(self.notitAgent_Pos):
            notitAgentMessage = agents()
            notitAgentMessage.id = i
            notitAgentMessage.uuid = str(uuid.uuid4())
            notitAgentMessage.position = [pos[0], pos[1]]
            notitAgentMessage.freeze = False
            notitAgents.append(notitAgentMessage)
            # Create Not It Node

            self.agentUUIDs[i] = notitAgentMessage.uuid
            self.allAgents_Pos[i] = [pos[0], pos[1]]
            
        notitNodes = []
        # Creating Not It Nodes
        for agent in notitAgents:
            notitNode = NotIt(agent, self.width, self.height)
            notitNodes.append(notitNode)

        # Creating Subscribers
        self.subscribe("NotItTopic", self.agents_handler)
        self.subscribe("ItTopic", self.agents_handler)
        
        # Creating IT Node
        itNode = It(itAgentMessage, self.width, self.height)
        
        # Launching Not It Nodes
        for node in notitNodes:
            node.process = multiprocessing.Process(target=node.launch_node, name="Not It Node")
            node.process.start()
            processes.append(node.process)

        # Launching IT Node
        itNode.process = multiprocessing.Process(target=itNode.launch_node, name="It Node")
        itNode.process.start()
        processes.append(itNode.process)
            
    def run(self):
        gui = Grid(self.width, self.height, self.itAgent_Pos, self.notitAgent_Pos)
        while True:
            # Update GUI with current positions
            gui.update_grid(self.allAgents_Pos)
            for key, value in self.allAgents_Pos.items():
                if key == -1:
                    continue
                if self.allAgents_Pos[-1] == value:
                    freezeMsg = freezeCommand()
                    freezeMsg.id = key
                    self.publish("freezeAgent", freezeMsg)
            time.sleep(0.1)

    def on_stop(self):
        pass

    def agents_handler(self, topic, message):
        message = agents.decode(message)
        if self.agentUUIDs[message.id] != message.uuid:
            self.agentUUIDs[message.id] = message.uuid
            self.allAgents_Pos[message.id] = [message.position[0], message.position[1]]
            print("Agent ID: ", message.id, "Agent UUID: ", message.uuid,
                  "Agent Position: ", message.position, "Agent Freeze: ", message.freeze)



class It(Node):
    def __init__(self, agentInfo, width, height):
        super().__init__()
        self.agentID = agentInfo.id
        self.agentUUID = agentInfo.uuid
        self.agentPosition = [agentInfo.position[0], agentInfo.position[1]]
        self.agentFreeze = agentInfo.freeze
        self.width = width
        self.height = height
        self.notitAgents_Pos = {}
        self.kill = False

    def on_start(self):
        self.subscribe("NotItTopic", self.notit_handler)

    def run(self):
        while True:
            message = agents()
            message.id = self.agentID
            message.uuid = str(uuid.uuid4())
            self.make_move()
            message.position = self.agentPosition
            message.freeze = self.agentFreeze
            
            # Publishing the ItAgent Message
            self.publish("ItTopic", message)
            time.sleep(0.5)

    def on_stop(self):
        pass

    def notit_handler(self, topic, message):
        message = agents.decode(message)
        self.notitAgents_Pos[message.id] = [message.position[0], message.position[1], message.freeze]

    def make_move(self):
        minimum_distance = float('inf')
        closest_position = None
        keys_to_remove = []
        for key, value in self.notitAgents_Pos.items():
            # If the not-it agent is frozen or has been caught (position equal to IT), mark for removal
            if value[2] == True or self.agentPosition == value[:2]:
                keys_to_remove.append(key)
                continue
            distance = abs(self.agentPosition[0] - value[0]) + abs(self.agentPosition[1] - value[1])
            if distance < minimum_distance:
                minimum_distance = distance
                closest_position = value
        
        # Remove caught or frozen agents after the loop
        for key in keys_to_remove:
            self.notitAgents_Pos.pop(key, None)
        
        if closest_position is not None:    
            if self.agentPosition[0] < closest_position[0]:
                self.agentPosition[0] += 1
            elif self.agentPosition[0] > closest_position[0]:
                self.agentPosition[0] -= 1
            elif self.agentPosition[1] < closest_position[1]:
                self.agentPosition[1] += 1
            elif self.agentPosition[1] > closest_position[1]:
                self.agentPosition[1] -= 1



class NotIt(Node):
    def __init__(self, agentInfo, width, height):
        super().__init__()
        self.agentID = agentInfo.id
        self.agentUUID = agentInfo.uuid
        self.agentPosition = [agentInfo.position[0], agentInfo.position[1]]
        self.agentFreeze = agentInfo.freeze
        self.move_options = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        self.width = width
        self.height = height

    def on_start(self):
        pass

    def run(self):
        while True:
            message = agents()
            message.id = self.agentID
            message.uuid = str(uuid.uuid4())
            self.subscribe("freezeAgent", self.freeze)
            message.freeze = self.agentFreeze
            if self.agentFreeze:
                break
            self.make_move()
            message.position = self.agentPosition
            
            # Publishing the NotItAgent Message
            self.publish("NotItTopic", message)
            time.sleep(1)

    def on_stop(self):
        print(f"Stopping Not It Agent {self.agentID}")

    def make_move(self):
        movement = random.choice(self.move_options)
        self.agentPosition[0] = max(0, min(self.agentPosition[0] + movement[0], self.width-1))
        self.agentPosition[1] = max(0, min(self.agentPosition[1] + movement[1], self.height-1))
    
    def freeze(self, topic, message):
        message = freezeCommand.decode(message)
        if message.id == self.agentID:
            self.agentFreeze = True


class Grid(tk.Tk):
    def __init__(self, width, height, itPos, notitPos):
        tk.Tk.__init__(self)
        self.width = width
        self.height = height
        self.itPos = itPos
        self.notitPos = notitPos
        self.grid_size = 20
        self.canvas = tk.Canvas(self, width=width*self.grid_size, height=height*self.grid_size)
        self.canvas.pack()
        

        # Creating Grid lines
        for i in range(1, self.width*self.grid_size, self.grid_size):
            self.canvas.create_line(i, 0, i, self.height*self.grid_size)
        for i in range(1, self.height*self.grid_size, self.grid_size):
            self.canvas.create_line(0, i, self.width*self.grid_size, i)

        # Creating IT Agent
        self.itAgent = self.canvas.create_rectangle(self.itPos[0]*self.grid_size, self.itPos[1]*self.grid_size,
                                                    self.itPos[0]*self.grid_size+self.grid_size, self.itPos[1]*self.grid_size+self.grid_size, fill="red")
        # Creating Not IT Agents
        self.notitAgents = []
        for pos in self.notitPos:
            self.notitAgents.append(
                self.canvas.create_rectangle(pos[0]*self.grid_size, pos[1]*self.grid_size, pos[0]*self.grid_size+self.grid_size, pos[1]*self.grid_size+self.grid_size, fill="blue")
            )

    def update_grid(self, agentPos):
        itPos = None
        notitPosList = []
        for key, value in agentPos.items():
            if key == -1:
                itPos = value
            else:
                notitPosList.append(value)

        if itPos is not None:
            self.canvas.coords(self.itAgent, itPos[0]*self.grid_size, itPos[1]*self.grid_size, itPos[0]*self.grid_size+self.grid_size, itPos[1]*self.grid_size+self.grid_size)

        for i, pos in enumerate(notitPosList):
            if i < len(self.notitAgents):
                self.canvas.coords(self.notitAgents[i], pos[0]*self.grid_size, pos[1]*self.grid_size, pos[0]*self.grid_size+self.grid_size, pos[1]*self.grid_size+self.grid_size)

        # Optionally process pending events without causing recursion:
        tk.Tk.update_idletasks(self)

    def on_closing(self):
        self.destroy()
        self.quit()

    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()




# Main Function to execute the game
def main():
    parser = argparse.ArgumentParser(description='Freezer Tag Game')
    parser.add_argument('--width', type=int, default=0, required=True, help='Width of the game board')
    parser.add_argument('--height', type=int, default=0, required=True, help='Height of the game board')
    parser.add_argument('--num-not-it', type=int, default=0, required=True, help='Number of Not It Players')
    parser.add_argument('--notitPos', type=int, nargs='+', required=True, help='Position of the not it player')
    parser.add_argument('--itPos', type=int, nargs='+', required=True, help='Position of the it player')
    args = parser.parse_args()
    width = args.width
    height = args.height
    itPos = [args.itPos[0], args.itPos[1]]
    if (itPos[0]<0 or itPos[0]>=width) or (itPos[1]<0 or itPos[1]>=height):
        raise ValueError("Invalid IT Player Position")
        
        
    notitPos = []
    for i in range(0, len(args.notitPos), 2):
        if (args.notitPos[i]<0 or args.notitPos[i]>=width) or (args.notitPos[i+1]<0 or args.notitPos[i+1]>=height):
            raise ValueError("Invalid NotIT Player Position")
        notitPos.append([args.notitPos[i], args.notitPos[i+1]])
    
    if(len(notitPos) != args.num_not_it):
        raise ValueError("Number of Not It Players and Not It Player Positions do not match")
    game_node = Game(width, height, notitPos, itPos)
    game_node.process = multiprocessing.Process(target=game_node.launch_node, name="Game Node")
    game_node.process.start()
    game_node.process.join()

if __name__ == '__main__':
    main()
