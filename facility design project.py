################################################################################################
################################ FACILITY DESIGN PROJECT - 2020 ################################
########################### Tal Eylon, Avihoo Menahem, Amihai Kalev ############################
################################################################################################

################################################################################################
# Imports
################################################################################################

import pandas as pd
import numpy as np
import pickle as p
import random


random.seed(666)


################################################################################################
# Classes
################################################################################################

#######################
# 1. Item
#######################

class Item:
    def __init__(self,item_number,exit=0,side=0):
        self.number = item_number # item catalog number
        self.exit = exit          # Can be either False/True. True means that the item needs to be taken out of the warehouse
        self.side = side          # 1 if the item is located on the left side of the warehouse, 2 on the right side, 
                                  # 3 if exactly on the center (column 7)
    
    def __str__(self):            # Allows visual presentation of the item
        if self.exit:
            return str("%s to exit"%(self.number))
        else:
            return str("%s"%(self.number))


#######################
# 2. Escort
#######################


class Escort:
    def __init__(self, robot_id):
        self.robot_id = robot_id # this escort belong to this robot_id
        self.number = 0          # escort number
        self.exit = 0
    
    def contains(self):
        return False # it isn't an item but an escort
    
    def __str__(self):
        return str("0")

#######################
# 3. Robot
#######################

class Robot:
    def __init__(self,robot_id,side):
        self.id = robot_id                  # The robot id. Can be either 1,2,3,4 or 5
        self.item_to_take = None            # will be equal to the item that the robot is on its way to
        self.currently_taking = None        # will be equal to the item's number the robot is taking to the IO
        self.path = None                    # the steps the robot will take
        self.side = None                    # The robot can exit items only on the relevant side of the warehouse
    
    def robot_will_take(self, item_number): # This function sets the item to take, and erases the currently taking item (if exists)
        self.item_to_take = item_number
        self.currently_taking = None
    
    def robot_is_taking(self, item_number): # This function sets the currently taking attribute, and erases the item to take item (if exists)
        self.item_to_take = None
        self.currently_taking = item_number
    
    def reset(self):                        # This function erases the attributes of the item, except its id and side.
        self.item_to_take = None
        self.currently_taking = None
        self.path = None
        
    def is_free(self):                      # checks if the robot is free to take an item.
        if self.item_to_take == None and self.currently_taking == None and self.path == None:
            print("robot %s is free"%(self.id))
            return True
        else:
            print("robot %s is not free"%(self.id))
            return False
    
    def __str__(self):                      # Allows visual presentation of the robot
        return str("Robot %s"%(self.id))


#######################
# 4. Cell
#######################


class Cell:
    def __init__(self, item_number=0, exit=0, robot_id=0, side=0): 
        # A cell can either contain: (item,robot) (escort,robot) (escort,) (item,)
        if item_number == 0: #is it an escort?
            self.item = Escort(robot_id)                   # Escort in cell
            self.robot = Robot(robot_id,side)              # We assume that the robot, at the beginning, is in the place of the escorts.
        else:
            self.item = Item(item_number, exit, side)      # item in cell, with respect to his location in the warehouse
            self.robot = ''
            
    def assignRobot(self, robot):
        self.robot = robot
        
    def assignItem(self, item):
        self.item = item
            
    def __repr__(self):                                     # Allows visual presentation of the cell
        rbt = self.robot
        itm = self.item
        return "[%s,%s]"%(itm,rbt)
        
    def __str__(self):                                      # Allows visual presentation of the cell
        rbt = self.robot
        itm = self.item
        return "[%s,%s]"%(itm,rbt)


#########################################################################################################################
# 4. Warehouse
#########################################################################################################################
# The main class of this program.
# A warehouse contains 9X15 cells.


