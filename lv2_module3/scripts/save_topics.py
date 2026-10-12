#!/usr/bin/env python3
"""Raw Image·Mask·Overlay·/target 토픽을 구독해 처음 받은 메시지를 파일로 저장한다 (모듈 3 실험 수신 증거).

검출 알고리즘은 없다. 받은 메시지를 그대로 저장만 한다.
  <out>/<label>_raw.png      /camera/camera/color/image_raw (rgb8 -> BGR로 저장)
  <out>/<label>_mask.png     /target/mask (mono8)
  <out>/<label>_overlay.png  /target/overlay (bgr8)
  <out>/<label>_received.yaml  토픽별 header stamp·frame_id·encoding·크기, /target 값, Mask 흰 픽셀 수

사용: python3 save_topics.py <out_dir> <label> [timeout_s]
모든 토픽을 받거나 timeout_s(기본 15 s)가 지나면 끝난다. 받지 못한 토픽은 yaml에 received: false로 남긴다.
"""
import os
import sys

import cv2
import numpy as np
import rclpy
import yaml
from cv_bridge import CvBridge
from geometry_msgs.msg import PointStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

IMAGES = {'raw': '/camera/camera/color/image_raw', 'mask': '/target/mask', 'overlay': '/target/overlay'}
TARGET = '/target'


def stamp(h):
    return {'sec': h.stamp.sec, 'nanosec': h.stamp.nanosec, 'frame_id': h.frame_id}


def main():
    out, label = sys.argv[1], sys.argv[2]
    timeout_s = float(sys.argv[3]) if len(sys.argv) > 3 else 15.0
    os.makedirs(out, exist_ok=True)
    rclpy.init()
    node = Node('save_topics')
    bridge = CvBridge()
    got = {}

    def on_image(key):
        def cb(msg):
            if key in got:
                return
            img = bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
            if msg.encoding == 'rgb8':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            path = os.path.join(out, f'{label}_{key}.png')
            cv2.imwrite(path, img)
            info = {'topic': IMAGES[key], 'received': True, 'header': stamp(msg.header),
                    'encoding': msg.encoding, 'width': msg.width, 'height': msg.height, 'file': os.path.basename(path)}
            if key == 'mask':
                info['white_px'] = int(np.count_nonzero(img))   # 255(HSV 범위 안) 픽셀 수
            got[key] = info
        return cb

    def on_target(msg):
        if TARGET not in got:
            got[TARGET] = {'topic': TARGET, 'received': True, 'header': stamp(msg.header),
                           'point': {'x': msg.point.x, 'y': msg.point.y, 'z': msg.point.z}}

    # 센서 QoS(BEST_EFFORT)는 RELIABLE·BEST_EFFORT 발행자 모두와 연결된다
    subs = [node.create_subscription(Image, t, on_image(k), qos_profile_sensor_data) for k, t in IMAGES.items()]
    subs.append(node.create_subscription(PointStamped, TARGET, on_target, qos_profile_sensor_data))
    end = node.get_clock().now().nanoseconds + timeout_s * 1e9
    while len(got) < len(IMAGES) + 1 and node.get_clock().now().nanoseconds < end:
        rclpy.spin_once(node, timeout_sec=0.1)

    result = {k: got.get(k, {'topic': t, 'received': False}) for k, t in list(IMAGES.items()) + [(TARGET, TARGET)]}
    with open(os.path.join(out, f'{label}_received.yaml'), 'w') as f:
        yaml.safe_dump(result, f, allow_unicode=True, sort_keys=False)
    print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
