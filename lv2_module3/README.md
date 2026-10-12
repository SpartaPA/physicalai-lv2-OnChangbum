# lv2_module3 — 설정값에 따른 Mask와 검출 결과 변화 분석

보고서: [report.md](report.md)

## 코드 출처

- 팀 저장소 [Lv2_Monglian_Assignment](https://github.com/Lv2-Monglian-Assignment/Lv2_Monglian_Assignment) 태그 `lv2-module5-submit`(커밋 `cc96e83`)의 `lv2_module5/`에서 비전 처리에 필요한 부분만 가져와 Mask·검출 Overlay 이미지 토픽 발행을 추가했다.
- 가져온 것: `ros2_ws/src/target_detector/`(검출 노드), `ros2_ws/src/tracker_bringup/launch/perception.launch.py`(카메라·검출 launch), `config/hsv.yaml`·`config/camera.yaml`. 모터 제어·OpenCR 패키지는 가져오지 않았다.
- 이 저장소에서 바꾼 것 (커밋으로 확인 가능)

| 커밋 | 내용 |
|---|---|
| `6e66717` | 위 파일을 수정 없이 복사 |
| `8a03bfb` | 가져오지 않은 제어 패키지(`tracker_controller`, `tracker_bridge`) 의존 줄과 `camera.yaml`의 `tracker_controller` 설정 삭제 |
| `ffa3f3a` | `target_detector.py`에 `/target/mask`(mono8)·`/target/overlay`(bgr8) 발행 추가, `camera.yaml`에 `mask_topic`·`overlay_topic`·`publish_images` 추가. 검출 알고리즘은 바꾸지 않음 |

- 실험 도구(`scripts/`)는 받은 토픽을 저장·비교만 한다. 검출 알고리즘이 없다.

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `ros2_ws/src/target_detector/` | 검출 노드 (`target_detector.py`: ROS 2 입출력, `detection.py`: HSV Mask·Contour·후보 선택) |
| `ros2_ws/src/tracker_bringup/` | `perception.launch.py`와 `config/*.yaml` 설치 |
| `config/` | 기본 설정 (`hsv.yaml`: 색 범위·최소 면적, `camera.yaml`: 토픽·깊이·저장) |
| `scripts/send_one_frame.sh` | 일시정지된 bag에서 지정 시각의 영상 한 장만 재생하고 수신 결과 저장 |
| `scripts/save_topics.py` | Raw·Mask·Overlay·`/target` 첫 메시지를 PNG·yaml로 저장 |
| `scripts/compare_runs.py` | 두 실행의 입력 동일성·Mask 차이·검출 결과 비교 |
| `scripts/hsv_stats.py` | 저장된 Raw PNG의 영역별 HSV 분포 |
| `results/` | 실험 결과 (아래 "결과 파일 위치") |
| `.gitignore` | bag 데이터 파일(`*.bag`, `*.mcap`, `*.db3`)을 올리지 않음. 수백 MB라서 `metadata.yaml`과 녹화 로그만 올린다. 이 폴더에만 적용되고, 빌드 산출물(`build/`, `install/`, `log/`)은 저장소 최상위 `.gitignore`가 제외한다 |

## 실행 환경

[results/environment.txt](results/environment.txt)

| 항목 | 내용 |
|---|---|
| 컴퓨터 | PC (Ubuntu 24.04.5 LTS, kernel 6.8.0-142-generic) |
| ROS 2 | Lyrical, RMW `rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=28`, `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` |
| Python / OpenCV / NumPy | 3.12.3 / 4.6.0 / 1.26.4 |
| 카메라 | Intel RealSense D435 (FW 5.15.1.55), USB 3, 컬러 640×480 rgb8 30 Hz, `ros-lyrical-realsense2-camera` 4.57.7 |
| 이미지 뷰어 | `ros-lyrical-rqt-image-view` 2.0.5 |
| 소켓 버퍼 | `net.core.rmem_max`·`wmem_max` = 4194304 (`/etc/sysctl.d/60-ros2-dds-buffer.conf`) |

**소켓 버퍼 설정이 필요한 이유**: 기본값(212992)에서는 640×480 컬러 영상(한 장 921,600바이트)을 BEST_EFFORT로 구독하면 한 장도 받지 못했다(CycloneDDS, 2026-10-12 측정). 검출 노드가 영상을 BEST_EFFORT로 구독하므로 PC에서 아래 설정이 필요하다. 이전 모듈의 Raspberry Pi는 이미 4194304였다. 원인 분석은 [report.md 6장](report.md#6-진행-중-발견한-문제)에 있다.

```bash
printf 'net.core.rmem_max=4194304\nnet.core.wmem_max=4194304\n' | sudo tee /etc/sysctl.d/60-ros2-dds-buffer.conf
```
```bash
sudo sysctl --system
```

## 빌드 (PC)

```bash
cd lv2_module3/ros2_ws
```
```bash
colcon build --symlink-install
```
```bash
source install/setup.bash
```

아래 명령은 모두 `lv2_module3/`에서, `source ros2_ws/install/setup.bash`와 `export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`를 한 터미널에서 실행한다.

## 실행 방법

### 1. 입력 bag 녹화 (카메라)

```bash
ros2 launch tracker_bringup perception.launch.py run_id:=live
```
```bash
ros2 bag record --disable-keyboard-controls -o results/bag/target_scene --topics /camera/camera/color/image_raw /camera/camera/color/camera_info
```

약 15 s 녹화 후 Ctrl+C. 목표를 치운 같은 장소에서 `results/bag/no_target_scene`도 같은 방법으로 녹화했다. bag 데이터(`.mcap`, 각 414 MiB)는 크기 때문에 `lv2_module3/.gitignore`로 저장소에서 제외했고, `metadata.yaml`과 녹화 로그만 올렸다. 따라서 이 저장소만으로는 bag을 다시 재생할 수 없고, 같은 실험을 하려면 1부터 새로 녹화해야 한다. 실험에 쓴 프레임의 받은 이미지는 `results/`에 PNG로 남아 있다.

### 2. 검출 노드 실행 (카메라 없이, 실험 설정으로)

```bash
ros2 launch tracker_bringup perception.launch.py camera:=false config_dir:=$PWD/results/exp1_h_lower/A/config run_id:=exp1_A
```

### 3. bag을 일시정지 상태로 열기

```bash
ros2 bag play results/bag/target_scene --topics /camera/camera/color/image_raw --start-paused --disable-keyboard-controls
```

### 4. 영상 한 장 보내고 수신 결과 저장

```bash
scripts/send_one_frame.sh results/exp1_h_lower/A exp1_A 1791782778 200000000
```

bag 시각 `1791782778.200000000`으로 이동(seek)한 뒤 다음 영상 한 장(header stamp `1791782778.179045410`, bag의 236번째 영상)을 재생(play_next)한다. 실험 1·2는 모두 이 프레임을, 목표 없음 확인은 `no_target_scene`의 236번째 영상(seek `1791783100 200000000`, stamp `1791783100.180469971`)을 썼다.

### 5. 이미지 뷰어 수신 화면

```bash
ros2 run rqt_image_view rqt_image_view
```

창 3개를 열어 각각 `/camera/camera/color/image_raw`, `/target/mask`, `/target/overlay`를 선택한 뒤 4를 실행하고 화면을 캡처했다. 영상을 한 장만 보내므로 창은 먼저 토픽을 구독하고 있어야 한다.

### 6. A·B 비교

```bash
python3 scripts/compare_runs.py results/exp1_h_lower/A exp1_A results/exp1_h_lower/B exp1_B
```

## 설정값 변경·적용 방법

1. `config/`의 두 파일을 실험 폴더의 `config/`로 복사하고 바꿀 값만 고친다. 바꾼 줄에는 원래 값을 주석으로 적었다.
2. `perception.launch.py`의 `config_dir:=<폴더>`로 그 폴더의 `*.yaml`을 검출 노드 파라미터로 넘긴다.
3. 검출 노드는 시작할 때 `declare_parameter`로 설정을 한 번만 읽는다(`target_detector.py` 73행). 바뀐 값을 반영하는 콜백이 없으므로 **값을 바꿀 때마다 노드를 다시 시작**한다. 적용된 값은 시작 로그 `run_id=... hsv=...~... min_area=...` 줄(`*_launch.log`)로 확인했다.
4. 같은 stamp의 영상은 재전송으로 보고 처리하지 않으므로(`target_detector.py` `on_color`), 같은 프레임을 다시 넣을 때도 노드를 다시 시작한다.

실험에서 바꾼 값

| 실험 | 폴더 | 기본 설정과 다른 값 |
|---|---|---|
| 공통 고정 | 모든 실험 폴더 | `use_depth: false`, `size_check: false`, `use_object_tracker: false`, `log_dir` |
| 1 A / B | `results/exp1_h_lower/{A,B}/config` | `hsv_lower` `[102, 120, 40]` / `[96, 120, 40]` |
| 2 A / B | `results/exp2_min_area/{A,B}/config` | `min_area_px` `100.0` / `3000.0` |
| 목표 없음 | `results/no_target/config` | 선택값 (`hsv_lower [102, 120, 40]`, `min_area_px 100.0`) |

## 결과 파일 위치

| 경로 | 내용 |
|---|---|
| `results/environment.txt` | 실행 환경 버전 |
| `results/bag/` | 입력 bag의 `metadata.yaml`과 녹화 로그 |
| `results/topics/` | 토픽 목록·발행 구독 정보·메시지 형식·수신 주기, rqt 수신 화면(`rqt_raw.png`, `rqt_mask.png`, `rqt_overlay.png`) |
| `results/exp1_h_lower/{A,B}/` | 실험 1 묶음: 설정, `*_raw.png`·`*_mask.png`·`*_overlay.png`(받은 토픽), `*_received.yaml`(stamp·Mask 흰 픽셀 수·`/target`), `*_target_echo.txt`, `*_rqt.png`(뷰어 화면), `*_detect.csv`·`*_launch.log`(검출 노드 기록), `*_player_calls.txt` |
| `results/exp1_h_lower/compare.md`, `hsv_stats.md` | 실험 1 A·B 비교, 영역별 HSV |
| `results/exp2_min_area/{A,B}/`, `compare.md` | 실험 2 묶음과 비교 |
| `results/no_target/` | 목표 없음 확인 묶음, `continuous_check.txt`(이어 재생 중 `/target` 주기·값) |
