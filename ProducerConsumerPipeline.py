import threading
import cv2
import time
#To save the frames 
import os
os.makedirs("output", exist_ok=True)

# Global buffers to hold video frames
buffer1 = []
buffer2 = []

# Global semaphores and mutexes

#Proccess the raw frames 
#keeps track of frames until were full starting at 0
buffer1_full = threading.Semaphore(0)
#how many empty spots there are and if you can add to it; starting at 10
buffer1_empty = threading.Semaphore(10)
#Makes sure buffer is only being accessed by one thing at a time 
buffer1_mutex = threading.Lock()


#Processes the processed frames (after the converter)
buffer2_full = threading.Semaphore(0)
buffer2_empty = threading.Semaphore(10)
buffer2_mutex = threading.Lock() 

# Functions for threads

#Primary goal: Read frames from video then send to the first buffer
def extractor():
    #print("extractor")
    #Grab the video 
    vid = cv2.VideoCapture("clip.mp4")
    #If video is not opening 
    if not vid.isOpened():
        print("Failed to open video file.")
        return
    #Keep count of how many frames have been read
    count = 0
    # vid.read returns 2 values (True or false, image data)
    # Sees if the frame was read or not 
    success, frame = vid.read()

    #Go as long as there are frames
    while success:
        #sees if theres room in buffer
        buffer1_empty.acquire() 
        #Locks it 
        buffer1_mutex.acquire()
        #Add the raw frame to the buffer
        buffer1.append(frame)
        #release the lock so it can be used again 
        buffer1_mutex.release()
        #Signals that buffer1 now has a new frame available for the converter
        buffer1_full.release()
        
        #Just to keep track of the frames proccessed 
        count += 1

        #Grab the next frame; if it returns false we have reached the end
        success,frame = vid.read()
    #release the video
    vid.release()


def converter():
    #print("convertor")
    #counts how many frames that have been converted
    count = 0
    #Just have a set of max frames for now can techinally go forever testing since cv2.show not working
    MAX_FRAMES = 30
    #Go while we havent reached the max frames
    while count < MAX_FRAMES:
        #see if theres something in buffer and grab it 
        buffer1_full.acquire()
        #lock the buffer so it cant be touched by anything else
        buffer1_mutex.acquire()
        #pop the first raw frame
        frame = buffer1.pop(0)
        #unlock the buffer 
        buffer1_mutex.release()
        #nofify theres empty space and can add another frame
        buffer1_empty.release()

        #change the frame from raw color to the grey scale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #see if theres room in buffer 2 to give new converted frame 
        buffer2_empty.acquire()
        #lock the buffer 
        buffer2_mutex.acquire()
        #add the frame to the buffer
        buffer2.append(gray)
        #unlock the buffer 
        buffer2_mutex.release()
        #relase the new frame to displayer 
        buffer2_full.release()

        #incremented the frame conversion count 
        count += 1

def displayer():
    #keep track of frames displayed
    count = 0
    # match conveter
    MAX_FRAMES = 30

    #Go until we reach the max frames 
    while count < MAX_FRAMES:
        #see if theres at least 1 frame in buffer 2
        buffer2_full.acquire()
        #lock the buffer 
        buffer2_mutex.acquire()
        #grabs the first frame from buffer 2
        frame = buffer2.pop(0)
        #unlocks the lock on buffer two
        buffer2_mutex.release()
        #now there is room for new frame
        buffer2_empty.release()

        #Error check : something went wrong like a frame is none 
        if frame is None:
            print(f"[Displayer] Skipping invalid frame {count}")
            continue

        # CV2 NOT WORKING 
        # try:
        #     #Display the frame
        #     cv2.imshow("Video", frame)
        #     #wait 42 milsec for effect of 24 fps;  if q is pressed stops playback
        #     if cv2.waitKey(42) & 0xFF == ord("q"):
        #         break
        #     #If something is not working display error 
        # except Exception as e:
        #     print(f"[Displayer] Exception at frame {count}: {e}")
        #     continue

        #Save each frame in output file because show is not working
        cv2.imwrite(f"output/frame_{count}.jpg", frame)
        #see if the frames are being processed even though they are not displayed 
        print(f"[Displayer] (frame {count} processed but not shown)")

        #increment count
        count += 1

    #Would clean up gui but CV2 is not working to display 
    # cv2.destroyAllWindows()
    print("Displayer: done.")



# Main thread
if __name__ == "__main__":
    # Create threads (extractor, converter, displayer)
    t1 = threading.Thread(target=extractor)
    t2 = threading.Thread(target=converter)
    t3 = threading.Thread(target=displayer)

    #Start threads (Meaning all 3 functions are running at the same time)
    t1.start()
    t2.start()
    t3.start()

    #Wait for them to finish
    t1.join()
    t2.join()
    t3.join()

    print("All threads finished. Done.")
