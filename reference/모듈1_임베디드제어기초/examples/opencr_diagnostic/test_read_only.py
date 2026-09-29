"""Guard the diagnostic's essential property: no motor write instructions."""
from pathlib import Path
import re

source = Path(__file__).with_name('opencr_diagnostic.ino').read_text(encoding='utf8')
calls = set(re.findall(r'\bdxl\.(\w+)\s*\(', source))
allowed = {'begin', 'setPortProtocolVersion', 'ping', 'getModelNumber',
           'readControlTableItem', 'getLastLibErrCode', 'getLastStatusPacketError'}
assert calls <= allowed, f'Unexpected bus API: {calls - allowed}'
assert {'ping', 'readControlTableItem'} <= calls
print('PASS: diagnostic only uses bus setup, PING, READ and error queries')
