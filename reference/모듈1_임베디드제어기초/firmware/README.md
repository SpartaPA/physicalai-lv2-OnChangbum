# 과제 1용 사전 빌드 펌웨어

`opencr_position_p.ino.bin`은 이 레포의 `../examples/opencr_position_p/opencr_position_p.ino`로 빌드했습니다. 수강생은 라즈베리파이에서 이 파일을 다운로드·검증·업로드합니다. 오늘은 펌웨어 컴파일 자체를 실습 범위에 넣지 않습니다.

- 빌드일: 2026-09-22
- OpenCR 보드 패키지: 1.5.3 / FQBN `OpenCR:OpenCR:OpenCR`
- 도구 체인: OpenCR 제공 GCC 5.4.0-2016q2
- Dynamixel2Arduino: `cfbbaf79581ecfcdec952a87916572885453f4ab`
- XM430-W350 모델 1020, ID 12, 1 Mbps, Protocol 2.0 전용 기본 설정
- 빌드 성공: 프로그램 87,824바이트, 전역 변수 40,468바이트
- SHA-256: `c68eddf221d60cfc61767d1937120db2f3d74445dcc5d30b851d5be850df4f7f`

소프트웨어 빌드는 확인했습니다. 실제 라즈베리파이 ARM 환경의 업로드·모터 구동은 아직 검증하지 않았습니다. 장비별 업로드·구동 검증이 완료된 자료인지 확인한 뒤 사용하세요. 다른 모델·ID·통신속도 장비에 이 파일을 그대로 사용하지 마세요. 소스 설정이 바뀌면 새 바이너리와 체크섬을 배포해야 합니다.

[과제 1 발제문서](../과제1_발제_SSH_라즈베리파이_OpenCR.md)
