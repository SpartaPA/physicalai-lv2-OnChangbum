#include <Dynamixel2Arduino.h>
#include <string.h>
using namespace ControlTableItem;

// Only PING and READ packets. No motor configuration or motion commands.
Dynamixel2Arduino dxl(Serial3, 84);
const uint32_t bauds[] = {57600, 1000000, 115200, 9600,
                          2000000, 3000000, 4000000, 4500000};

void help() {
  Serial.println("OPENCR_DIAGNOSTIC_V1: PING/READ only");
  Serial.println("Connect ONE motor. Type scan then Enter (up to 60 s).");
  Serial.println("Type help to show this banner. No motion/settings writes.");
}

void field(uint8_t id, uint8_t item, const char *name) {
  const int32_t value = dxl.readControlTableItem(item, id, 30);
  const auto error = dxl.getLastLibErrCode();
  const auto status = dxl.getLastStatusPacketError();
  Serial.print(name); Serial.print("=");
  if (error != DXL_LIB_OK || status != 0) {
    Serial.print("READ_ERROR lib="); Serial.print(error);
    Serial.print(" status="); Serial.println(status);
  } else {
    Serial.println(value);
  }
}

void scan() {
  Serial.println("SCAN_BEGIN");
  for (uint8_t protocol = 2; protocol >= 1; --protocol) {
    dxl.setPortProtocolVersion(protocol);
    for (uint8_t b = 0; b < sizeof(bauds) / sizeof(bauds[0]); ++b) {
      dxl.begin(bauds[b]); // OpenCR bus UART + bus power, not motor baud register.
      delay(100);
      Serial.print("TRY protocol="); Serial.print(protocol);
      Serial.print(" baud="); Serial.println(bauds[b]);
      for (uint16_t id = 0; id <= 252; ++id) {
        if (!dxl.ping(static_cast<uint8_t>(id))) continue;
        const uint16_t model = dxl.getModelNumber(id);
        Serial.print("FOUND id="); Serial.print(id);
        Serial.print(" baud="); Serial.print(bauds[b]);
        Serial.print(" protocol="); Serial.print(protocol);
        Serial.print(" model="); Serial.println(model);
        if (model == 1020) {
          field(id, FIRMWARE_VERSION, "firmware");
          field(id, DRIVE_MODE, "drive_mode");
          field(id, OPERATING_MODE, "operating_mode");
          field(id, TORQUE_ENABLE, "torque_enable");
          field(id, STATUS_RETURN_LEVEL, "status_return_level");
          field(id, HARDWARE_ERROR_STATUS, "hardware_error");
          field(id, VELOCITY_LIMIT, "velocity_limit");
          field(id, PRESENT_INPUT_VOLTAGE, "input_voltage_raw_0.1V");
        }
        Serial.println("SCAN_DONE: first motor found; settings unchanged.");
        return;
      }
    }
  }
  Serial.println("NOT_FOUND: check TTL cable, external motor power, port, ID collision.");
  Serial.println("No response does not prove that the motor is defective.");
}

void setup() {
  Serial.begin(115200);
  dxl.begin(57600);
  help();
}

void loop() {
  static char line[24];
  static uint8_t used = 0;
  static bool overflow = false;
  while (Serial.available()) {
    const char c = Serial.read();
    if (c == '\r' || c == '\n') {
      line[used] = '\0';
      if (overflow) Serial.println("Command too long; use help or scan.");
      else if (used && strcmp(line, "scan") == 0) scan();
      else if (used) help();
      used = 0; overflow = false;
    } else if (!overflow) {
      if (used < sizeof(line) - 1) line[used++] = c;
      else overflow = true;
    }
  }
}
