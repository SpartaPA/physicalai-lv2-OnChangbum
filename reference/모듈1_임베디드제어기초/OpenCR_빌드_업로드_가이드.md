# 라즈베리파이에서 OpenCR 펌웨어 빌드·업로드

라즈베리파이의 **Ubuntu Server 22.04 ARM64** 환경에서 Arduino CLI를 설치하고, 과제 소스로 펌웨어를 빌드하여 OpenCR에 업로드하는 가이드입니다. PC는 SSH 접속에만 사용합니다. **아래 명령은 모두 SSH로 접속한 라즈베리파이에서 실행합니다.** OpenCR USB 케이블도 라즈베리파이에 연결하세요.

공식 OpenCR 패키지는 ARM Linux 호스트용 컴파일러·업로더를 제공하지 않으므로, 코어를 수동 설치하고 Ubuntu의 크로스 컴파일러와 소스로 빌드한 업로더를 사용합니다. 공식 보드 매니저의 ARM 지원을 의미하지 않습니다.

> 검증 범위: 아래 버전 조합으로 Ubuntu 22.04 x86_64에서 과제 소스 컴파일과 업로더 빌드를 확인했습니다. 라즈베리파이 ARM64에서의 빌드·업로드와 모터 동작은 아직 확인하지 않았습니다. 동일 장비에서 검증한 뒤 사용하세요.

각 단계가 성공한 것을 확인한 후 다음 단계로 넘어가세요. 처음 설치하는 전용 작업 폴더를 기준으로 작성했습니다. 같은 경로에 기존 작업이 있다면 덮어쓰지 말고 현재 내용과 설정을 확인하세요.

## 1. 환경과 필수 도구 준비

```bash
hostname
cat /etc/os-release
uname -m
df -h "$HOME"
```

Ubuntu 22.04와 `aarch64`를 확인합니다. 다른 아키텍처이면 아래 ARM64용 CLI를 그대로 설치하지 마세요. 다운로드·설치를 위해 5GB 이상의 여유 공간을 권장합니다.

```bash
export BASE="$HOME/pa-opencr-build"
set -o pipefail
mkdir -p "$BASE"/{bin,downloads,data,user,sketches,output}
sudo apt update
sudo apt install -y build-essential curl git python3-serial \
  gcc-arm-none-eabi libnewlib-arm-none-eabi \
  libstdc++-arm-none-eabi-newlib usbutils file
arm-none-eabi-g++ --version
sudo usermod -aG dialout "$USER"
```

SSH를 종료하고 다시 접속하여 `id -nG` 출력에 `dialout`이 포함되는지 확인하세요. 새 세션에서는 아래 설정도 다시 적용합니다.

```bash
export BASE="$HOME/pa-opencr-build"
set -o pipefail
```

## 2. Arduino CLI 1.5.1 설치

```bash
cd "$BASE/downloads"
VER=1.5.1
ASSET="arduino-cli_${VER}_Linux_ARM64.tar.gz"
RELEASE="https://github.com/arduino/arduino-cli/releases/download"
curl -fL -o "$ASSET" "$RELEASE/v$VER/$ASSET"
curl -fL -o checksums.txt \
  "$RELEASE/v$VER/${VER}-checksums.txt"
grep "  $ASSET\$" checksums.txt | sha256sum -c -
```

체크섬 검증이 `OK`일 때만 압축을 풀어 실행합니다.

```bash
tar -xzf "$ASSET" -C "$BASE/bin" arduino-cli
file "$BASE/bin/arduino-cli"
"$BASE/bin/arduino-cli" version
```

ARM aarch64 실행 파일과 버전 1.5.1을 확인하세요. `Exec format error`이면 다운로드한 파일과 호스트 아키텍처를 확인합니다.

## 3. OpenCR 코어 1.5.3 설치

```bash
cd "$BASE/downloads"
CORE_URL="https://github.com/ROBOTIS-GIT/OpenCR/releases/download"
curl -fL -o opencr.tar.bz2 "$CORE_URL/1.5.3/opencr.tar.bz2"
CORE_SHA=418656e5e6d99d45d187ffdb28dece0f450c6707da3f6db56769f3ecafdc413c
printf '%s  opencr.tar.bz2\n' "$CORE_SHA" | sha256sum -c -
```

