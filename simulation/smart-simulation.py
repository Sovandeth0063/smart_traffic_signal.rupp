import random
import time
import threading
import pygame
import sys
import os

# --- CONFIGURATION ---
USE_YOLO_DATA = True 

# Default values
defaultGreen = {0:10, 1:10, 2:10, 3:10}
defaultRed = 150
defaultYellow = 5

signals = []
noOfSignals = 2 
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

timeElapsed = 0
simulationTime = 300
timeElapsedCoods = (1100,50)
vehicleCountTexts = ["0", "0", "0", "0"]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]
manualSpawnEnabled = True
instructionsCoords = (20, 20)

pygame.init()
simulation = pygame.sprite.Group()

# --- FUNCTION: READ YOLO DATA ---
# REPLACE THIS FUNCTION IN YOUR SMART CODE
def get_smart_timing():
    try:
        with open("traffic_data.txt", "r") as f:
            lines = f.readlines()
            
            # Phase 0
            p0_cars = int(lines[0].strip())
            p0_motos = int(lines[1].strip())
            p0_trucks = int(lines[2].strip())
            p0_tuktuks = int(lines[3].strip())
            
            # Phase 1
            if len(lines) >= 8:
                p1_cars = int(lines[4].strip())
                p1_motos = int(lines[5].strip())
                p1_trucks = int(lines[6].strip())
                p1_tuktuks = int(lines[7].strip())
            else:
                p1_cars, p1_motos, p1_trucks, p1_tuktuks = 2, 2, 0, 0

            # Calculate Initial Green Time based on Phase 0 load
            total_pcu = (p0_cars * 1.0) + (p0_motos * 0.3) + (p0_trucks * 2.5) + (p0_tuktuks * 0.7)
            calculated_time = total_pcu * 1.8 * 0.6
            final_time = int(max(15, min(90, calculated_time)))
            
            print(f"[SMART LOGIC] Loaded Phase 0 & Phase 1 Data.")
            
            # CORRECTLY COMBINE LIMITS
            total_limits = {
                'car': p0_cars + p1_cars,
                'bike': p0_motos + p1_motos,
                'truck': p0_trucks + p1_trucks,
                'bus': p0_tuktuks + p1_tuktuks
            }
            
            return final_time, total_limits
            
    except Exception as e:
        print("[ERROR] Could not read traffic_data.txt. Using default.")
        return 20, {'car': 10, 'bike': 10, 'truck': 2, 'bus': 2}
    
smart_green_time, vehicle_limits = get_smart_timing()

