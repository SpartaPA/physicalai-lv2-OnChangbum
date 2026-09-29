# lv2_module1 — OpenCR·다이나믹셀 통합 과제

## 장비·환경·버전

[results/환경확인.txt](results/환경확인.txt)  
[results/버전확인.txt](results/버전확인.txt)

| 항목 | 내용 |
|---|---|
| 호스트 | 라즈베리파이 (pa23), Ubuntu Server 22.04.5 LTS, kernel 5.15.0-1108-raspi, aarch64 |
| 원격 접속 | PC → SSH. PC는 SSH 접속에만 사용 |
| 제어기 | OpenCR R1.0, 라즈베리파이 USB 연결, `/dev/ttyACM0` (`/dev/ttyUSB0`는 라이다용, 미사용) |
| 모터 | XM430-W350(모델 1020), ID 12, 1 Mbps, Protocol 2.0, 속도 모드, 모터 펌웨어 ≥ 38(예제 검사 통과) |
| 예제 | `opencr_position_p` (제공 소스, 수정 없음) |
| 빌드 | Arduino CLI 1.5.1, OpenCR 코어 1.5.3(수동 설치, FQBN `ROBOTIS:OpenCR:OpenCR`), Ubuntu 22.04 패키지 `gcc-arm-none-eabi`, Dynamixel2Arduino `cfbbaf7` |
| 업로더 | `opencr_ld` ver 1.0.4 (ROBOTIS OpenCR `68ec75d` 소스 빌드) |
| 시리얼 도구 | Ubuntu 패키지 `python3-serial`의 `serial.tools.miniterm`, `script`(util-linux), tmux |
| 컴파일러·Python·pyserial 버전 | [results/버전확인.txt](results/버전확인.txt) |

## 실행 방법 (모두 라즈베리파이에서 수행)

1. **빌드·업로드:** `OpenCR_빌드_업로드_가이드.md`를 따라 빌드하고, `opencr_ld`로 `/dev/ttyACM0`에 업로드했다. 출력은 가이드의 `tee` 명령어로 `~/pa-opencr-build/build.log`, `upload.log`에 저장한 뒤 `results/`로 복사했다.
2. **수신·로그 저장:** tmux 세션 안에서 다음 명령으로 모니터 출력 전체를 파일에 저장했다.

   ```bash
   PORT=/dev/ttyACM0
   script -q -c "python3 -m serial.tools.miniterm "$PORT" 115200 --eol LF -e" results/실행A.log
   ```

3. **모니터 안에서 입력한 명령**
   - `k <Kp>`: 준비 확인(`P SET` 응답)
   - `s <Kp> <속도 °/s> <목표 °>`: 실행
   - `x`: 정지(`STOP: user` 확인)
   - Ctrl+]: 종료
4. **실행 순서**
   - 실행 A: `s 0.5 20 20`
   - 복귀 : `s 0.5 20 -20`
   - 실행 B: `s 1.0 20 20`
   - 정지 후 토크가 꺼지면 팔이 중력에 의해 초기 자세로 돌아가므로, 두 실행은 같은 자세에서 시작했다.
   - 따라서 복귀.log는 실제로 작동하지 않은 로그와 같다.
5. **결과 정리:** 로그는 라즈베리파이에서 생성·저장했고, 보고서 작성을 위해 `scp`로 PC의 저장소에 복사해 커밋했다.

## 결과 파일

| 파일 | 내용 |
|---|---|
| [report.md](report.md) | 문제 1~4 설정·증거·해석 |
| [results/환경확인.txt](results/환경확인.txt) | 호스트명·OS·아키텍처·SSH·포트·권한 |
| [results/build.log](results/build.log), [results/upload.log](results/upload.log) | 라즈베리파이 빌드·업로드 기록 |
| [results/실행A.log](results/실행A.log) | Kp 0.5 실측 기록 |
| [results/실행B.log](results/실행B.log) | Kp 1.0 실측 기록 |
| [results/복귀.log](results/복귀.log) | 비교에 사용하지 않은 −20° 복귀 시도 기록(−3.516°에서 정지) |

로그는 `script`로 저장한 터미널 원본이라 줄 끝에 제어 문자(`\r`)가 포함될 수 있다. 정지 줄은 `x` 입력 표시 때문에 `xSTOP: user`로 나타난다.