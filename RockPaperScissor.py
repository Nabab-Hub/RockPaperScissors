import mediapipe as mp
import random as r
import cv2

mp_draw = mp.solutions.drawing_utils
mp_hand = mp.solutions.hands.Hands(max_num_hands=1)

def distance(p1, p2):
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** 0.5

def transparent(base_image, tp_image, point,size=None):
    if size is not None:
        tp_image = cv2.resize(tp_image,size)
    emoji_height, emoji_width, _ = tp_image.shape
    roi_x, roi_y = point
    
    roi = base_image[roi_y:roi_y + emoji_height, roi_x:roi_x + emoji_width]
    alpha_channel = tp_image[:, :, 3]/255.0
    base_channel = 1.0 - alpha_channel
    
    for c in range(3):
        base_image[roi_y:roi_y + emoji_height, roi_x:roi_x + emoji_width, c] = (
            alpha_channel*tp_image[:, :, c] + base_channel * roi[:, :, c]
        )
    return base_image

def checkGes(fingers_open):
    if fingers_open.count(1) == 5:
        # 'paper'
        return 'paper'
    elif fingers_open.count(0) == 5:
        # 'rock'
        return 'rock'
    elif (fingers_open[1] == 1 and fingers_open[2] == 1) and (fingers_open[0] == 0 and fingers_open[3] == 0 and fingers_open[4] == 0):
        # 'scissors'
        return 'scissors'
    elif fingers_open[0]==1 and fingers_open[1:].count(0)==4:
        # 'like'
        return 'like'
    elif (fingers_open[1]==1 and fingers_open[4] == 1) and (fingers_open[2:4].count(0)==2 and fingers_open[0]==0):
        return 'yo'
    elif (fingers_open[1]==1 and fingers_open[4] == 1 and fingers_open[0]==1) and (fingers_open[2:4].count(0)==2):
        return 'yoyo'
    else:
        return ''
    
like_img = cv2.imread(r'lrps\like.png', -1)
rock_img = cv2.imread(r'lrps\rock.png', -1)
papr_img = cv2.imread(r'lrps\paper.png', -1)
sisr_img = cv2.imread(r'lrps\scissors.png', -1)

flag = True
chart_box_on = False
turns = 5
com_score = 0
you_score = 0
who_won = ''
game_over = True
cap = cv2.VideoCapture(0)

