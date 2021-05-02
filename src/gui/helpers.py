import cv2
import gui.constants as c


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if self.vid.isOpened():
            print("FPS: {0}".format(self.vid.get(cv2.CAP_PROP_FPS)))
            # Get video source width and height
            self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.fps = self.vid.get(cv2.CAP_PROP_FPS)
        else:
            self.width = c.INIT_VIDEO_WIDTH
            self.height = c.INIT_VIDEO_HEIGHT
            self.fps = c.INIT_VIDEO_FPS

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                frame = cv2.resize(frame, (int(self.width/2), int(self.height/2)), interpolation=cv2.INTER_AREA)
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                return ret, None
        else:
            return False, None

    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
