import cv2


# Vẽ vùng giám sát (ROI) bằng chuột


drawing = False
ix, iy = -1, -1
roi = None


def draw_roi(event, x, y, flags, param):
    global ix, iy, drawing, roi

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        roi = (ix, iy, x - ix, y - iy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi = (ix, iy, x - ix, y - iy)
        print("ROI Selected:", roi)


class MotionDetector:
    def __init__(self, min_area=1500):
        # Bộ trừ nền
        self.bg = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )
        self.min_area = min_area
        self.last_boxes = []  # list các bbox chuyển động (global coords)

    def detect(self, frame, roi_rect):
        self.last_boxes = []

        if roi_rect is None:
            return False

        x, y, w, h = roi_rect

        # bỏ nếu w/h = 0
        if w == 0 or h == 0:
            return False

        # chuẩn hóa nếu kéo ngược
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h

        fh, fw = frame.shape[:2]

        # nếu ROI nằm ngoài frame thì bỏ
        if x >= fw or y >= fh:
            return False

        # ép ROI nằm trong frame
        x = max(0, x)
        y = max(0, y)
        w = min(w, fw - x)
        h = min(h, fh - y)

        if w <= 0 or h <= 0:
            return False

        roi = frame[y:y + h, x:x + w]

        if roi.size == 0:
            return False

        fgmask = self.bg.apply(roi)
        fgmask = cv2.GaussianBlur(fgmask, (5, 5), 0)
        _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
        fgmask = cv2.dilate(fgmask, None, iterations=2)

        contours, _ = cv2.findContours(
            fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        motion_found = False

        for c in contours:
            if cv2.contourArea(c) < self.min_area:
                continue

            bx, by, bw, bh = cv2.boundingRect(c)

            # toạ độ global trên frame gốc
            gx1 = x + bx
            gy1 = y + by
            gx2 = gx1 + bw
            gy2 = gy1 + bh

            self.last_boxes.append((gx1, gy1, gx2, gy2))
            motion_found = True

        return motion_found


def main():
    global roi
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    detector = MotionDetector(min_area=2000)

    cv2.namedWindow("Motion Detector")
    cv2.setMouseCallback("Motion Detector", draw_roi)

    while True:
        ret, frame = cap.read()
        frame= cv2.flip(frame, 1)
        if not ret:
            break

        h, w = frame.shape[:2]

        if roi is None:
            roi_rect = (0, 0, w, h)
        else:
            roi_rect = roi

        # Vẽ ROI (màu xanh dương)
        rx, ry, rw, rh = roi_rect
        if rw < 0:
            rx += rw; rw = -rw
        if rh < 0:
            ry += rh; rh = -rh
        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (255, 0, 0), 2)

        # Phát hiện chuyển động trong ROI
        motion = detector.detect(frame, roi_rect)

        # Vẽ khung quanh các vùng chuyển động và label "person"
        for gx1, gy1, gx2, gy2 in detector.last_boxes:
            cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (255, 0, 255), 2)
            cv2.putText(frame, "person", (gx1, gy1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

        # Ô trạng thái ở góc phải trên giống video
        panel_w, panel_h = 260, 60
        x1 = w - panel_w - 10
        y1 = 10
        x2 = w - 10
        y2 = y1 + panel_h

        # nền trắng
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 1)

        if motion:
            status = "Person: ALERT"
            color = (0, 0, 255)  # đỏ
        else:
            status = "Person: SAFE"
            color = (0, 150, 0)  # xanh lá đậm

        cv2.putText(frame, status, (x1 + 15, y1 + 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Motion Detector", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