while cap.isOpened():
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    
    cv2.rectangle(frame, (20, 10), (620, 60), (139, 32, 227), cv2.FILLED)
    cv2.rectangle(frame, (10, 5), (630, 65), (0, 0, 0), 2)
    cv2.rectangle(frame, (10, 70), (630, 470), (0, 0, 0), 2)
    cv2.putText(frame, 'rock paper scissors'.title(), (150, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (10, 10, 10), 4, cv2.LINE_AA)

    results = mp_hand.process(frame[:, :, ::-1])
    if results.multi_hand_landmarks:
        h, w = 480, 640
        for landmarks in results.multi_hand_landmarks:
            hand_points = []
            for landmark in landmarks.landmark:
                hand_points.append([int(landmark.x*w), int(landmark.y*h)])
            fingers_open = [0, 0, 0, 0, 0]
            tips = [8, 12, 16, 20]
            if distance((hand_points[4][0], hand_points[4][1]), (hand_points[14][0], hand_points[14][1])) >50:
                fingers_open[0] = 1
            else:
                fingers_open[0] = 0
            for idx, i in enumerate(tips, 1):
                if (hand_points[i][1] - hand_points[i-3][1]) <0:
                    fingers_open[idx] = 1
                else:
                    fingers_open[idx] = 0
            
            gesture = checkGes(fingers_open=fingers_open)
                
            if flag and game_over:
                size = (100, 100)
                def decoration(frame, move, tp_img, imgori, textori):
                    cv2.rectangle(frame, (imgori[0]-25, imgori[1]-15), (imgori[0]+125, imgori[1]+135), (0, 0, 0), 2)
                    cv2.rectangle(frame, (imgori[0]-25, imgori[1]+135), (imgori[0]+125, imgori[1]+165), (0, 0, 0), 2)
                    cv2.rectangle(frame, (imgori[0]-23, imgori[1]+137), (imgori[0]+123, imgori[1]+163), (139, 32, 227), -1)
                    frame = transparent(frame, tp_img, imgori, size)
                    cv2.putText(frame, move.upper(), textori, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                    return frame
                hx, hy = 220, 80
                if gesture == 'rock':
                    frame = decoration(frame, gesture, rock_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif gesture == 'paper':
                    frame = decoration(frame, gesture, papr_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif gesture == 'scissors':
                    frame = decoration(frame, gesture, sisr_img, (275+hx, 215+hy), (265+hx, 370+hy))
                elif gesture == 'like':
                    frame = decoration(frame, gesture, like_img, (275+hx, 215+hy), (300+hx, 370+hy))
                    gif = cv2.VideoCapture(r"lrps\timer.gif")
                    flag = False
                
            time_up = False
            if  not flag and game_over:
                gif_size = ()
                gfx, gfy = 220, 180
                if gif.isOpened():
                    time_up, g_frame = gif.read()
                    if time_up:
                        gif_size = g_frame.shape[:2]
                        cv2.rectangle(frame, (180, 80), (420, 110), (0,0,0), 2)
                        cv2.putText(frame, 'pick your move'.upper(), (200, 102), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (139, 32, 227), 2, cv2.LINE_AA)
                        frame[gfy:gfy + gif_size[0], gfx:gfx + gif_size[1]] = g_frame
            
            if time_up == False and not flag and game_over:
                if not chart_box_on:
                    chart_box_on = True
                    your_move = gesture
                    dont_go = True
                    computers_move = r.choice(['rock', 'paper', 'scissors'])
                    if your_move == computers_move:
                        who_won = 'match draw'
                    elif (computers_move == 'rock' and your_move == 'scissors') or (computers_move == 'paper' and your_move == 'rock') or (computers_move == 'scissors' and your_move == 'paper'):
                        who_won = 'computer win'
                        com_score+=5
                        turns-=1
                    elif your_move not in ['rock', 'paper', 'scissors']:
                        dont_go = False
                    else:
                        who_won = 'you win'
                        you_score+=5
                        turns-=1
                if (gesture == 'yo' and chart_box_on) or dont_go==False:
                    chart_box_on = False
                    flag = True    
            
            if not time_up and chart_box_on and dont_go and game_over:          
                cv2.rectangle(frame, (20, 80), (620, 460), (0, 0, 0), 2)
                cv2.rectangle(frame, (30, 90), (610, 130), (0, 0, 0), 2)
                cv2.rectangle(frame, (32, 92), (608, 128), (139, 32, 227), -1)

                cv2.rectangle(frame, (30, 140), (610, 440), (0, 0, 0), 2)
                cv2.rectangle(frame, (35, 145), (315, 405), (0, 0, 0), 2)
                cv2.rectangle(frame, (320, 145), (605, 405), (0, 0, 0), 2)

                cv2.rectangle(frame, (30, 410), (610, 450), (0, 0, 0), 2)
                cv2.rectangle(frame, (32, 412), (608, 448), (139, 32, 227), -1)
                cv2.putText(frame, f"yours score : {str(you_score).zfill(2)} || computer's score : {str(com_score).zfill(2)}".upper(), (45, 117), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 0), 1, cv2.LINE_AA)
                
                cv2.rectangle(frame, (40, 360), (310, 400), (0, 0, 0), 2)
                cv2.rectangle(frame, (42, 362), (308, 398), (139, 32, 227), -1)
                cv2.putText(frame, 'You Chose'.upper(), (110, 385), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                cv2.rectangle(frame, (325, 360), (600, 400), (0, 0, 0), 2)
                cv2.rectangle(frame, (327, 362), (598, 398), (139, 32, 227), -1)
                cv2.putText(frame, 'Computer Chose'.upper(), (355, 385), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                
                hx, hy = -150, -40
                if your_move == 'rock':
                    frame = decoration(frame, your_move, rock_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif your_move == 'paper':
                    frame = decoration(frame, your_move, papr_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif your_move == 'scissors':
                    frame = decoration(frame, your_move, sisr_img, (275+hx, 215+hy), (265+hx, 370+hy))
                hx, hy = 150, -40
                if computers_move == 'rock':
                    frame = decoration(frame, computers_move, rock_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif computers_move == 'paper':
                    frame = decoration(frame, computers_move, papr_img, (275+hx, 215+hy), (290+hx, 370+hy))
                elif computers_move == 'scissors':
                    frame = decoration(frame, computers_move, sisr_img, (275+hx, 215+hy), (265+hx, 370+hy))
                
                if who_won == 'match draw':
                    cv2.putText(frame, 'match draw'.upper(), (230, 436), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                elif who_won == 'computer win':
                    cv2.putText(frame, 'computer win'.upper(), (220, 436), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                elif who_won == 'you win':
                    cv2.putText(frame, 'you win'.upper(), (270, 436), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (52, 186, 235), 2, cv2.LINE_AA)
                    
            if turns == 0 and not chart_box_on:
                game_over = False
                
            if game_over==False:
                if you_score > com_score:
                    cv2.rectangle(frame, (20, 80), (620, 460), (0, 0, 0), 2)
                    cv2.putText(frame, 'you won'.upper(), (150, 270), cv2.FONT_HERSHEY_COMPLEX_SMALL, 3, (0, 255, 0), 5, cv2.LINE_AA)
                else:
                    cv2.rectangle(frame, (20, 80), (620, 460), (0, 0, 0), 2)
                    cv2.putText(frame, 'computer won'.upper(), (120, 270), cv2.FONT_HERSHEY_COMPLEX_SMALL, 2, (0, 0, 255), 3, cv2.LINE_AA)
                    
                if gesture == 'yoyo':
                    turns = 5
                    you_score = 0
                    com_score = 0
                    game_over = True
    if _:
        cv2.imshow('Rock Paper Scissors', frame)
    if cv2.waitKey(1) == 27:
        cap.release()
        break
cv2.destroyAllWindows()