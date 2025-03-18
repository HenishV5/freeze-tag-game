#!/usr/bin/env python3
import multiprocessing
import argparse
from node import Node
import time
import random
import tkinter as tk
import tkinter.messagebox as messagebox
from messages import agents, freezeCommand, start_stop
import uuid
from itagent import ITAgent
from notitagent import NotITAgent



#Game Class
class Game(Node):
    #Initializing Required Global Parameters
    def __init__(self, width, height, notitPos, itPos, num_not_it, debug_mode):
        super().__init__()
        #Map and Agent Position Parameters
        self.width = width
        self.height = height
        self.notitPos = notitPos
        self.itPos = itPos
        self.num_not_it = num_not_it
        
        #Debug Mode Parameter
        self.debug_mode = debug_mode

        #Storing Process
        self.processes = []

        #Status Management
        self.active_status = []

        


    def on_start(self):
        if self.debug_mode == True:
            print("Game Started...Initializing Agents")
        
        #Agents
        self.agents = {}

        #Storing Process
        self.processes = []

        #Creating Not IT Agents Message
        for i in range(self.num_not_it):
            notitAgent = agents()
            notitAgent.uuid = str(uuid.uuid1())
            notitAgent.id = i
            notitAgent.position = [self.notitPos[i][0], self.notitPos[i][1]]
            notitAgent.freeze = False
            self.agents[notitAgent.uuid] = notitAgent
            #self.active_status.append(notitAgent.uuid)
        
        self.nodes = []
        #Creating Not IT Agents
        for i in self.agents:
            notit_agent = NotITAgent(self.agents[i], self.width, self.height, self.debug_mode)
            self.nodes.append(notit_agent)            
        


        #Creating IT Agent Message
        itAgent = agents()
        itAgent.uuid = str(uuid.uuid1())
        self.itAgent_uuid = itAgent.uuid
        itAgent.id = -1
        itAgent.position = [self.itPos[0], self.itPos[1]]
        itAgent.freeze = False
        self.agents[itAgent.uuid] = itAgent
        self.active_status.append(itAgent.uuid)

        #Subscribing to Topics
        self.subscribe("NotItTopic", self.agent_handlers)
        self.subscribe("ItTopic", self.agent_handlers)
        
        #Creating IT Agents
        it_agent = ITAgent(itAgent, self.width, self.height, self.debug_mode)
        self.nodes.append(it_agent)

        self.gui = Grid(self.width, self.height, self.itPos, self.notitPos)
        self.gui.update_grid(self.agents)
        time.sleep(2)

        

        

        


    def run(self):
        try:
            #Starting Agents
            for node in self.nodes:
                process = multiprocessing.Process(target=node.launch_node, name=f"Agent Node {node.agentid}")
                if self.debug_mode == True:
                    print(f"Starting Agent {node.agentid}")
                process.start()
                self.processes.append(process)
            flag = True
            while flag == True:
                #Updating GUI Every Run
                self.gui.update_grid(self.agents)
                #print("Updating GUI")


                msg = start_stop()
                msg.start = True
                self.publish("Start_Stop", msg)
                
                count = 0
                #Checking for Freeze
                for key, value in self.agents.items():
                    if value.freeze == True:
                        count += 1
                    if count == self.num_not_it:
                        flag = False
                    if value.id == -1:
                        continue
                    else:
                        if self.agents[self.itAgent_uuid].position == value.position:
                            freezeMsg = freezeCommand()
                            freezeMsg.id = key
                            self.publish("FreezeTopic", freezeMsg)
                time.sleep(0.1)
            messagebox.showinfo("Game Over", "All NotIt agents are frozen")

        except Exception as e:
            print(f"Error running the game: {e}")

    def on_stop(self):
        try:
            for process in self.processes:
                if process.is_alive():
                    process.terminate()
                    process.join()
            print("Game Stopped...Agents Terminated")
            self.active_status.clear()
            self.agents.clear()
        except Exception as e:
            print(f"Error stopping the game: {e}")

    def agent_handlers(self, topic, message):
        try:
            message = agents.decode(message)
            if message.uuid in self.agents:
                self.agents[message.uuid] = message
                if self.debug_mode == True:
                    print(f"Agent {message.id} Position Updated: {message.position}")
        except Exception as e:
            print(f"Error handling agent message: {e}")        

    def active_status_management(self):
        pass