# --- NEW FUNCTION: GENERATE PNG REPORT ---
def generate_final_report_image():
    print("Generating Final Report Image...")
    
    REPORT_BG = (240, 240, 240)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 150)
    GREY = (200, 200, 200)
    
    # Init fonts
    title_font = pygame.font.SysFont('Arial', 30, bold=True)
    header_font = pygame.font.SysFont('Arial', 22, bold=True)
    data_font = pygame.font.SysFont('Arial', 20)

    img_width, img_height = 600, 500
    report_surface = pygame.Surface((img_width, img_height))
    report_surface.fill(REPORT_BG)

    title_text = title_font.render("Final Traffic Simulation Report", True, BLUE)
    time_text = data_font.render(f"Total Duration: {timeElapsed} seconds", True, BLACK)
    report_surface.blit(title_text, (img_width//2 - title_text.get_width()//2, 30))
    report_surface.blit(time_text, (img_width//2 - time_text.get_width()//2, 70))

    start_x, start_y = 50, 130
    col_widths = [180, 150, 150]
    row_height = 50
    headers = ["Direction", "Total Spawned", "Total Crossed"]
    directions = ['right', 'down', 'left', 'up']

    for i, header in enumerate(headers):
        text = header_font.render(header, True, BLACK)
        report_surface.blit(text, (start_x + sum(col_widths[:i]), start_y))
    
    pygame.draw.line(report_surface, BLACK, (start_x, start_y + 35), (start_x + sum(col_widths), start_y + 35), 3)

    current_y = start_y + row_height
    grand_total_spawned = 0
    grand_total_crossed = 0

    for direction in directions:
        total_spawned = len(vehicles[direction][0]) + len(vehicles[direction][1]) + len(vehicles[direction][2])
        total_crossed = vehicles[direction]['crossed']
        grand_total_spawned += total_spawned
        grand_total_crossed += total_crossed

        row_data = [direction.upper(), str(total_spawned), str(total_crossed)]

        for i, data in enumerate(row_data):
            text = data_font.render(data, True, BLACK)
            report_surface.blit(text, (start_x + sum(col_widths[:i]) + 10, current_y))
        
        pygame.draw.line(report_surface, GREY, (start_x, current_y + 35), (start_x + sum(col_widths), current_y + 35), 1)
        current_y += row_height

    pygame.draw.line(report_surface, BLACK, (start_x, current_y), (start_x + sum(col_widths), current_y), 3)
    current_y += 10
    total_row_data = ["GRAND TOTAL", str(grand_total_spawned), str(grand_total_crossed)]
    for i, data in enumerate(total_row_data):
        text = header_font.render(data, True, BLUE) 
        report_surface.blit(text, (start_x + sum(col_widths[:i]) + 10, current_y))

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"traffic_report_{timestamp}.png"
    pygame.image.save(report_surface, filename)
    print(f"[SUCCESS] Report saved as: {filename}")


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

        # Stop Coordinate Logic
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
            
        # Set Initial Position
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
        # Retrieve the vehicle directly in front
        if self.index > 0:
            prev_vehicle = vehicles[self.direction][self.lane][self.index-1]
        else:
            prev_vehicle = None

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
                        # UPDATED GAP LOGIC: Check if prev vehicle is turning/crossed
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(prev_vehicle.x - movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):               
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
                        if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x+self.image.get_rect().width<(prev_vehicle.x - movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):                
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
                    if((self.x+self.image.get_rect().width<=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x+self.image.get_rect().width<(prev_vehicle.x - movingGap))):                
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
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(prev_vehicle.y - movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):                
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
                        if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.y+self.image.get_rect().height<(prev_vehicle.y - movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):                
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
                    if((self.y+self.image.get_rect().height<=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y+self.image.get_rect().height<(prev_vehicle.y - movingGap))):                
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
                        if((self.x>=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(prev_vehicle.x + prev_vehicle.image.get_rect().width + movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):                
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
                        if((self.x>=self.stop or (currentGreen==0 and currentYellow==0) or self.crossed==1) and (self.index==0 or self.x>(prev_vehicle.x + prev_vehicle.image.get_rect().width + movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):                
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
                    if((self.x>=self.stop or (currentGreen==0 and currentYellow==0)) and (self.index==0 or self.x>(prev_vehicle.x + prev_vehicle.image.get_rect().width + movingGap))):                
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
                        if((self.y>=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(prev_vehicle.y + prev_vehicle.image.get_rect().height +  movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))): 
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
                        if((self.y>=self.stop or (currentGreen==1 and currentYellow==0) or self.crossed == 1) and (self.index==0 or self.y>(prev_vehicle.y + prev_vehicle.image.get_rect().height +  movingGap) or prev_vehicle.turned==1 or (prev_vehicle.crossed==1 and prev_vehicle.willTurn==1))):  
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
                    if((self.y>=self.stop or (currentGreen==1 and currentYellow==0)) and (self.index==0 or self.y>(prev_vehicle.y + prev_vehicle.image.get_rect().height + movingGap))):                
                        self.y -= self.speed
                else:
                    if((self.crossedIndex==0) or (self.y>(vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].y + vehiclesNotTurned[self.direction][self.lane][self.crossedIndex-1].image.get_rect().height + movingGap))):                
                        self.y -= self.speed 

def initialize():
    ts1 = TrafficSignal(0, defaultYellow, smart_green_time)
    signals.append(ts1)
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

def calculate_dynamic_green_time(phase):
    if phase == 0:
        directions = ['right', 'left']
    else:
        directions = ['down', 'up']
        
    cars = 0
    bikes = 0
    trucks = 0
    buses = 0
    
    for direction in directions:
        for lane in range(3): 
            for vehicle in vehicles[direction][lane]:
                if vehicle.crossed == 0: 
                    v_type = vehicle.vehicleClass
                    if v_type == 'car': cars += 1
                    elif v_type == 'bike': bikes += 1
                    elif v_type == 'truck': trucks += 1
                    elif v_type == 'bus': buses += 1

    total_pcu = (cars * 1.0) + (bikes * 0.3) + (trucks * 2.5) + (buses * 0.7)
    calculated_time = int(total_pcu * 1.8 * 0.6)
    final_time = max(10, min(90, calculated_time))
    
    print(f"[REAL-TIME] Phase {phase} Queue: {cars} Cars, {bikes} Bikes. New Time: {final_time}s")
    return final_time

def repeat():
    global currentGreen, currentYellow, nextGreen
    phaseDirections = {0: ['right', 'left'], 1: ['down', 'up']}
    
    real_time_duration = calculate_dynamic_green_time(currentGreen)
    signals[currentGreen].green = real_time_duration
    
    empty_lane_counter = 0 
    
    while(signals[currentGreen].green > 0):
        if currentGreen == 0: 
            active_dirs = ['right', 'left']
        else: 
            active_dirs = ['down', 'up']

        vehicles_still_on_road = 0
        for direction in active_dirs:
            total_generated = len(vehicles[direction][0]) + len(vehicles[direction][1]) + len(vehicles[direction][2])
            total_crossed = vehicles[direction]['crossed']
            vehicles_still_on_road += (total_generated - total_crossed)

        if vehicles_still_on_road == 0:
            empty_lane_counter += 1 
            if empty_lane_counter >= 5:
                print(f"   [GAP OUT] Empty > 5s. Cutting Green Light Early!")
                signals[currentGreen].green = 0 
        else:
            empty_lane_counter = 0 

        printStatus()
        updateValues()
        time.sleep(1)
        
    currentYellow = 1 
    
    for direction in phaseDirections[currentGreen]:
        for i in range(0,3):
            for vehicle in vehicles[direction][i]:
                vehicle.stop = defaultStop[direction]

    while(signals[currentGreen].yellow > 0): 
        printStatus()
        updateValues()
        time.sleep(1)
    currentYellow = 0 
    
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

def generateVehicles():
    spawned_counts = {'car': 0, 'bus': 0, 'truck': 0, 'bike': 0}
    
    while(True):
        vehicle_type_id = random.choice(allowedVehicleTypesList)
        vehicle_type_name = vehicleTypes[vehicle_type_id]
        
        if USE_YOLO_DATA:
            if spawned_counts[vehicle_type_name] >= vehicle_limits[vehicle_type_name]:
                time.sleep(0.5)
                continue 
            
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

# --- UPDATED showStats: No Crash Logic ---
def showStats():
    totalVehicles = 0
    print('Direction-wise Vehicle Counts')
    # Loop over 4 directions explicitly using vehicle data, NOT signals list
    for i in range(0,4):
        direction = directionNumbers[i]
        count = vehicles[direction]['crossed']
        print(f"Direction {i+1} ({direction}): {count}")
        totalVehicles += count
    print('Total vehicles passed:',totalVehicles)
    print('Total time:',timeElapsed)

# --- UPDATED SIMTIME: Generates Report on Timeout ---
def simTime():
    global timeElapsed, simulationTime
    while(True):
        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed==simulationTime):
            showStats()
            generate_final_report_image() # <--- Generates PNG record
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
                generate_final_report_image() # <--- Generates PNG record on Close
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
                "Press 1-4 to Spawn Manually",
                "PNG Report Generated on Exit"
            ]
            for i, instruction in enumerate(instructions):
                instructionText = instructionFont.render(instruction, True, white, black)
                screen.blit(instructionText, (instructionsCoords[0], instructionsCoords[1] + i * 20))

        for vehicle in simulation:  
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()
        pygame.display.update()

Main()