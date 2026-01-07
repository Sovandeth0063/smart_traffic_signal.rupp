import random
import time
import threading
import pygame
import sys
import os

# --- NEW: CONFIGURATION FOR PROJECT ---
# Set this to True to use YOLO data, False to use random generation
USE_YOLO_DATA = True 

# Default values of signal timers
defaultGreen = {0:10, 1:10, 2:10, 3:10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 2  # 2 phases
currentGreen = 0 
nextGreen = (currentGreen+1)%noOfSignals 
currentYellow = 0 

speeds = {'car':2.25, 'bus':1.8, 'truck':1.8, 'bike':3.5} 
scales = {'car':0.7, 'bus':1.0, 'truck':0.9, 'bike':0.5} 

# Coordinates
x = {'right':[0,0,0], 'down':[602,627,657], 'left':[1400,1400,1400], 'up':[755,727,697]}    
y = {'right':[498,466,436], 'down':[0,0,0], 'left':[348,370,398], 'up':[800,800,800]}

vehicles = {'right': {0:[], 1:[], 2:[], 'crossed':0}, 'down': {0:[], 1:[], 2:[], 'crossed':0}, 'left': {0:[], 1:[], 2:[], 'crossed':0}, 'up': {0:[], 1:[], 2:[], 'crossed':0}}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
stoppingGap = 25 
movingGap = 25 

allowedVehicleTypes = {'car': True, 'bus': True, 'truck': True, 'bike': True}
allowedVehicleTypesList = []
vehiclesTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
vehiclesNotTurned = {'right': {1:[], 2:[]}, 'down': {1:[], 2:[]}, 'left': {1:[], 2:[]}, 'up': {1:[], 2:[]}}
rotationAngle = 3
mid = {'right': {'x':705, 'y':445}, 'down': {'x':695, 'y':450}, 'left': {'x':695, 'y':425}, 'up': {'x':695, 'y':400}}

randomGreenSignalTimer = False # Disabled because we want Smart Timer
randomGreenSignalTimerRange = [10,20]

timeElapsed = 0
simulationTime = 300
timeElapsedCoods = (1100,50)
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]
manualSpawnEnabled = True
instructionsCoords = (20, 20)

pygame.init()
simulation = pygame.sprite.Group()

# --- NEW FUNCTION: READ YOLO DATA & CALCULATE TIME ---
def get_smart_timing():
    try:
        with open("traffic_data.txt", "r") as f:
            lines = f.readlines()
            cars = int(lines[0].strip())
            motos = int(lines[1].strip())
            trucks = int(lines[2].strip())
            tuktuks = int(lines[3].strip())
            
            # --- PCU FORMULA (Your Chapter 6 Logic) ---
            total_pcu = (cars * 1.0) + (motos * 0.3) + (trucks * 2.5) + (tuktuks * 0.7)
            
            # Convert to seconds (Base 1.8s * 0.6 Parallel Factor)
            calculated_time = total_pcu * 1.8 * 0.6
            
            # Cap limits
            final_time = int(max(15, min(90, calculated_time)))
            
            print(f"[SMART LOGIC] Loaded: {cars} Cars, {motos} Motos, {trucks} Trucks.")
            print(f"[SMART LOGIC] Calculated Green Time: {final_time} seconds (PCU: {total_pcu})")
            
            return final_time, {'car': cars, 'bike': motos, 'truck': trucks, 'bus': tuktuks}
            
    except Exception as e:
        print("[ERROR] Could not read traffic_data.txt. Using default.")
        print(e)
        return 20, {'car': 5, 'bike': 5, 'truck': 1, 'bus': 1} # Default fallback

