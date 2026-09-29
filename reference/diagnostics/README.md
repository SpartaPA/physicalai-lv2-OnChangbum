# OpenCR 모터 통신 진단

과제 펌웨어의 FAULT 원인을 확인하는 별도 진단 펌웨어입니다. OpenCR 응용 펌웨어를 교체합니다. 기존 부트로더와 모터 설정은 변경하지 않습니다. 진단 후에는 확인된 장비 설정에 맞는 과제 펌웨어를 다시 업로드해야 합니다.

모터는 XM430-W350-T 한 개만 OpenCR 3핀 TTL 포트에 연결하고, 모델에 맞는 외부 전원을 사용하세요. 전원을 끈 상태에서 케이블을 연결하고 이동 범위를 비워 두세요. 진단 코드는 모터 구동·토크·설정 쓰기 명령을 보내지 않지만 OpenCR의 모터 버스 전원은 켭니다.

## 사용

라즈베리파이에서 기존 시리얼 모니터를 Ctrl+]로 닫고 아래 명령을 실행합니다.

```bash
mkdir -p ~/opencr-diagnosis
cd ~/opencr-diagnosis
URL=https://raw.githubusercontent.com/SpartaPA/physicalai-lv2-assignments/main/diagnostics
curl -fLO "$URL/opencr_diagnostic.bin"
curl -fLO "$URL/SHA256SUMS"
sha256sum -c SHA256SUMS
```

다운로드와 체크섬이 성공해야 진행합니다. 아래는 기존 가이드의 업로더 경로입니다. 이전 안내의 경로도 대안으로 확인합니다.

```bash
UPLOADER="$HOME/pa-opencr-build/uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"
if [ ! -x "$UPLOADER" ]; then
  UPLOADER="$HOME/opencr-uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"
fi
ls -l /dev/ttyACM*
```

OpenCR 포트를 확인하여 지정하세요. 실행 가능한 업로더를 찾지 못했다면 빌드·업로드 가이드를 먼저 확인합니다.

```bash
PORT=/dev/ttyACM0
test -x "$UPLOADER" && "$UPLOADER" "$PORT" 115200   "$HOME/opencr-diagnosis/opencr_diagnostic.bin" 1
```

`CRC OK`와 `[OK] Download`를 확인합니다. 종료 코드만으로 성공을 판단하지 않습니다. 다시 포트를 확인하고 모니터를 엽니다. 모니터를 연 뒤 RESET을 반복해서 누르지 마세요.

```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200 --eol LF
```

모니터 안에서 `help`와 Enter를 입력합니다. **OPENCR_DIAGNOSTIC_V1** 배너가 나와야 올바른 진단 펌웨어입니다. 이어 `scan`과 Enter를 입력하고 최대 약 1분 기다립니다. 진단 펌웨어에서는 `s 0.3 15 30` 같은 구동 명령을 사용하지 않습니다.

## 결과

- `FOUND`: 발견한 ID, 통신속도, 프로토콜, 모델 번호.
- XM430-W350(1020)이면 firmware, drive_mode, operating_mode, torque_enable, status_return_level, hardware_error, velocity_limit, input_voltage_raw_0.1V를 추가로 읽습니다.
- `READ_ERROR`는 유효한 측정값 0과 다릅니다. 오류 코드도 함께 전달하세요.
- `NOT_FOUND`이면 전원·TTL 케이블·포트를 점검합니다. 검색 실패만으로 모터 고장을 단정하지 않습니다.

첫 모터를 찾으면 검색을 멈춥니다. 결과는 SCAN_BEGIN부터 SCAN_DONE 또는 NOT_FOUND까지 공유하세요. 확인 전 모터 ID·통신속도·운전 모드를 임의로 변경하지 않습니다. 원래 과제 펌웨어 기준은 ID 12, 1 Mbps, Protocol 2.0, 모델 1020, 모터 펌웨어 38 이상이며 추가 초기화 조건도 확인해야 합니다.

## 검증 및 출처

[소스](../모듈1_임베디드제어기초/examples/opencr_diagnostic/opencr_diagnostic.ino)와 [읽기 전용 API 검사](../모듈1_임베디드제어기초/examples/opencr_diagnostic/test_read_only.py)를 포함합니다. OpenCR 코어 1.5.3, Dynamixel2Arduino cfbbaf79581ecfcdec952a87916572885453f4ab로 컴파일을 확인했습니다. 프로그램 사용량 66,484바이트, 전역 변수 40,316바이트입니다. 실제 장비 검색은 아직 수행하지 않았습니다.

[XM430-W350 공식 문서](https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/)
