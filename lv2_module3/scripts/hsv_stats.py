#!/usr/bin/env python3
"""저장된 Raw PNG에서 영역별 HSV 분포(5·50·95 백분위)를 출력한다 (모듈 3 실험 1 근거).

사용: python3 hsv_stats.py <raw.png> <이름>=<영역 마스크 PNG>[:largest][,-<뺄 마스크 PNG>] ...
  예) 원기둥=A_mask.png:largest  빨대=B_mask.png,-A_mask.png
영역 마스크는 흰 픽셀(>0)을 영역으로 본다. ':largest'를 붙이면 가장 큰 외곽 덩어리만 쓴다.
',-' 뒤 마스크의 흰 픽셀은 영역에서 뺀다.
HSV는 OpenCV 기준(H 0~179, S·V 0~255)이고, 검출 노드와 같이 BGR PNG를 COLOR_BGR2HSV로 바꾼다.
"""
import sys

import cv2
import numpy as np


def main():
    raw = cv2.imread(sys.argv[1])
    hsv = cv2.cvtColor(raw, cv2.COLOR_BGR2HSV)
    print('| 영역 | 픽셀 수 | H (5/50/95 %) | S (5/50/95 %) | V (5/50/95 %) |')
    print('|---|---|---|---|---|')
    for arg in sys.argv[2:]:
        name, spec = arg.split('=', 1)
        parts = spec.split(',')
        path, _, opt = parts[0].partition(':')
        m = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if opt == 'largest':
            cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            keep = np.zeros_like(m)
            cv2.drawContours(keep, [max(cs, key=cv2.contourArea)], -1, 255, -1)
            m = m & keep
        region = m > 0
        for p in parts[1:]:
            region &= ~(cv2.imread(p.lstrip('-'), cv2.IMREAD_GRAYSCALE) > 0)
        px = hsv[region]
        cols = ['/'.join(str(int(v)) for v in np.percentile(px[:, k], [5, 50, 95]).round()) for k in range(3)]
        print(f'| {name} | {len(px)} | ' + ' | '.join(cols) + ' |')


if __name__ == '__main__':
    main()