`OK`를 확인한 뒤 다음을 실행합니다. 이 파일은 확장자와 달리 실제로는 gzip 형식이므로 `tar -xf`로 자동 감지합니다.

```bash
mkdir -p "$BASE/user/hardware/ROBOTIS/OpenCR"
tar -xf opencr.tar.bz2 \
  -C "$BASE/user/hardware/ROBOTIS/OpenCR" --strip-components=1
```

## 4. CLI 설정과 라이브러리 설치

```bash
cat > "$BASE/arduino-cli.yaml" <<EOF
directories:
  data: $BASE/data
  downloads: $BASE/downloads
  user: $BASE/user
EOF
"$BASE/bin/arduino-cli" --config-file "$BASE/arduino-cli.yaml" \
  core update-index
"$BASE/bin/arduino-cli" --config-file "$BASE/arduino-cli.yaml" \
  board listall
```

보드 목록에 `OpenCR Board`와 **`ROBOTIS:OpenCR:OpenCR`**이 있어야 합니다. 이번 수동 설치의 vendor 폴더가 `ROBOTIS`이므로 보드 매니저 설치에서 쓰는 `OpenCR:OpenCR:OpenCR`과 다릅니다.

```bash
mkdir -p "$BASE/user/libraries"
git clone https://github.com/ROBOTIS-GIT/Dynamixel2Arduino.git \
  "$BASE/user/libraries/Dynamixel2Arduino"
git -C "$BASE/user/libraries/Dynamixel2Arduino" checkout \
  cfbbaf79581ecfcdec952a87916572885453f4ab
```

## 5. Ubuntu 컴파일러 연결

원본 `platform.txt`는 유지하고 로컬 설정으로 컴파일러 경로를 지정합니다.

```bash
cat > "$BASE/user/hardware/ROBOTIS/OpenCR/platform.local.txt" <<'EOF'
compiler.path=/usr/bin/
EOF
arm-none-eabi-g++ --version
```

검증한 컴파일러는 Ubuntu 22.04의 `arm-none-eabi-g++ 10.3.1`입니다. 이 조합에서는 추가 호환 옵션 없이 빌드됐습니다. 다른 버전에서 오류가 발생하면 버전과 첫 오류를 확인하고, 임의의 옵션으로 오류를 숨기지 마세요.

## 6. 과제 소스 준비와 빌드

제공 소스의 기본 대상은 **XM430-W350(모델 1020), ID 12, 1 Mbps, Protocol 2.0**입니다. 본인 장비가 다르면 검증된 호환 소스·설정이 필요합니다. 모델 검사를 제거하지 마세요.

```bash
git clone https://github.com/SpartaPA/physicalai-lv2-assignments.git \
  "$BASE/repo"
SOURCE=$(find "$BASE/repo" -type d -name opencr_position_p -print -quit)
test -n "$SOURCE" && test -f "$SOURCE/opencr_position_p.ino"
```

소스를 찾았을 때만 작업 폴더에 복사하고 빌드합니다. 복사 경로가 이미 있다면 중복 복사하지 말고 사용할 소스 버전을 확인하세요.

```bash
cp -r "$SOURCE" "$BASE/sketches/"
set -o pipefail
"$BASE/bin/arduino-cli" --config-file "$BASE/arduino-cli.yaml" \
  compile --fqbn ROBOTIS:OpenCR:OpenCR --jobs 1 \
  --output-dir "$BASE/output" \
  "$BASE/sketches/opencr_position_p" 2>&1 | tee "$BASE/build.log"
```

빌드가 성공했을 때만 아래 결과를 확인합니다. 실패했다면 이전에 생성된 파일을 새 빌드 결과로 사용하지 마세요.

```bash
test -s "$BASE/output/opencr_position_p.ino.bin"
file "$BASE/output/opencr_position_p.ino.elf"
arm-none-eabi-size "$BASE/output/opencr_position_p.ino.elf"
sha256sum "$BASE/output/opencr_position_p.ino.bin"
```