class Warehouse:
    
    #########################################################################################################################
    ############### WAREHOUSE INTIALIZATION
    #########################################################################################################################
    
    def __init__(self, warehouse_filename, items_to_exit_filename):
        
        self.distances_left = []               # initiate list of distances of items from the left of the I/O
        self.distances_right = []              # initiate list of distances of items from the right of the I/O
        self.robot_side = {}                   # A dictionary with pairs of (robot_id: side)
        self.robot_positions = None            # A list of the robot positions. Will be updated every time unit
        self.items_to_exit_positions = None    # The items that are needed to be exited positions. Will be updated every time unit
        self.robots_moves = {1: [], 2: [], 3: [], 4: [], 5:[]} # history of the robot movements with pairs of (robot_id: moves)
        self.exited_items = {}                 # A dictionary with pairs of (item number to exit: Time of exit) 

        self.robot_final_positions_left = [(7,0),(3,0),(0,4)]      # final locations for the robots on the left side of the warehouse
        self.robot_final_positions_right = [(8,14),(0,14),(0,14)]  # final locations for the robots on the right side of the warehouse
        
        ############################
        # Reading the pickle files
        ############################

        # Warehouse
        with open(warehouse_filename,'rb') as infile:
            initiated_warehouse = p.load(infile) 
        
        # Items to exit
        with open(items_to_exit_filename,'rb') as infile:
            items_to_exit = p.load(infile)
            # Dictionary of items to exit with their occupation status - the key is the item number, the value is the robot id
            self.items_to_exit = {items_to_exit[i]: False for i in range(len(items_to_exit))}
        
        rows, columns = len(initiated_warehouse), len(initiated_warehouse[0]) # rows and columns of the warehouse
        
        # Initiate an array and a counter of robots
        self.warehouse = pd.DataFrame(np.zeros((rows,columns))) # initiate an array
        robot_id=1 # initiate a count of robots' id
        
        robot_side = [1,2,1,2,1] # The distribution of the robots
        k = 0                    # initiate a counter for determining the robot side allocation
        
        ###################################
        # Filling the warehouse with cells
        ###################################
        for i in range(self.warehouse.shape[0]): # filling the warehouse with cells
            for j in range(self.warehouse.shape[1]):
                number = initiated_warehouse[i][j]
                if number == 0: # in case this is an escort, create a cell with escort + robot in relation to his intended side
                    side = robot_side[k]
                    self.warehouse.iloc[i,j] = Cell(robot_id=robot_id, side=side)
                    self.robot_side[robot_id] = side # save the belonging of the robot to the relevant side of the warehouse
                    robot_id+=1
                    k+=1
                else:
                    to_exit = number in items_to_exit # TRUE if the item needs to be exited; FALSE otherwise
                    if j<7:
                        side=1 # item is located on the left of the warehouse
                    elif j>7:
                        side=2 # item is located on the right of the warehouse
                    else:
                        side=3 # item is located exactly in the middle of the warehouse
                    self.warehouse.iloc[i,j] = Cell(item_number=number,exit=to_exit,side=side) # Create the cell with the item
            
        self.calculate_positions()                # Calculate all robots & items to exit positions in the warehouse
        self.calculate_distance_from_IO()         # calculate distance of the items from the I/O point
        
    
    #########################################################################################################################
    ############### ASSIGNMENTS FUNCTIONS
    #########################################################################################################################
    
    ################################
    # 1. Define the path of a robot
    ################################
    def define_robot_path(self, robot_id, steps, overwrite=True):
        #### Assign planned path (of steps) to a specific robot. 
        #### If overwrite=true, overwrite the path (steps) list of the robot with the received steps.
        
        robot_loc = self.robot_positions[robot_id-1][0] # retrieve current robot's position

        if overwrite: # should we delete the current robot's route with a new one?
            self.warehouse.iloc[robot_loc].robot.path = steps
            
        else: # add the planned path to the current robot's planned steps
            self.warehouse.iloc[robot_loc].robot.path.insert(0,steps) # inserting the steps like in a stack
    

    #########################################
    # 2. Exiting an item from the warehouse
    #########################################
    def exit_item(self, robot_id, current_time):
        #### When the item has arrived to the I/O point, remove the item from the list of items to exit,
        #### assign item "999" to the relevant cell and add the item along with the robot_id who took it to the list of exited items.
        
        if robot_id: # if it was exited by a robot
            robot_loc = self.robot_positions[robot_id-1][0] # retrieve current robot's position
            #self.warehouse.iloc[robot_loc].robot.currently_taking = None
        
        item_number = self.warehouse.iloc[(0,7)].item.number
        self.exited_items[item_number] = current_time+1 # it takes another time unit to exit the item
        del self.items_to_exit[item_number]
        self.warehouse.iloc[(0,7)].assignItem(Item(999))
        print("Items remaining: %s, current time: %s"%(len(self.items_to_exit),current_time))
        

    #########################################################################################################################
    ############### POSITIONS AND LOCATIONS
    #########################################################################################################################
    
    #################################################################################
    # 1. Calculate the positions of the robots and the items that needs to be exited
    #################################################################################
    def calculate_positions(self):
        #### robots positions
        #####################
        criterion = [self.warehouse.T[i].map(lambda x: x.robot != '') for i in range(self.warehouse.shape[0])]
        positions = [(i,j) for i,j in np.argwhere(criterion)]   # retrieve the positions in which we have robots there
        # retrieve robot positions with their ID:
        current_robot_positions = [(positions[i],
                                    self.warehouse.iloc[positions[i]].robot.id) for i in range(len(positions))]
        current_robot_positions = sorted(current_robot_positions,
                                         key=lambda x: x[1])    # Sort the list in order to preserve the robots order: 1-5
        self.robot_positions = current_robot_positions          # each object is with the format: ((x,y),robot_id)
        
        #### items to exit positions
        ############################
        criterion = [self.warehouse.T[i].map(lambda x: x.item != 0 and x.item.exit)
                     for i in range(self.warehouse.shape[0])]
        
        positions = [(i,j) for i,j in np.argwhere(criterion)]   # retrieve the positions of the items to exit
        
        self.items_to_exit_positions = positions                # each object is with the format: (x,y)
        
    #################################################################################
    # 2. Distance from the IO calculator
    #################################################################################
    def calculate_distance_from_IO(self):
        # abs distance calculation: {(x,y) - (0,7)} where x,y is the position of the item, (0,7) the position of the I/O
        # the warehouse is splitted to two parts: column <=7 and >7
        
        self.distances_left,self.distances_right = [],[]
        
        for item in self.items_to_exit: # for items that we need to exit
            if not self.items_to_exit[item] and item!=None: # TRUE means that the item needs to be exited
                position = self.find_item_location(item)
                distance = position[0]+abs(position[1]-7)
                item_number = self.warehouse.iloc[position].item.number
                if position[1] > 7:
                    self.distances_right.append((item_number,distance)) # pairs of: (item number,distance from I/O)
                else:
                    self.distances_left.append((item_number,distance)) # pairs of: (item number,distance from I/O)
        
        # sort items by minimum to maximum distance
        self.distances_left = sorted(self.distances_left, key=lambda x: x[1]) # sorted by distances
        self.distances_right = sorted(self.distances_right, key=lambda x: x[1]) # sorted by distances
    
    #########################################################################################################################
    ############### SEARCH & DISTANCE CALCULATIONS
    #########################################################################################################################
    
    #################################################################################
    # 1. Find item location
    #################################################################################
    def find_item_location(self, item_number):
        # retrieve item_number position with the format (x,y)
        criterion = [self.warehouse.T[i].map(lambda x: x.item != 0 and x.item.number==item_number)
                     for i in range(self.warehouse.shape[0])]
        positions = [(i,j) for i,j in np.argwhere(criterion)] # retrieve item location
        return positions[0] # return the location
          
    #########################################################################################################################
    ############### MANHATTAN JOURNEY PLANNER
    ######################################################################################################################### 
    
    def manhattan_journey_to_item(self, robot_id, item, overwrite=True, final=False, final_loc=0):
        # calculate the path towards a location ((x,y) format)
        
        steps = []
        
        ### Locations
        current_loc = self.robot_positions[robot_id-1][0]   # retrieve current robot's position
        robot_loc = current_loc
        target_loc = self.find_item_location(item)          # The location of the item
        
        ### Make sure we are with the escort
        escort_loc = self.return_to_escort(current_loc,robot_id) # FALSE if the robot is with the escort
        if escort_loc: # Have we received the location of the robot's escort?
            steps.extend([(current_loc,escort_loc,False)])  # add one step to the escort
            current_loc = escort_loc                        # Now the robot's location is the same as the escort's
        
        ## Scenarios:
        ### 1. The target item's location is on the same row as the robot's
        ### 2. The target item's location is on the same column as the robot's 
        
        if target_loc[0] == current_loc[0] or target_loc[0]<=1: # target is in the same row: apply columns steps first, then rows
            decision = True
        elif target_loc[1] == current_loc[1]:                   # target is in the same column: apply rows first, then columns
            decision = False
        else:                                                   # Otherwise, choose randomly
            decision = random.choice([True, False])
            
        if final:                                               # is this the last route for the robot?
            decision = random.choice([True, False])             # Choose randomly how to get over there
            current_loc = final_loc                             

        if decision:                                            # According to the decided way
            if target_loc[0] == 0:                              # In case the target location is in row 0,
                if 0 < target_loc[1] < 14:                      # Arrive one column left to the item, if possible
                    target_loc = (target_loc[0],target_loc[1]-1)
                elif target_loc[1] == 0:
                    target_loc = (target_loc[0],1)
                elif target_loc[1] == 14:
                    target_loc = (target_loc[0],13)
                    
            columns_steps = self.columns_steps(current_loc, target_loc[1])    # columns steps
            middle_loc = (current_loc[0],target_loc[1])                       # we have arrived to the turn location
            rows_steps = self.rows_steps(middle_loc,target_loc[0])            # now apply rows steps
            
            steps.extend(columns_steps)
            steps.extend(rows_steps)

        else: 
            if target_loc[0] > 1:
                target_loc = (target_loc[0]-1,target_loc[1]) # one row beneath the item
                
            rows_steps = self.rows_steps(current_loc,target_loc[0])           # rows steps
            middle_loc = (target_loc[0],current_loc[1])                       # we have arrived to the turn location
            columns_steps = self.columns_steps(middle_loc, target_loc[1])     # columns steps
            
            steps.extend(rows_steps)
            steps.extend(columns_steps)
        
        if steps:                                                   # do we have planned steps?
            if overwrite:
                self.define_robot_path(robot_id, steps, overwrite)  # assign the relevant final planned steps and overwrite the exist path
            else: # in case we want to add steps to the current robot's path
                for step in reversed(steps): # adding the manhattan step like adding elements to a stack
                    self.define_robot_path(robot_id, step, overwrite)
        
        else:                           # we haven't planned any steps
            self.three_step(robot_id)   # we are ready to start 3 step
            return True
            
            
        if not final:                   # if it's not the final route of the robot
            self.warehouse.iloc[robot_loc].robot.item_to_take = item # assign the intended item to take
        
    #########################################################################################################################
    ############### MOVEMENTS IN THE WAREHOUSE
    #########################################################################################################################
    
    ################################
    # 1. Movement in rows
    ################################

    def rows_steps(self, current_loc, target):
        first_movement, visited, steps = True, False, []

        if target-current_loc[0] > 0: # walking from down to up
            for x in range(current_loc[0],target,1):
                visited=True
                if first_movement:
                    step1 = [((x,current_loc[1]), (x+1,current_loc[1]), False)]
                    step2 = [((x+1,current_loc[1]), (x,current_loc[1]), True)]
                    steps.extend(step1+step2)
                    first_movement=False
                else:
                    step1 = [((x-1,current_loc[1]), (x,current_loc[1]), False)]
                    step2 = [((x,current_loc[1]), (x+1,current_loc[1]), False)]
                    step3 = [((x+1,current_loc[1]), (x,current_loc[1]), True)]
                    steps.extend(step1+step2+step3)
            # last move to the escort, but we make sure that we have done earlier steps
            if visited:
                steps.extend([((target-1,current_loc[1]), (target,current_loc[1]), False)])
        else: # walking from up to down
            for x in range(current_loc[0],target,-1):
                visited=True
                if first_movement:
                    step1 = [((x,current_loc[1]), (x-1,current_loc[1]), False)]
                    step2 = [((x-1,current_loc[1]), (x,current_loc[1]), True)]
                    steps.extend(step1+step2)
                    first_movement=False
                else:
                    step1 = [((x+1,current_loc[1]), (x,current_loc[1]), False)]
                    step2 = [((x,current_loc[1]), (x-1,current_loc[1]), False)]
                    step3 = [((x-1,current_loc[1]), (x,current_loc[1]), True)]
                    steps.extend(step1+step2+step3)
            # last move to the escort, but we make sure that we have done earlier steps
            if visited:
                steps.extend([((target+1,current_loc[1]), (target,current_loc[1]), False)])

        return steps


    ################################
    # 2. Movement in columns
    ################################

    def columns_steps(self, current_loc, y_target):
        first_movement, visited, steps = True, False, []
        
        if y_target-current_loc[1] > 0: # walking from left to right
            for y in range(current_loc[1],y_target,1):
                visited=True
                if first_movement:
                    step1 = [((current_loc[0],y), (current_loc[0],y+1), False)]
                    step2 = [((current_loc[0],y+1), (current_loc[0],y), True)]
                    steps.extend(step1+step2)
                    first_movement=False
                else:
                    step1 = [((current_loc[0],y-1), (current_loc[0],y), False)]
                    step2 = [((current_loc[0],y), (current_loc[0],y+1), False)]
                    step3 = [((current_loc[0],y+1), (current_loc[0],y), True)]
                    steps.extend(step1+step2+step3)
            # last move to the escort, but we make sure that we have done earlier steps
            if visited:
                steps.extend([((current_loc[0],y_target-1), (current_loc[0],y_target), False)])
        else: # walking from right to left
            for y in range(current_loc[1],y_target,-1):
                visited=True
                if first_movement:
                    step1 = [((current_loc[0],y), (current_loc[0],y-1), False)]
                    step2 = [((current_loc[0],y-1), (current_loc[0],y), True)]
                    steps.extend(step1+step2)
                    first_movement=False
                else:
                    step1 = [((current_loc[0],y+1), (current_loc[0],y), False)]
                    step2 = [((current_loc[0],y), (current_loc[0],y-1), False)]
                    step3 = [((current_loc[0],y-1), (current_loc[0],y), True)]
                    steps.extend(step1+step2+step3)
            # last move to the escort, but we make sure that we have done earlier steps
            if visited:
                steps.extend([((current_loc[0],y_target+1), (current_loc[0],y_target), False)])

        return steps
    
    
    #########################################################################################################################
    ############### THREE STEP MOVEMENTS
    #########################################################################################################################

    ################################
    # 1. Horizontal movements
    ################################

    def three_step_horizontal(self,current_loc):
        # We assume here that the robot is with the escort
        steps=["check"]         # a checkmark for the beginning of this series of steps
        if current_loc[1] == 7: # if we are at the same column as the I/O point is, then no steps are needed.
            return steps
        else:
            direction = 1 if current_loc[1]>7 else -1 # defines on which side we are at (column-wise)
        
        steps.extend(self.columns_steps(current_loc,current_loc[1]-direction)) # one step left/right
        location_2 = (current_loc[0],current_loc[1]-direction)
        
        steps.extend(self.rows_steps(location_2,current_loc[0]-1)) # one step down
        location_3 = (current_loc[0]-1,current_loc[1]-direction)
        
        steps.extend(self.columns_steps(location_3,current_loc[1])) # one step to the item
        final_loc = steps[-1][1] # the location of the robot at the end

        return final_loc,steps
    
    ################################
    # 2. Vertical movements
    ################################

    def three_step_vertical(self,current_loc):
        # assuming the robot is with the escort
        steps=["check"]         # a checkmark for the beginning of this series of steps
        if current_loc[1] == 7: # if we are at the same column as the I/O point is, no steps are needed.
            return steps
        else:
            direction = 1 if current_loc[1]>7 else -1 # defines on which side we are at (column-wise)
        
        # locations during the steps:
        location_2 = (current_loc[0]-1,current_loc[1])
        location_3 = (current_loc[0]-1,current_loc[1]-direction)
        
        # apply steps:
        steps.extend(self.rows_steps(current_loc,current_loc[0]-1))             # one step down
        steps.extend(self.columns_steps(location_2,current_loc[1]-direction))   # one step left/right
        steps.extend(self.rows_steps(location_3,current_loc[0]))                # one step up

        final_loc = steps[-1][1] # the location of the robot at the end
        
        if final_loc[0] == 0: # we need to apply another final three step if we arrive the I/O
            steps.extend(self.rows_steps(final_loc,1))                                              # one step towards the item
            steps.extend(self.columns_steps((final_loc[0]+1,final_loc[1]),final_loc[1]-direction))  # one step left/right
            steps.extend(self.rows_steps((final_loc[0]+1,final_loc[1]-direction),0))                # one step down
            final_loc = (0,final_loc[1]-direction)

        return final_loc,steps
    
    #########################################################################################################################
    ############### MAIN THREE STEP JOURNEY PLANNER
    #########################################################################################################################
    
    def three_step(self,robot_id):
        # by a given current_loc, calculate the needed three steps until we reach either column 7 or row 1 (in relation to the relevant side of the warehouse)
        last_valid_loc = self.robot_positions[robot_id-1][0]
        steps = []
        item_above, item_below, item_right, item_left = False,False,False,False
        
        # Determine the items around the robot location, including the position of the robot
        items = [self.warehouse.iloc[(last_valid_loc)].item.number]
        if last_valid_loc[0] < 8: # item above
            item_above = True
            items.append(self.warehouse.iloc[(last_valid_loc[0]+1,last_valid_loc[1])].item.number)
        if last_valid_loc[0] > 0: # item below
            item_below = True
            items.append(self.warehouse.iloc[(last_valid_loc[0]-1,last_valid_loc[1])].item.number)
        if last_valid_loc[1] < 14: # item right
            item_right = True
            items.append(self.warehouse.iloc[(last_valid_loc[0],last_valid_loc[1]+1)].item.number)
        if last_valid_loc[1] > 0: # item left
            item_left = True
            items.append(self.warehouse.iloc[(last_valid_loc[0],last_valid_loc[1]-1)].item.number)

        
        # Does the item that the robot is currently taking was found in the items around him?
        if self.warehouse.iloc[last_valid_loc].robot.item_to_take not in items and self.warehouse.iloc[last_valid_loc].robot.currently_taking not in items:
            # If so, apply reroute to the item.
            self.reroute(robot_id)
            return False
        else:
            # Otherwise we can start the three steps - horizontal then vertical.
            first_time = True
            
            # Let's make sure that the robot is with the escort.
            escort_loc = self.return_to_escort(last_valid_loc,robot_id)
            if escort_loc: # if the robot is not with the escort,
                steps.extend([(last_valid_loc,escort_loc,False)]) # apply one step to the escort
                last_valid_loc = escort_loc                       # and save the current location.
            
            while last_valid_loc[1]!=7 and last_valid_loc[0]>0: # until we reach column 7 where the I/O point is, or until row is 1
                # one step towards the item if its the first movement
                if first_time and item_above: # make sure we can go to row 8
                    steps.append("check")
                    steps.extend(self.rows_steps(last_valid_loc,last_valid_loc[0]+1))
                    last_valid_loc = steps[-1][1] # update last valid location
                    first_time = False
                
                # Now apply three steps until we reach the relevant position
                new_loc, current_steps = self.three_step_horizontal(last_valid_loc)
                last_valid_loc = new_loc # update last valid location
                steps.extend(current_steps)
                if last_valid_loc[0]>0: # maybe we are finished here, and only one vertical movement is needed?
                    new_loc, current_steps = self.three_step_vertical(last_valid_loc)
                    last_valid_loc = new_loc # update last valid location
                    steps.extend(current_steps)
                    
        if steps: # Have we planned steps? if so, save them according to the relevant robot.
            self.define_robot_path(robot_id,steps)

        else:     # If no 3 steps are needed but only 5 steps:
            # Now the robot is currently taking the item.
            item_to_take = self.warehouse.iloc[self.robot_positions[robot_id-1][0]].robot.item_to_take
            self.warehouse.iloc[self.robot_positions[robot_id-1][0]].robot.currently_taking = item_to_take
            self.warehouse.iloc[self.robot_positions[robot_id-1][0]].robot.item_to_take = None
            self.five_step(robot_id) # do the necessary 5 steps towards the IO
            return False
        return True

    #########################################################################################################################
    ############### FIVE STEP MOVEMENTS
    #########################################################################################################################
    
    ################################
    # 1. Horizontal movements
    ################################

    def five_step_horizontal(self,current_loc):
        # assuming that the item is closer to the I/O in comparison to the robot
        last_valid_loc = current_loc
        steps = ["check"]          # a checkmark for the beginning of this series of steps
        if current_loc[1] - 7 > 0: #we are at the right side of the I/O
            steps.extend(self.rows_steps(current_loc,current_loc[0]+1)) #step up, first step
            steps.extend(self.columns_steps((current_loc[0]+1,current_loc[1]),current_loc[1]-2)) #two steps left
            steps.extend(self.rows_steps((current_loc[0]+1,current_loc[1]-2),current_loc[0])) #step down
            steps.extend(self.columns_steps((current_loc[0],current_loc[1]-2),current_loc[1]-1))#step to the item
        elif current_loc[1] - 7 < 0: #we are on the left side of the I/O
            steps.extend(self.rows_steps(current_loc,current_loc[0]+1)) #step up, first step
            steps.extend(self.columns_steps((current_loc[0]+1,current_loc[1]),current_loc[1]+2)) #two steps right
            steps.extend(self.rows_steps((current_loc[0]+1,current_loc[1]+2),current_loc[0])) #step down
            steps.extend(self.columns_steps((current_loc[0],current_loc[1]+2),current_loc[1]+1))#step to the item
        
        if steps: # any steps were created?
            final_loc = steps[-1][1] # the location of the robot at the end of the steps
        else: # no steps were created
            final_loc = current_loc
            
        return final_loc,steps
    
    ################################
    # 2. Vertical movements
    ################################
    
    def five_step_vertical(self,current_loc,side):
        # assuming that the item is closer to the I/O in comparison to the robot
        last_valid_loc = current_loc
        steps = ["check"]         # a checkmark for the beginning of this series of steps
        
        if current_loc[0] > 1:#we are above the I/O on column 7
            if side == 1: # we are on the left side of the warehouse
                steps.extend(self.columns_steps(current_loc,current_loc[1]-1)) #step aside,, first step
                steps.extend(self.rows_steps((current_loc[0],current_loc[1]-1),current_loc[0]-2))#two steps down
                steps.extend(self.columns_steps((current_loc[0]-2,current_loc[1]-1),current_loc[1]))#back to the right wall
                steps.extend(self.rows_steps((current_loc[0]-2,current_loc[1]),current_loc[0]-1))#step to the item
            
            elif side == 2 or side == 3: # we are on the right side of the warehouse
                steps.extend(self.columns_steps(current_loc,current_loc[1]+1))#step aside, first step
                steps.extend(self.rows_steps((current_loc[0],current_loc[1]+1),current_loc[0]-2))#two steps down
                steps.extend(self.columns_steps((current_loc[0]-2,current_loc[1]+1),current_loc[1]))#back to left wall
                steps.extend(self.rows_steps((current_loc[0]-2,current_loc[1]),current_loc[0]-1))#step to the item
                
        if steps:
            final_loc = steps[-1][1] # the location of the robot at the end of the steps
        else: # no steps were created
            final_loc = current_loc
            
        return final_loc,steps
    
    #########################################################################################################################
    ############### FIVE STEP JOURNEY PLANNER
    #########################################################################################################################
    
    def five_step(self,robot_id):
        # By a given robot id, this function calculates the needed path towards the I/O point.
        last_valid_loc = self.robot_positions[robot_id-1][0]
        
        steps = []
        
        # Determine the information about the item
        currently_taking = self.warehouse.iloc[last_valid_loc].robot.currently_taking
        side = self.warehouse.iloc[self.find_item_location(currently_taking)].item.side
        
        ## Let's check if we are already at row 0 and column 7:
        if last_valid_loc == (0,7): # are we in the IO?
            loc = self.around_IO() # find if there are items around the IO that can be exited
            if loc: # Is there an item to exit around the IO point?
                # Apply the relevant step towards the item.
                if loc == (0,6): # one step left
                    steps.extend(self.columns_steps((0,7),6))
                elif loc == (0,8): # one step right
                    steps.extend(self.columns_steps((0,7),8))
                elif loc == (1,7): # one step down
                    steps.extend(self.rows_steps((1,7),0))
                self.warehouse.iloc[last_valid_loc].robot.path = steps

                # Maybe the item is allocated to another robot - let's reset the other robot plans.
                item = self.warehouse.iloc[loc].item.number
                self.warehouse.iloc[last_valid_loc].robot.currently_taking = item
                if self.items_to_exit[item]:                    # the other robot takes the item
                    other_robot = self.items_to_exit[item]      # retrieve the robot_id who should have taken the item
                    other_robot_loc = self.robot_positions[other_robot-1][0]
                    self.items_to_exit[item] = robot_id
                    self.new_route(other_robot)                 # redefine the route of the other robot
                else: # no robot takes the item
                    self.items_to_exit[item] = robot_id
                
                    
                return False

        #### Possible cases:
        if last_valid_loc[1] == 7: # case 1: the robot is in column 7 (the same column as the I/O)
            # Here we do vertical five steps until we reach the I/O point.
            item_above = self.warehouse.iloc[(last_valid_loc[0]+1,last_valid_loc[1])].item.number 
            item_below = self.warehouse.iloc[(last_valid_loc[0]-1,last_valid_loc[1])].item.number
            if item_above != currently_taking and item_below != currently_taking:
                self.reroute(robot_id)
                return False
            
            
            # At first, apply only one step towards the item, if the item is above the robot
            if item_above == currently_taking:
                steps.append("check")
                side = self.warehouse.iloc[(last_valid_loc[0]+1,last_valid_loc[1])].item.side
                steps.extend(self.rows_steps(last_valid_loc,last_valid_loc[0]+1))
                last_valid_loc = steps[-1][1] # update last valid location
            else: # item below
                side = self.warehouse.iloc[(last_valid_loc[0]-1,last_valid_loc[1])].item.side
            
            # all is set; now start the needed vertical five steps.
        
            while int(last_valid_loc[0])>1: # until the robot is only 1 row above the I/O
                last_valid_loc, current_steps = self.five_step_vertical(last_valid_loc, side) # movements according to the item's side!
                steps.extend(current_steps)
                
        
        elif last_valid_loc[0]<=1: # case 2: the robot is in row 1 or 0 (one row above the IO)
            item_left = self.warehouse.iloc[(last_valid_loc[0],last_valid_loc[1]-1)].item.number
            item_right = self.warehouse.iloc[(last_valid_loc[0],last_valid_loc[1]+1)].item.number
            currently_taking = self.warehouse.iloc[last_valid_loc].robot.currently_taking

            if last_valid_loc[1]>7 and item_right == currently_taking: # one step right is needed towards the item
                steps.extend(self.columns_steps(last_valid_loc,last_valid_loc[1]+1))
                last_valid_loc = steps[-1][1] # update last valid location

            elif last_valid_loc[1]<7 and item_left == currently_taking: # one step left is needed towards the item
                steps.extend(self.columns_steps(last_valid_loc,last_valid_loc[1]-1))
                last_valid_loc = steps[-1][1] # update last valid location



            elif item_left != currently_taking and item_right != currently_taking: # there is a problem, the robot missed the item.
                self.reroute(robot_id)
                return False
                    
            # all is set; start the horizontal five steps.
            while last_valid_loc[1]<6 or last_valid_loc[1]>8: # until the robot is only 1 row above the I/O
                new_loc, current_steps = self.five_step_horizontal(last_valid_loc) # movements according to the item's side!
                last_valid_loc = new_loc
                steps.extend(current_steps)
            
            #now, at the end, we need one vertical five-step to (0,7) if the robot is two rows above the I/O
            if last_valid_loc == (2,7):
                side = self.warehouse.iloc[(2,7)].item.side
                steps.extend(self.rows_steps(last_valid_loc,last_valid_loc[0]+1)) # one step above
                last_valid_loc, current_steps = self.five_step_vertical(last_valid_loc, side) # movements according to the item's side!
                steps.extend(current_steps)
        
        # define the planned steps
        self.define_robot_path(robot_id,steps)
        
    
    #########################################################################################################################
    ############### TO THE NEXT ITEM JOURNEY PLANNER
    #########################################################################################################################
    
    def to_next_item(self,robot_id,item_number):
        # If the robot has turned over the item to the I/O point & is in the location: (1,7) (0,6) or (0,8),
        # plan his next steps to the next item.
        item_location = self.find_item_location(item_number) # retrieve the item that the robot is going to take
        robot_loc = self.robot_positions[robot_id-1][0]      # retrieve current robot's position
        side = 1 if item_location[1] <= 7 else 2             # determine the item's side
        
        steps = []
        if self.warehouse.iloc[robot_loc].item.number != 0:        # if the robot is not with the escort,
            escort_loc = self.return_to_escort(robot_loc,robot_id) # find the escort
            steps.extend([(robot_loc,escort_loc,False)])           # and save the needed step towards it
            old_robot_loc = robot_loc
            robot_loc = escort_loc
        else:
            old_robot_loc = robot_loc
            

        if robot_loc[0]>0: # Going back from the escort
            steps.extend(self.rows_steps(robot_loc,0)) #robot goes to row 0 so it can start his journey to the next item
        
        row_below_item = 0 if item_location[0] == 0 else item_location[0]-1 # the target is one row below the item
        
        p = 1 if self.robot_side[robot_id]==1 else -1                       # determine the robot side
        
        if item_location[1] == 0 or item_location[1] == 14:
            item_location = (item_location[0],item_location[1]+p)
        
        if side == 1: # next item is at the left side of the warehouse
            steps.extend(self.columns_steps((0,robot_loc[1]),0))              # go to the left wall of the warehouse: (0,0)
            steps.extend(self.rows_steps((0,0),row_below_item))                    # go to one row below the item (if possible)
            steps.extend(self.columns_steps((row_below_item,0),item_location[1]))  # go to the item's column
            
        else: # next item is at the right side of the warehouse
            steps.extend(self.columns_steps((0,robot_loc[1]),14))             # go to the right wall of the warehouse: (0,14)
            steps.extend(self.rows_steps((0,14),row_below_item))                   # go to one row below the item (if possible)
            steps.extend(self.columns_steps((row_below_item,14),item_location[1])) # go to the item's column
        
        # Save the information about the robot
        self.warehouse.iloc[old_robot_loc].robot.item_to_take = item_number
        self.warehouse.iloc[old_robot_loc].robot.currently_taking = None
        self.items_to_exit[item_number] = robot_id # now this robot is assigned to this item
        self.define_robot_path(robot_id,steps)     # define the needed steps
    
    #########################################################################################################################
    ############### APPLYING ROBOT STEPS
    #########################################################################################################################
    
    ######################################
    # 1. New route - to a different item
    ######################################

    def new_route(self, robot_id):
        # in case we want to set a new route for a specific robot towards a *different* item than what it takes now
        if self.items_to_exit: # are there still items to exit?
            if self.robot_side[robot_id] == 1: # according to the robot's side,
                if len(self.distances_left) > 0:
                    next_item = random.choice(self.distances_left)[0] # randomly choose an item
                else:
                    return False # no items left

            else:
                if len(self.distances_right) > 0:
                    next_item = random.choice(self.distances_right)[0] # randomly choose an item
                else:
                    return False # no items left

            robot_loc = self.robot_positions[robot_id-1][0]

            # reset the information for the items to exit dictionary; the robot is going to take another item.
            if self.warehouse.iloc[robot_loc].robot.item_to_take:
                self.items_to_exit[self.warehouse.iloc[robot_loc].robot.item_to_take] = False
            elif self.warehouse.iloc[robot_loc].robot.currently_taking:
                self.items_to_exit[self.warehouse.iloc[robot_loc].robot.currently_taking] = False
            
            self.manhattan_journey_to_item(robot_id,next_item) # calculate the journey to the item
            # if the robot is exactly in the place to start 3 or 5 steps:
            if self.warehouse.iloc[robot_loc].robot.path[0] == 'check':
                # the robot doesn't need to go to the item; so it can start directly to take it to the IO
                self.warehouse.iloc[robot_loc].robot.item_to_take = None
                self.warehouse.iloc[robot_loc].robot.currently_taking = next_item 
            else: # the robot will attend the item
                self.warehouse.iloc[robot_loc].robot.item_to_take = next_item
                self.warehouse.iloc[robot_loc].robot.currently_taking = None
            self.items_to_exit[next_item] = robot_id  
            return True
        
        return False # no items left
    
    ######################################
    # 2. Escort in target check
    ######################################

    def escort_in_target(self, location, robot_id):
        # find if there is an escort in the robot's target location.
        if self.warehouse.iloc[location].item.number == 0 and self.warehouse.iloc[location].item.robot_id != robot_id: # Escort is indeed in target
            new_route = self.new_route(robot_id) # define a new route for the robot
            if new_route:
                return new_route # it's TRUE if we successfully planned the steps for the robot.
            else:
                return True
        else:
            return False

    ################################################
    # 3. Apply robot steps - plans vs. actual state
    ################################################

    def apply_robot_step(self, robot_id, fictitious=False):
        # apply the given step to a robot_id 
        robot_loc = self.robot_positions[robot_id-1][0]

        if fictitious: # if the applied step is fictitious
            self.robots_moves[robot_id].append((robot_loc, robot_loc, False)) # add a fictitious move

        else: 
            step = self.warehouse.iloc[robot_loc].robot.path[0] # receive the robot's step
            if step == "check": # if it's part of a 3 or 5 steps
                if not self.location_check(robot_id):
                    return False # stop here if the robot isn't located in the right place for 3/5 steps
                else:
                    del self.warehouse.iloc[robot_loc].robot.path[0] # delete the "check" so we can receive the planned step
                    
            current_loc, to_loc, with_item = self.warehouse.iloc[robot_loc].robot.path[0]
        
            current_cell, to_cell = self.warehouse.iloc[current_loc], self.warehouse.iloc[to_loc]
            
            if current_loc == to_loc: # in case origin location equals to destination location
                self.robots_moves[robot_id].append((current_loc, current_loc, False)) # apply fictitious move
                
            elif self.warehouse.iloc[to_loc].robot != '': # is there a robot in the destination?
                # Apply escape
                self.escape(robot_id,to_loc)
                
                ######!!!!!!!!!!!#########
                new_loc,next_new_loc,with_item = self.warehouse.iloc[current_loc].robot.path[0]
                ######!!!!!!!!!!!#########
                
                self.robots_moves[robot_id].append((new_loc, next_new_loc, False))
                return False
                
            elif self.escort_in_target(to_loc, robot_id): # is there an escort of another robot in target?
                # then we freeze at the location for 3 time units.
                for i in range(2):
                    self.define_robot_path(robot_id,(current_loc, current_loc, False),overwrite=False)
                self.robots_moves[robot_id].append((current_loc, current_loc, False)) # add a fictitious move
                return False
                
            else: # the destination is free from robot/escort
                self.warehouse.iloc[to_loc].assignRobot(current_cell.robot)         # assign the robot to the destination cell
                self.warehouse.iloc[current_loc].assignRobot('')                    # empty the current cell from the robot
                self.robots_moves[robot_id].append((with_item, current_loc, to_loc))
                if with_item: # robot is moving to the new location with the item
                    if self.warehouse.iloc[to_loc].item.number == 0: # if the destination is the escort of this current robot,
                        escort = self.warehouse.iloc[to_loc].item                   # save the escort
                        self.warehouse.iloc[to_loc].assignItem(current_cell.item)   # assign the item to the destination cell
                        self.warehouse.iloc[current_loc].assignItem(escort)         # now the current cell has an escort
                
            del self.warehouse.iloc[to_loc].robot.path[0] # delete the planned step for the robot that it is
                                                          # not at to_loc, so we can move to the next one.
            
            
    
    #########################################################################################################################
    ############### MAIN PROGRAM FUNCTIONS
    #########################################################################################################################

    ################################################
    # 1. Running first time
    ################################################

    def running_first_time(self):
        # We use this function only at the beginning of the program.
        for robot_id in range(1,6):                     # for each robot,
            i = 1 if robot_id%2==0 else -1              # determing its side
            if self.robot_side[robot_id] == 1:          # and according to the robot side
                item = self.distances_left[i*robot_id-1][0] # take the item
            else:
                item = self.distances_right[i*robot_id-1][0]
            # we take here 3 close items to the IO, and 2 far items.

            self.manhattan_journey_to_item(robot_id,item)
            self.items_to_exit[item] = robot_id        
    
    ################################################
    # 2. Can the robot proceed function
    ################################################

    def can_proceed(self, robot_id):
        # identify the robots in the area of 6X7 around the I/O, that are currently taking an item 
        # and find the robot with the minimum item distance towards the I/O that can proceed with it.
        area = [(i,j) for i in range(6) for j in range(4,11)]
        
        robot_locs = [location for location in area if self.warehouse.iloc[location].robot != '']
        candidates = []
        
        for location in robot_locs: # find pairs of (robot_id,distance)
            if self.warehouse.iloc[location].robot.currently_taking:   # is this an item that a robot is currently taking?
                candidate_id = self.warehouse.iloc[location].robot.id  # the robot is a candidate to proceed
                distance_left = location[0] + abs(location[1]-7)       # rows+(columns-7) is the distance from the IO
                candidates.append((candidate_id,distance_left))
        
        if not candidates:
            return True  # no robots around the I/O, proceed with current robot
        else:
            candidate = sorted(candidates, key=lambda x: x[1])[0][0]  # return the robot_id with minimum distance
            if candidate == robot_id:  # the candidate is this robot_id?
                return True
            else:
                return False
            
    ################################################
    # 3. Escape function - Collision handling
    ################################################
    
    def escape(self, robot_id, other_robot_next_loc):
        # Calculate an escape route to a robot, in accordance to the other robot next location,
        # in order to avoid collision between robots.
        robot_loc = self.robot_positions[robot_id-1][0]
        if robot_id == self.warehouse.iloc[other_robot_next_loc].robot.id: # if it's somehow the same robot, like in a fictitious step,
            return False # then abort.
        
        # define direction
        if robot_loc[0] == 0 or robot_loc[1] == 0:
            direction = 1
        elif robot_loc[0] == 8 or robot_loc[1] == 14:
            direction = -1
        else:
            direction = random.choice([1,-1])

        steps = []
        
        if robot_loc[1] - other_robot_next_loc[1] == 0: # on the same column, so move to another column
            temporary_location = (robot_loc[0],robot_loc[1]+direction)
            steps.extend(self.columns_steps(robot_loc,robot_loc[1]+direction)) # move one column
            steps.extend([(temporary_location, temporary_location, False) for i in range(3)]) # freeze for 3 time units
            steps.extend(self.columns_steps(temporary_location,robot_loc[1])) # return to column
        elif robot_loc[0] - other_robot_next_loc[0] == 0: # on the same row, so move by rows
            temporary_location = (robot_loc[0]+direction,robot_loc[1])
            steps.extend(self.rows_steps(robot_loc,robot_loc[0]+direction))
            steps.extend([(temporary_location, temporary_location, False) for i in range(3)]) # freeze for 3 time units
            steps.extend(self.rows_steps(temporary_location, robot_loc[0]))
        
        
        for step in reversed(steps): # define robot path inserts the steps like a stack
            self.define_robot_path(robot_id,step,overwrite=False)

        return True
    
    ################################################
    # 4. Escape function - Collision handling
    ################################################

    def reroute(self,robot_id):
        # when needed, this function will reset the robot's planned steps,
        # and will figure out the relevant route back to it.
        robot_loc = self.robot_positions[robot_id-1][0]
        currently_taking = self.warehouse.iloc[robot_loc].robot.currently_taking
        item_to_take = self.warehouse.iloc[robot_loc].robot.item_to_take
        
        if currently_taking: # is it an item that the robot is currently taking?
            self.manhattan_journey_to_item(robot_id,currently_taking)
            self.warehouse.iloc[robot_loc].robot.currently_taking = None
            self.warehouse.iloc[robot_loc].robot.item_to_take = currently_taking
        else: # is it a robot that is going to take the item?
            self.manhattan_journey_to_item(robot_id,item_to_take)
    
    ################################################
    # 5. Location check - Items around the robot
    ################################################

    def location_check(self,robot_id):
        # check if the robot is near the item for 3 step or 5 step
        location = self.robot_positions[robot_id-1][0]
        above = 8 if location[0] == 8 else location[0]+1
        below = 0 if location[0] == 0 else location[0]-1
        left = 0 if location[1] == 0 else location[1]-1
        right = 14 if location[1] == 14 else location[1]+1
        
        item_location = self.find_item_location(self.warehouse.iloc[location].robot.currently_taking)
        
        if item_location[0] in [above,below] or item_location[1] in [left,right]:
            return True
        else:
            self.reroute(robot_id)
            return False
        
    ################################################
    # 6. Escort search around the robot
    ################################################

    def return_to_escort(self, location, robot_id):
        above = (8,location[1]) if location[0] == 8 else (location[0]+1,location[1])
        below = (0,location[1]) if location[0] == 0 else (location[0]-1,location[1])
        left = (location[0],0) if location[1] == 0 else (location[0],location[1]-1)
        right = (location[0],14) if location[1] == 14 else (location[0],location[1]+1)
        
        for loc in [above,below,left,right]:
            if self.warehouse.iloc[loc].item.number == 0:
                if self.warehouse.iloc[loc].item.robot_id == robot_id: # does this escort belong to this robot?
                    return loc
        
        return False # the escort is with the robot
        
    ################################################
    # 7. Robot search around the robot
    ################################################

    def around_robot(self, robot_id):
        location = self.robot_positions[robot_id-1][0]
        above = (8,location[1]) if location[0] == 8 else (location[0]+1,location[1])
        below = (0,location[1]) if location[0] == 0 else (location[0]-1,location[1])
        left = (location[0],0) if location[1] == 0 else (location[0],location[1]-1)
        right = (location[0],14) if location[1] == 14 else (location[0],location[1]+1)
        
        robots_around = []
        
        for loc in [above,below,left,right]:
            if self.warehouse.iloc[loc].robot != '': # robot around the IO?
                return loc # return the location of the robot
        
        return False

    ################################################
    # 8. Items to exit around the IO
    ################################################

    def around_IO(self):
        # this function checks if there is an item to exit around the IO
        
        for loc in [(0,6),(0,8),(1,7)]:
            if loc in self.items_to_exit_positions:
                return loc
        
        return False

    ################################################
    # 9. Final route calculation for a robot that has finished its tasks
    ################################################
    
    def final(self,robot_id):
        
        robot_loc = self.robot_positions[robot_id-1][0]
        self.warehouse.iloc[robot_loc].robot.currently_taking = None
        self.warehouse.iloc[robot_loc].robot.item_to_take = None

        if self.warehouse.iloc[robot_loc].item.number != 0: # let's make sure the robot is with the escort
            escort_loc = self.return_to_escort(robot_loc,robot_id)
            step = (robot_loc,escort_loc,False)
            old_robot_loc = robot_loc
            robot_loc = escort_loc
        else:
            old_robot_loc = robot_loc

        
        if self.robot_side[robot_id] == 1:  # the robot is allocated to the left side of the warehouse
            loc = self.robot_final_positions_left[0]
            item = self.warehouse.iloc[loc].item.number
            self.manhattan_journey_to_item(robot_id,item,final=True,final_loc=robot_loc) # route to the location where the robot will rest
            del self.robot_final_positions_left[0] # allow the next planned location for the robot to rest
        else:                               # the robot is allocated to the right side of the warehouse
            loc = self.robot_final_positions_right[0]
            item = self.warehouse.iloc[loc].item.number
            self.manhattan_journey_to_item(robot_id,item,final=True,final_loc=robot_loc) # route to the location where the robot will rest
            del self.robot_final_positions_right[0] # allow the next planned location for the robot to rest
        
        return True
        

