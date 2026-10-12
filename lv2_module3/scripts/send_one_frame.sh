#!/usr/bin/env bash
# 일시정지된 bag 재생기(ros2 bag play --start-paused)에서 지정 시각의 영상 한 장만 내보내고, 받은 토픽을 저장한다.
# 검출 노드와 bag 재생기는 먼저 따로 실행해 둔다(README 참고). 검출 노드는 같은 stamp 영상을 다시 처리하지 않으므로 실행마다 새로 띄운다.
#
# 사용: scripts/send_one_frame.sh <out_dir> <label> <seek_sec> <seek_nanosec>
#   <out_dir>/<label>_raw.png·_mask.png·_overlay.png·_received.yaml  (save_topics.py)
#   <out_dir>/<label>_target_echo.txt   ros2 topic echo /target 출력
#   <out_dir>/<label>_player_calls.txt  seek·play_next 서비스 호출 결과
set -u
out=$1 label=$2 sec=$3 nsec=$4
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"

timeout 20 ros2 topic echo /target > "$out/${label}_target_echo.txt" 2>&1 &
echo_pid=$!
python3 "$here/save_topics.py" "$out" "$label" 20 > "$out/${label}_save.log" 2>&1 &
save_pid=$!
sleep 4   # 구독자가 발행자를 찾을 시간 (영상을 한 장만 보내므로 먼저 연결돼 있어야 한다)

{
  echo "\$ ros2 service call /rosbag2_player/seek rosbag2_interfaces/srv/Seek \"{time: {sec: $sec, nanosec: $nsec}}\""
  timeout 10 ros2 service call /rosbag2_player/seek rosbag2_interfaces/srv/Seek "{time: {sec: $sec, nanosec: $nsec}}"
  echo "\$ ros2 service call /rosbag2_player/play_next rosbag2_interfaces/srv/PlayNext"
  timeout 10 ros2 service call /rosbag2_player/play_next rosbag2_interfaces/srv/PlayNext
} > "$out/${label}_player_calls.txt" 2>&1

wait "$save_pid"
sleep 1
kill "$echo_pid" 2>/dev/null
wait "$echo_pid" 2>/dev/null
cat "$out/${label}_save.log"
