#!/usr/bin/env python3
"""두 실행(A·B)의 저장된 수신 결과를 비교해 표로 출력한다 (모듈 3 실험 분석).

사용: python3 compare_runs.py <A_dir> <A_label> <B_dir> <B_label>
  - 입력 동일성: 두 Raw PNG가 픽셀 단위로 같은지, header stamp가 같은지
  - Mask: 흰 픽셀 수, A에만·B에만 있는 흰 픽셀 수, 덩어리(외곽 컨투어)별 면적·외접 사각형
  - 검출: /target 값, 검출 노드 CSV의 detected·cx·cy·n_candidates
덩어리 목록은 Mask를 다시 findContours로 나눈 것이다(검출 노드의 min_area 필터 전 상태).
"""
import csv
import os
import sys

import cv2
import numpy as np
import yaml


def load(d, label):
    rec = yaml.safe_load(open(os.path.join(d, f'{label}_received.yaml')))
    raw = cv2.imread(os.path.join(d, f'{label}_raw.png'))
    mask = cv2.imread(os.path.join(d, f'{label}_mask.png'), cv2.IMREAD_GRAYSCALE)
    rows = list(csv.DictReader(open(os.path.join(d, f'{label}_detect.csv'))))
    return rec, raw, mask, rows


def blobs(mask):
    cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in sorted(cs, key=cv2.contourArea, reverse=True):
        x, y, w, h = cv2.boundingRect(c)
        out.append(f'{cv2.contourArea(c):.1f} px^2 @ x{x} y{y} w{w} h{h}')
    return out


def stamp(rec, key):
    h = rec[key]['header']
    return f"{h['sec']}.{h['nanosec']:09d}"


def main():
    a_dir, a_label, b_dir, b_label = sys.argv[1:5]
    ra, raw_a, mask_a, rows_a = load(a_dir, a_label)
    rb, raw_b, mask_b, rows_b = load(b_dir, b_label)
    print(f'# {a_label} vs {b_label}\n')
    print('## 입력 동일성')
    print(f'- Raw PNG 픽셀 동일: {np.array_equal(raw_a, raw_b)}')
    for k in ('raw', 'mask', 'overlay', '/target'):
        print(f'- {k} stamp: {a_label} {stamp(ra, k)} / {b_label} {stamp(rb, k)}')
    print('\n## Mask')
    print(f'- 흰 픽셀: {a_label} {int(np.count_nonzero(mask_a))} / {b_label} {int(np.count_nonzero(mask_b))}')
    print(f'- {a_label}에만 흰 픽셀: {int(np.count_nonzero((mask_a > 0) & (mask_b == 0)))}, '
          f'{b_label}에만 흰 픽셀: {int(np.count_nonzero((mask_b > 0) & (mask_a == 0)))}')
    print(f'- Mask 픽셀 동일: {np.array_equal(mask_a, mask_b)}')
    for label, m in ((a_label, mask_a), (b_label, mask_b)):
        print(f'- {label} 덩어리: ' + '; '.join(blobs(m)))
    print('\n## 검출 결과')
    for label, rec, rows in ((a_label, ra, rows_a), (b_label, rb, rows_b)):
        p = rec['/target']['point']
        r = rows[0]
        print(f"- {label} /target: x={p['x']:.4f} y={p['y']:.4f} z={p['z']:.6f} | CSV detected={r['detected']} "
              f"cx={r['cx_px']} cy={r['cy_px']} area_ratio={r['area_ratio']} n_candidates={r['n_candidates']} "
              f"(CSV 행 {len(rows)}개)")


if __name__ == '__main__':
    main()