# Get the smart data immediately
smart_green_time, vehicle_limits = get_smart_timing()

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        self.crossedIndex = 0
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        scale = scales[vehicleClass]
        width = int(self.originalImage.get_width() * scale)
        height = int(self.originalImage.get_height() * scale)
        self.originalImage = pygame.transform.scale(self.originalImage, (width, height))
        self.image = self.originalImage.copy()

        if(len(vehicles[direction][lane])>1 and vehicles[direction][lane][self.index-1].crossed==0):   
            if(direction=='right'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().width - stoppingGap         
            elif(direction=='left'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().width + stoppingGap
            elif(direction=='down'):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].image.get_rect().height - stoppingGap
            elif(direction=='up'):
                self.stop = vehicles[direction][lane][self.index-1].stop + vehicles[direction][lane][self.index-1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        if(direction=='right'):
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif(direction=='left'):
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif(direction=='down'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif(direction=='up'):
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        if(self.direction=='right'):
            if(self.crossed==0 and self.x+self.image.get_rect().width>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1): 
                    if(self.crossed==0 or self.x+self.image.get_rect().width<stopLines[self.direction]+40):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):               
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y+self.image.get_rect().height)<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):
                                self.y += self.speed
                elif(self.lane == 2): 
                    if(self.crossed==0 or self.x+self.image.get_rect().width<mid[self.direction]['x']):
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                 
                            self.x += self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 2.8
                            self.y -= 2.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):
                                self.y -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(vehicles[self.direction][self.lane][self.index-1].x - movingGap))):                
                        self.x += self.speed
                else:
                    if((self.crossedIndex==0) or (self.x+self.image.get_rect().width<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):                 
                        self.x += self.speed
        elif(self.direction=='down'):
            if(self.crossed==0 and self.y+self.image.get_rect().height>stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1): 
                    if(self.crossed==0 or self.y+self.image.get_rect().height<stopLines[self.direction]+50):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))): 
                                self.x -= self.speed
                elif(self.lane == 2): 
                    if(self.crossed==0 or self.y+self.image.get_rect().height<mid[self.direction]['y']):
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.y += self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x += 1.8
                            self.y += 2.4
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.x + self.image.get_rect().width) < (vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - movingGap))):
                                self.x += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(vehicles[self.direction][self.lane][self.index-1].y - movingGap))):                
                        self.y += self.speed
                else:
                    if((self.crossedIndex==0) or (self.y+self.image.get_rect().height<(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y - movingGap))):                
                        self.y += self.speed
        elif(self.direction=='left'):
            if(self.crossed==0 and self.x<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1): 
                    if(self.crossed==0 or self.x>stopLines[self.direction]-70):
                        if((self.x>=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else: 
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x -= 1.2
                            self.y -= 2.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.y>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height +  movingGap))):
                                self.y -= self.speed
                elif(self.lane == 2): 
                    if(self.crossed==0 or self.x>mid[self.direction]['x']):
                        if((self.x>=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):                
                            self.x -= self.speed
                    else:
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 1.8
                            self.y += 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or ((self.y + self.image.get_rect().height) <(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].y  -  movingGap))):
                                self.y += self.speed
            else: 
                if(self.crossed == 0):
                    if((self.x>=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x>(vehicles[self.direction][self.lane][self.index-1].x + vehicles[self.direction][self.lane][self.index-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.x>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):                
                        self.x -= self.speed
        elif(self.direction=='up'):
            if(self.crossed==0 and self.y<stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1
                if(self.willTurn==0):
                    vehiclesNotTurned[self.direction][self.lane].append(self)
                    self.crossedIndex = len(vehiclesNotTurned[self.direction][self.lane]) - 1
            if(self.willTurn==1):
                if(self.lane == 1): 
                    if(self.crossed==0 or self.y>stopLines[self.direction]-60):
                        if((self.y>=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)): 
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x<(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x - vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width - movingGap))):
                                self.x += self.speed
                elif(self.lane == 2): 
                    if(self.crossed==0 or self.y>mid[self.direction]['y']):
                        if((self.y>=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height +  movingGap) or vehicles[self.direction][self.lane][self.index-1].turned==1)):  
                            self.y -= self.speed
                    else:   
                        if(self.turned==0):
                            self.rotateAngle += rotationAngle
                            self.image = pygame.transform.rotate(self.originalImage, self.rotateAngle)
                            self.x -= 2.4
                            self.y -= 1.8
                            if(self.rotateAngle==90):
                                self.turned = 1
                                vehiclesTurned[self.direction][self.lane].append(self)
                                self.crossedIndex = len(vehiclesTurned[self.direction][self.lane]) - 1
                        else:
                            if(self.crossedIndex==0 or (self.x>(vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].x + vehiclesTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().width + movingGap))):
                                self.x -= self.speed
            else: 
                if(self.crossed == 0):
                    if((self.y>=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y>(vehicles[self.direction][self.lane][self.index-1].y + vehicles[self.direction][self.lane][self.index-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed 

def initialize():
    # --- UPDATED: USE SMART TIMING ---
    # Phase 0: X-axis (Right/Left) gets the Smart Time
    ts1 = TrafficSignal(0, defaultYellow, smart_green_time)
    signals.append(ts1)
    
    # Phase 1: Y-axis (Down/Up) gets default time (for comparison)
    ts2 = TrafficSignal(ts1.yellow+ts1.green, defaultYellow, defaultGreen[1])
    signals.append(ts2)
    
    repeat()

def printStatus():
    phaseNames = ["X-axis (Right/Left)", "Y-axis (Down/Up)"]
    for i in range(0, noOfSignals):
        if(signals[i] != None):
            if(i==currentGreen):
                if(currentYellow==0):
                    print(" GREEN", phaseNames[i], "-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
                else:
                    print("YELLOW", phaseNames[i], "-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
            else:
                print("   RED", phaseNames[i], "-> r:",signals[i].red," y:",signals[i].yellow," g:",signals[i].green)
    print()  

def repeat():
    global currentGreen, currentYellow, nextGreen
    phaseDirections = {0: ['right', 'left'], 1: ['down', 'up']}
    
    # --- [NEW] GAP TIMER INITIALIZATION ---
    empty_lane_counter = 0 
    
    # --- LOOP: While Green Timer is Running ---
    while(signals[currentGreen].green > 0):
        
        # ==============================================================================
        # [NEW] SMART GAP LOGIC (10 Second Rule)
        # ==============================================================================
        # 1. Identify which roads are currently moving
        if currentGreen == 0: 
            active_dirs = ['right', 'left'] # X-Axis
        else: 
            active_dirs = ['down', 'up']    # Y-Axis

        # 2. Count vehicles still on road
        vehicles_still_on_road = 0
        for direction in active_dirs:
            # Total Spawned - Total Crossed = Vehicles Currently on Road
            total_generated = len(vehicles[direction][0]) + len(vehicles[direction][1]) + len(vehicles[direction][2])
            total_crossed = vehicles[direction]['crossed']
            vehicles_still_on_road += (total_generated - total_crossed)

        # 3. The 10-Second Logic
        if vehicles_still_on_road == 0:
            empty_lane_counter += 1 # Count up: 1s, 2s, 3s...
            print(f"   [SENSOR] Road Empty for {empty_lane_counter}s...")
            
            # If empty for 10 seconds, force the switch
            if empty_lane_counter >= 10:
                print(f"   [GAP OUT] Empty > 10s. Cutting Green Light Early!")
                signals[currentGreen].green = 0 
        else:
            empty_lane_counter = 0 # Reset counter if a car is found
        # ==============================================================================

        printStatus()
        updateValues()
        time.sleep(1)
        
    currentYellow = 1 
    
    # Reset stops for vehicles
    for direction in phaseDirections[currentGreen]:
        for i in range(0,3):
            for vehicle in vehicles[direction][i]:
                vehicle.stop = defaultStop[direction]

    # --- LOOP: Yellow Timer ---
    while(signals[currentGreen].yellow > 0): 
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0 
    
    # --- Reset Timers for Next Cycle ---
    if currentGreen == 0: 
        signals[currentGreen].green = smart_green_time 
    else:
        signals[currentGreen].green = defaultGreen[currentGreen]
        
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed
       
    currentGreen = nextGreen 
    nextGreen = (currentGreen+1)%noOfSignals 
    signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green 
    repeat()

def updateValues():
    for i in range(0, noOfSignals):
        if(i==currentGreen):
            if(currentYellow==0):
                signals[i].green-=1
            else:
                signals[i].yellow-=1
        else:
            signals[i].red-=1

# --- UPDATED: SPAWN BASED ON YOLO COUNTS ---
def generateVehicles():
    # Use the limits from the text file
    spawned_counts = {'car': 0, 'bus': 0, 'truck': 0, 'bike': 0}
    
    while(True):
        vehicle_type_id = random.choice(allowedVehicleTypesList)
        vehicle_type_name = vehicleTypes[vehicle_type_id]
        
        # Check if we have already spawned enough of this type
        # (This makes the simulation match the YOLO numbers visually)
        if USE_YOLO_DATA:
            if spawned_counts[vehicle_type_name] >= vehicle_limits[vehicle_type_name]:
                time.sleep(0.5)
                continue # Skip if we hit the limit for this vehicle type
            
        spawned_counts[vehicle_type_name] += 1
        
        lane_number = random.randint(1,2)
        will_turn = 0
        if(lane_number == 1):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        elif(lane_number == 2):
            temp = random.randint(0,99)
            if(temp<40):
                will_turn = 1
        temp = random.randint(0,99)
        direction_number = 0
        dist = [25,50,75,100]
        if(temp<dist[0]):
            direction_number = 0
        elif(temp<dist[1]):
            direction_number = 1
        elif(temp<dist[2]):
            direction_number = 2
        elif(temp<dist[3]):
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type_id], direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(1)

def spawnVehicleManually(direction_number):
    direction = directionNumbers[direction_number]
    vehicle_type = random.choice(allowedVehicleTypesList)
    lane_number = random.randint(1, 2)
    will_turn = 0
    if lane_number == 1:
        temp = random.randint(0, 99)
        if temp < 40:
            will_turn = 1
    elif lane_number == 2:
        temp = random.randint(0, 99)
        if temp < 40:
            will_turn = 1
    
    Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, direction, will_turn)
    print(f"Vehicle spawned: {vehicleTypes[vehicle_type]} in {direction} lane {lane_number}")

def showStats():
    totalVehicles = 0
    print('Direction-wise Vehicle Counts')
    for i in range(0,4):
        if(signals[i]!=None):
            print('Direction',i+1,':',vehicles[directionNumbers[i]]['crossed'])
            totalVehicles += vehicles[directionNumbers[i]]['crossed']
    print('Total vehicles passed:',totalVehicles)
    print('Total time:',timeElapsed)

def simTime():
    global timeElapsed, simulationTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simulationTime):
            showStats()
            os._exit(1) 

class Main:
    global allowedVehicleTypesList
    i = 0
    for vehicleType in allowedVehicleTypes:
        if(allowedVehicleTypes[vehicleType]):
            allowedVehicleTypesList.append(i)
        i += 1
    thread1 = threading.Thread(name="initialization",target=initialize, args=()) 
    thread1.daemon = True
    thread1.start()

    black = (0, 0, 0)
    white = (255, 255, 255)

    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    background = pygame.image.load('images/intersection.png')

    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SMART TRAFFIC SIMULATION (YOLO INTEGRATED)")

    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    thread2 = threading.Thread(name="generateVehicles",target=generateVehicles, args=()) 
    thread2.daemon = True
    thread2.start()

    thread3 = threading.Thread(name="simTime",target=simTime, args=()) 
    thread3.daemon = True
    thread3.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showStats()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    spawnVehicleManually(0) 
                elif event.key == pygame.K_2:
                    spawnVehicleManually(1) 
                elif event.key == pygame.K_3:
                    spawnVehicleManually(2) 
                elif event.key == pygame.K_4:
                    spawnVehicleManually(3) 

        screen.blit(background,(0,0)) 
        signalToPhase = {0: 0, 1: 1, 2: 0, 3: 1} 
        for i in range(0, 4): 
            phase = signalToPhase[i]
            if(phase==currentGreen):
                if(currentYellow==1):
                    signalText = signals[phase].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signalText = signals[phase].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if(signals[phase].red<=10):
                    signalText = signals[phase].red
                else:
                    signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["","","",""]

        signalToPhase = {0: 0, 1: 1, 2: 0, 3: 1}
        for i in range(0, 4):  
            phase = signalToPhase[i]
            if(phase==currentGreen):
                if(currentYellow==1):
                    timerText = signals[phase].yellow
                else:
                    timerText = signals[phase].green
            else:
                if(signals[phase].red<=10):
                    timerText = signals[phase].red
                else:
                    timerText = "---"
            signalTexts[i] = font.render(str(timerText), True, white, black)
            screen.blit(signalTexts[i],signalTimerCoods[i])

        for i in range(0, 4):
            displayText = vehicles[directionNumbers[i]]['crossed']
            vehicleCountTexts[i] = font.render(str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i],vehicleCountCoods[i])

        timeElapsedText = font.render(("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText,timeElapsedCoods)

        if manualSpawnEnabled:
            instructionFont = pygame.font.Font(None, 20)
            instructions = [
                "Smart Traffic Mode Active",
                f"Calculated Time: {smart_green_time}s",
                "Press 1-4 to Spawn Manually"
            ]
            for i, instruction in enumerate(instructions):
                instructionText = instructionFont.render(instruction, True, white, black)
                screen.blit(instructionText, (instructionsCoords[0], instructionsCoords[1] + i * 20))

        for vehicle in simulation:  
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        pygame.display.update()

Main()