`.elf`는 OpenCR 타깃의 섹션·주소·심볼 정보를 포함하고, `.bin`은 업로드할 원시 펌웨어입니다. 빌드 성공은 파일 생성 완료를 의미하며 장치 업로드 성공과는 별개입니다.

직접 만든 파일은 기존 제공 바이너리와 크기·해시가 달라질 수 있습니다. 레포의 `firmware/SHA256SUMS`를 새 빌드 결과의 정답 해시로 사용하지 않습니다.

## 7. 라즈베리파이용 업로더 빌드

펌웨어는 `arm-none-eabi-g++`로 OpenCR용 파일을 만듭니다. 아래 업로더는 일반 `gcc`로 라즈베리파이에서 실행할 파일을 만듭니다.

```bash
mkdir "$BASE/uploader-src"
cd "$BASE/uploader-src"
git init
git remote add origin https://github.com/ROBOTIS-GIT/OpenCR.git
git sparse-checkout init --cone
git sparse-checkout set arduino/opencr_develop/opencr_ld
git fetch --depth 1 --filter=blob:none origin \
  68ec75d8a400949580ecf263e0105ea9743b878e
git checkout --detach FETCH_HEAD
make -C arduino/opencr_develop/opencr_ld
file arduino/opencr_develop/opencr_ld/opencr_ld
```

ARM64 라즈베리파이라면 업로더도 ARM aarch64 실행 파일인지 확인합니다.

## 8. OpenCR 포트 확인과 업로드

OpenCR을 라즈베리파이에 USB로 연결하고 연결 전후의 목록을 비교해 포트를 확인하세요. 다른 시리얼 프로그램이 열려 있으면 종료합니다.

```bash
lsusb
ls -l /dev/ttyACM*
```

아래 `/dev/ttyACM0`은 예시입니다. 실제로 확인한 OpenCR 포트로 지정하세요.

```bash
PORT=/dev/ttyACM0
udevadm info --query=property --name="$PORT"
test -r "$PORT" && test -w "$PORT" && echo 'Port access OK'
```

이 업로드는 OpenCR의 기존 응용 펌웨어를 교체합니다. 장비 설정과 모터 고정·이동 범위·전원 차단 방법을 확인한 상태에서 수행하세요.

```bash
UPLOADER="$BASE/uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"
set -o pipefail
"$UPLOADER" "$PORT" 115200 \
  "$BASE/output/opencr_position_p.ino.bin" 1 \
  2>&1 | tee "$BASE/upload.log"
```

**이번에 직접 빌드한 `output/opencr_position_p.ino.bin`을 업로드합니다.** 사전 빌드된 `firmware/` 파일과 혼동하지 마세요.

출력의 **`CRC OK`와 `[OK] Download`**를 확인합니다. 이 업로더는 내부 오류가 있어도 종료 코드가 성공으로 보일 수 있으므로 종료 코드만으로 성공을 판단하지 않습니다.

## 9. 업로드 이후 준비 상태 확인

포트 번호가 달라질 수 있으므로 다시 확인합니다. 모터에 맞는 전원·통신 설정을 준비하고 아래 명령으로 초기 출력을 확인하세요. 이 단계에서는 움직임 명령을 보내지 않습니다.

```bash
ls -l /dev/ttyACM*
PORT=/dev/ttyACM0
python3 -m serial.tools.miniterm "$PORT" 115200 --eol LF -e
```

READY와 정상 준비 상태를 확인합니다. 초기 출력을 놓쳤다면 안전한 정지 상태에서 RESET으로 다시 확인할 수 있습니다. USB가 재연결되면 포트와 모니터를 다시 확인하세요. FAULT는 정상 준비 완료가 아닙니다. 원인을 확인하고 해결한 뒤 과제를 진행하세요. 모니터 종료는 Ctrl+]입니다.

이후 목표 입력·기록·제출은 [과제 1 발제문서](과제1_발제_SSH_라즈베리파이_OpenCR.md)를 따릅니다. SSH 또는 모니터 종료가 모터 정지를 보장하지는 않습니다.

## 문제 해결