#########################################################################################################################
############### THE MAIN PROGRAM
#########################################################################################################################

def main_program(wh):
    time = 1
    beginning = True
    while wh.items_to_exit: # as long as we have items to exit
        
        #### RUNNING FIRST TIME ####
        if beginning: # initiating the program
            wh.running_first_time()
            beginning=False
            
        else:         # let's get the warehouse to work
            
            steps_to_apply = {1: False, 2: False, 3: False, 4: False, 5: False}
            
            ##############################################################
            ################## Check if an item to exit is in the I/O
            ##############################################################
            if wh.warehouse.iloc[(0,7)].item.number in wh.items_to_exit: # An item to exit is in the I/O?
                robot_id = wh.items_to_exit[wh.warehouse.iloc[(0,7)].item.number] # retrieve the robot id
                robot_loc = wh.robot_positions[robot_id-1][0]                     # retrieve the robot location
                wh.exit_item(robot_id,time)                                       # Exit the item
                if wh.items_to_exit and robot_id: # there are still items to exit
                    if wh.robot_side[robot_id] == 1: # left side of the warehouse
                        if len(wh.distances_left) > 0:
                            next_item = wh.distances_left[-1][0] # the chosen item - the farest
                            wh.to_next_item(robot_id,next_item)  # calculate the path to this item
                            wh.warehouse.iloc[robot_loc].robot.item_to_take = next_item
                            wh.warehouse.iloc[robot_loc].robot.currently_taking = None
                            wh.items_to_exit[next_item] = robot_id
                            steps_to_apply[robot_id] = True
                        else:
                            steps_to_apply[robot_id] = wh.final(robot_id)

                    else:
                        if len(wh.distances_right) > 0:  # right side of the warehouse
                            next_item = wh.distances_right[-1][0] # the chosen item - the farest
                            wh.to_next_item(robot_id,next_item)  # calculate the path to this item
                            wh.warehouse.iloc[robot_loc].robot.item_to_take = next_item
                            wh.warehouse.iloc[robot_loc].robot.currently_taking = None
                            wh.items_to_exit[next_item] = robot_id
                            steps_to_apply[robot_id] = True
                        else:
                            steps_to_apply[robot_id] = wh.final(robot_id)

            ##############################################################
            ################## Going over each robot in this time unit
            ##############################################################
            for robot_id in range(1,6): # let's go over each robot
                
                robot_loc = wh.robot_positions[robot_id-1][0]
                
                if wh.warehouse.iloc[robot_loc].robot.path: # the robot has some steps to do?
                    if wh.warehouse.iloc[robot_loc].robot.path[0] == "check": # is it a 3-step or a 5-step?
                        if wh.location_check(robot_id): # TRUE if the location is correct
                            del wh.warehouse.iloc[robot_loc].robot.path[0]
                        else:
                            continue # continue to the next robot if the robot isn't located in the right place for 3/5 steps
                            
                    step = wh.warehouse.iloc[robot_loc].robot.path[0] # retrieve the planned step of this robot
                    next_loc = step[1] # retrieve its next location
                    
                    if robot_loc == next_loc: # if the robot's location equal to the next location
                        # planned fictitious move
                        steps_to_apply[robot_id] = True
                        
                    elif wh.warehouse.iloc[next_loc].robot != '': # is there a robot in target?
                        # rescue from collision
                        if wh.warehouse.iloc[next_loc].robot.path: # the robot in destination has steps to do?
                            other_robot_next_loc = wh.warehouse.iloc[next_loc].robot.path[0][1]
                            if next_loc == other_robot_next_loc: # the target of that robot is the same as this robot?
                                wh.escape(robot_id,other_robot_next_loc) # apply escape
                                steps_to_apply[robot_id] = True
                            else:
                                # just freeze for 3 time units
                                for i in range(3):
                                    wh.define_robot_path(robot_id,(robot_loc, robot_loc, False),overwrite=False)
                     
                    else: # maybe there is an escort in target?
                        if wh.escort_in_target(next_loc, robot_id): # is there an escort in target?
                            belongs_to = wh.warehouse.iloc[next_loc].item.robot_id # find out the robot id that the escort belongs to
                        
                            if robot_id == belongs_to: # the escort belongs to the robot, safely proceed
                                steps_to_apply[robot_id] = True

                            else: # this is someone else's escort!
                                if not wh.warehouse.iloc[next_loc].robot == '': # we make sure that in the next location there isn't a robot
                                    other_robot_next_loc = wh.warehouse.iloc[next_loc].robot.path[0][1]
                                    wh.escape(robot_id,other_robot_next_loc) # apply escape
                                steps_to_apply[robot_id] = True
                                
                        else: # in case there is neither robot nor escort is in target
                            currently_taking = wh.warehouse.iloc[robot_loc].robot.currently_taking
                            if 0 <= next_loc[0] <= 3 and 5 <= next_loc[1] < 9 and currently_taking: # are we in the restricted zone?
                                # entering the 'restricted zone'
                                if wh.can_proceed(robot_id):
                                    steps_to_apply[robot_id] = True # robot can proceed
                                else: # robot cannot proceed
                                    loc = wh.around_robot(robot_id)
                                    if loc: # if there is another robot, escape!!!
                                        if wh.warehouse.iloc[loc].item.number == 0: # we make sure we do the escape when the robot is with the escort
                                            if wh.warehouse.iloc[robot_loc].robot.currently_taking: # rerouting the robot to the item
                                                item = wh.warehouse.iloc[robot_loc].robot.currently_taking
                                                wh.warehouse.iloc[robot_loc].robot.currently_taking = None
                                                wh.warehouse.iloc[robot_loc].robot.item_to_take = item
                                            else:
                                                item = wh.warehouse.iloc[robot_loc].robot.item_to_take
                                            
                                            if wh.manhattan_journey_to_item(robot_id,item): # maybe manhattan journey is not needed?
                                                if wh.warehouse.iloc[robot_loc].robot.item_to_take: # the robot is in item to take mode?
                                                    wh.warehouse.iloc[robot_loc].robot.currently_taking = wh.warehouse.iloc[robot_loc].robot.item_to_take
                                                    wh.warehouse.iloc[robot_loc].robot.item_to_take = None
                                            
                                            if type(wh.warehouse.iloc[robot_loc].robot.path[0][1]) != str:
                                                to_loc = wh.warehouse.iloc[robot_loc].robot.path[0][1]
                                                if wh.warehouse.iloc[to_loc].robot != '': # is there a robot in the new next planned location?
                                                    wh.escape(robot_id,loc)
                                        
                            else:
                                steps_to_apply[robot_id] = True
                                
                    
               
                else: # the robot doesn't have some steps to do?
                            
                    
                    if wh.warehouse.iloc[robot_loc].robot.item_to_take: # the robot finished the manhattan trip
                        # now we are at three step
                        if not wh.three_step(robot_id): # if we have failed to plan three-step movements
                            steps_to_apply[robot_id] = True
                            continue # The needed steps before three step are planned; continue to the next robot

                        item_number = wh.warehouse.iloc[robot_loc].robot.item_to_take
                        wh.warehouse.iloc[robot_loc].robot.robot_is_taking(item_number) # now the robot is currently taking the item
                        steps_to_apply[robot_id] = True

                    elif wh.warehouse.iloc[robot_loc].robot.currently_taking: # check if the item's attended the IO
                        # now we are at five step
                        wh.five_step(robot_id)
                        # apply the steps now
                        steps_to_apply[robot_id] = True
                        

            for robot_id in steps_to_apply:
                if steps_to_apply[robot_id]: # apply the step here 
                    wh.apply_robot_step(robot_id)
                else: # apply fictitious step here
                    wh.apply_robot_step(robot_id,fictitious=True)
            
            
            ## Update positions
            wh.calculate_positions()
            wh.calculate_distance_from_IO()
            
            ## To the next time unit
            time += 1
            
    
    print ("It took %s time units to exit all items."%(time))
    return wh


#########################################################################################################################
############### EXPORT TO PICKLE FILES
#########################################################################################################################

def run_and_export_to_pickle(wh):
    current = Warehouse(wh, 'items_list.p')
    example_number = wh[:3] # retrieves the "whX" name where X is the number of the warehouse set example
    current = main_program(current)
    
    ## Robot moves
    steps = []
    for i in range(1,6):
        steps.append(current.robots_moves[i])
        
    # write the pickle file
    with open('robots_moves_%s.p'%(example_number),'wb') as infile:
        p.dump(steps,infile) # save as robot_moves_(wh).p
    
    print("\n\n Robot moves were exported to pickle successfully")
    
    ## Extractions
    extractions = current.exited_items.items()
    extractions = sorted(extractions, key=lambda x: x[1])
    

    # write the pickle file
    with open('extractions_%s.p'%(example_number),'wb') as infile:
        p.dump(extractions,infile) # save as extractions_(wh).p
        
    print("\n\n Extractions were exported to pickle successfully")

#########################################################################################################################
############### EXPORT TO PICKLE FILES
#########################################################################################################################

warehouse_file = 'wh1.p'

run_and_export_to_pickle(warehouse_file)


