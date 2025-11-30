import cv2


class MotionDetector:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)
        self.min_area = 1000

    # Thay đổi diện tích bắt chuyển động
    def set_min_area(self, val):
        self.min_area = val

    def detect(self, frame):
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(blurred)
        _, fg_mask = cv2.threshold(fg_mask, 244, 255, cv2.THRESH_BINARY)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, None)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        motion_detected = False

        for contour in contours:
            # So sánh diện tích với giá trị cài đặt
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)
                detections.append((x, y, w, h))
        return motion_detected, detections


if __name__ == "__main__":
        detector = MotionDetector()
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            print("Không mở được camera")
            exit()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            # Phát hiện chuyển động
            motion, boxes = detector.detect(frame)
            if motion:
                cv2.putText(frame, "canh bao", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 1)
            # Vẽ bounding box
            for (x, y, w, h) in boxes:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.imshow("motion", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()