연결·전원을 확인해도 `FAULT: RESET required.`가 계속되면 [읽기 전용 모터 진단](../diagnostics/README.md)으로 ID·통신속도와 장치 상태를 확인할 수 있습니다.

모터 설정을 바꾸지 않고 ID·통신속도를 찾는 진단 펌웨어를 준비했습니다. 모터 한 개만 연결하고, 회전 범위를 비워 두세요.
1. Ctrl+]로 시리얼 모니터를 닫고, 라즈베리파이에서 실행하세요.
```bash
mkdir -p ~/opencr-diagnosis
cd ~/opencr-diagnosis

URL=https://raw.githubusercontent.com/SpartaPA/physicalai-lv2-assignments/main/diagnostics

curl -fLO "$URL/opencr_diagnostic.bin"
curl -fLO "$URL/SHA256SUMS"
sha256sum -c SHA256SUMS
```
opencr_diagnostic.bin: OK가 나오면 다음으로 진행하세요.
2. 진단 펌웨어를 업로드합니다. 기존 과제 펌웨어는 진단 후 다시 올리면 됩니다.
```bash
UPLOADER="$HOME/pa-opencr-build/uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"

if [ ! -x "$UPLOADER" ]; then
  UPLOADER="$HOME/opencr-uploader-src/arduino/opencr_develop/opencr_ld/opencr_ld"
fi

ls -l /dev/ttyACM*
```
OpenCR 포트가 ttyACM0이면:
```bash
"$UPLOADER" /dev/ttyACM0 115200 \
  "$HOME/opencr-diagnosis/opencr_diagnostic.bin" 1
```
CRC OK와 [OK] Download를 확인하세요. 오류가 나오면 여기서 멈추고 출력 내용을 보내주세요.
3. 다시 연결하세요.
```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200 --eol LF
```
모니터 안에서 아래를 입력하고 Enter:
```
help
```
OPENCR_DIAGNOSTIC_V1이 나오면 다음을 입력하고 Enter:
```bash
scan
```
최대 약 1분 기다린 뒤 FOUND부터 SCAN_DONE까지의 출력을 보내주세요. NOT_FOUND가 나오면 그것도 그대로 보내주세요. RESET이나 모터 구동 명령은 입력하지 마세요.

| 현상 | 확인 사항 |
|---|---|
| Exec format error | uname -m과 CLI·업로더의 file 결과가 호스트와 일치하는지 |
| bzip2 오류 | 코어 파일에 tar -xf를 사용했는지 |
| 보드를 찾지 못함 | CLI 설정 파일, 수동 설치 경로, FQBN |
| Dynamixel2Arduino.h 없음 | 지정한 user/libraries 경로와 라이브러리 체크아웃 |
| 빌드 오류 | build.log의 첫 오류, 코어·컴파일러·라이브러리 버전 |
| Permission denied | dialout 추가 후 SSH에 다시 접속했는지 |
| 업로드 timeout | 포트·USB 케이블·시리얼 프로그램 점유 여부 |
| FAULT | 모터 모델·ID·통신속도·전원·통신 케이블 |

복구 모드가 필요하면 PUSH SW2를 누른 상태에서 RESET을 눌렀다 놓고 SW2를 놓습니다. 포트를 다시 확인하여 업로드를 재시도하세요. 부트로더 자체를 임의로 덮어쓰지 않습니다.

## 참고

- [공식 OpenCR 설치·ARM SBC 제한](https://emanual.robotis.com/docs/en/platform/turtlebot3/opencr_setup/)
- [Arduino 플랫폼 수동 설치·로컬 설정](https://docs.arduino.cc/arduino-cli/platform-specification/)
- [Arduino CLI 1.5.1 배포](https://github.com/arduino/arduino-cli/releases/tag/v1.5.1)
- [OpenCR 코어 1.5.3 배포](https://github.com/ROBOTIS-GIT/OpenCR/releases/tag/1.5.3)
- [OpenCR 업로더 소스](https://github.com/ROBOTIS-GIT/OpenCR/tree/68ec75d8a400949580ecf263e0105ea9743b878e/arduino/opencr_develop/opencr_ld)