import tkinter as tk

class Grid(tk.Tk):
    def __init__(self, board_width, board_height, itPos, notitPos):
        tk.Tk.__init__(self)
        
        self.board_width = board_width   # Number of columns
        self.board_height = board_height # Number of rows
        self.itPos = itPos               # IT agent's [col, row] position
        self.notitPos = notitPos         # List of Not IT agents' positions

        # Get screen dimensions.
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Compute the grid cell size such that the entire board fits in the screen.
        # For a given board, a larger number of cells yields a smaller grid size.
        computed_size = min(screen_width // board_width, screen_height // board_height)
        
        # For a standard board of 50x50, we want grid size 15.
        if board_width == 50 and board_height == 50:
            self.grid_size = 16
        else:
            self.grid_size = computed_size

        # Create a canvas sized exactly for the grid.
        self.canvas = tk.Canvas(self, width=board_width * self.grid_size, 
                                     height=board_height * self.grid_size)
        self.canvas.pack()

        # Draw vertical lines (including the left and right edges)
        for col in range(self.board_width + 2):
            x = col * self.grid_size
            self.canvas.create_line(x, 0, x, self.board_height * self.grid_size)

        # Draw horizontal lines (including the top and bottom edges)
        for row in range(self.board_height + 2):
            y = row * self.grid_size
            self.canvas.create_line(0, y, self.board_width * self.grid_size, y)


        # Draw the IT agent.
        self.itAgent = self.canvas.create_rectangle(
            itPos[0] * self.grid_size, itPos[1] * self.grid_size,
            itPos[0] * self.grid_size + self.grid_size, itPos[1] * self.grid_size + self.grid_size,
            fill="green"
        )

        # Draw the Not IT agents.
        self.notitAgents = []
        for pos in self.notitPos:
            rect = self.canvas.create_rectangle(
                pos[0] * self.grid_size, pos[1] * self.grid_size,
                pos[0] * self.grid_size + self.grid_size, pos[1] * self.grid_size + self.grid_size,
                fill="red"
            )
            self.notitAgents.append(rect)

    def update_grid(self, agents):
        """
        agents: a dictionary where each value has:
          - .id (with -1 for the IT agent)
          - .position (a [col, row] list)
          - .freeze (a Boolean indicating if a Not IT agent is frozen)
        """
        itPos = None
        notitPosList = []
        notitFreezeList = []
        for key, value in agents.items():
            if value.id == -1:
                itPos = value.position
            else:
                notitPosList.append(value.position)
                notitFreezeList.append(value.freeze)

        if itPos is not None:
            self.canvas.coords(self.itAgent,
                itPos[0] * self.grid_size, itPos[1] * self.grid_size,
                itPos[0] * self.grid_size + self.grid_size, itPos[1] * self.grid_size + self.grid_size
            )

        for i, pos in enumerate(notitPosList):
            if i < len(self.notitAgents):
                self.canvas.coords(self.notitAgents[i],
                    pos[0] * self.grid_size, pos[1] * self.grid_size,
                    pos[0] * self.grid_size + self.grid_size, pos[1] * self.grid_size + self.grid_size
                )
                fill_color = "blue" if notitFreezeList[i] else "red"
                self.canvas.itemconfig(self.notitAgents[i], fill=fill_color)

        self.update_idletasks()

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
    parser.add_argument('--debug', action='store_true', help='Debug Mode')
    args = parser.parse_args()
    width = args.width
    height = args.height
    debug_mode = args.debug
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
    game_node = Game(width, height, notitPos, itPos, args.num_not_it, debug_mode)
    game_node.process = multiprocessing.Process(target=game_node.launch_node, name="Game Node")
    game_node.process.start()
if __name__ == '__main__':
    main()
